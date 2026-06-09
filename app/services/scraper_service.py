import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Alert, PriceHistory, Product
from app.scrapers.amazon import scrape_amazon_product

logger = logging.getLogger(__name__)


async def scrape_product(db: AsyncSession, product: Product) -> None:
    """Scrape price for a single product and store result."""
    logger.info(f"Scraping {product.asin} ({product.name})")

    result = await scrape_amazon_product(product.asin)

    # Always store the price snapshot even if unavailable
    price_record = PriceHistory(
        product_id=product.id,
        price=result.price or 0,
        currency=result.currency,
        is_available=result.is_available,
    )
    db.add(price_record)

    # Check if alert should trigger
    if (
        result.is_available
        and result.price is not None
        and product.alert_threshold is not None
        and result.price <= float(product.alert_threshold)
    ):
        alert = Alert(
            product_id=product.id,
            price_at_alert=result.price,
            threshold=float(product.alert_threshold),
        )
        db.add(alert)
        logger.info(
            f"Alert triggered for {product.asin}: "
            f"{result.price} <= {product.alert_threshold}"
        )

    await db.flush()


async def scrape_all_products(db: AsyncSession) -> None:
    """Scrape all active products. Called by the scheduler."""
    result = await db.execute(
        select(Product).where(Product.is_active == True)  # noqa: E712
    )
    products = list(result.scalars().all())

    if not products:
        logger.info("No active products to scrape")
        return

    logger.info(f"Starting to scrape for {len(products)} products")

    for product in products:
        try:
            await scrape_product(db, product)
        except Exception as e:
            # Don't let one failed scrape kill the whole job
            logger.error(f"Failed to scrape {product.asin}: {e}")

    await db.commit()
    logger.info("Scrape complete")
