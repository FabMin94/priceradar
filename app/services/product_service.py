from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.amazon import clean_amazon_url, extract_asin
from app.models.product import PriceHistory, Product
from app.schemas.product import ProductCreate


class ProductNotFoundError(Exception):
    pass


class ProductAlreadyTrackedError(Exception):
    pass


async def create_product(
    db: AsyncSession,
    data: ProductCreate,
    user_id: str,
) -> Product:
    asin = extract_asin(data.url)

    # Check if user already tracks this ASIN
    result = await db.execute(
        select(Product).where(
            Product.user_id == UUID(user_id),
            Product.asin == asin,
            Product.is_active == True,  # noqa: E712
        )
    )
    if result.scalar_one_or_none():
        raise ProductAlreadyTrackedError(f"You are already tracking ASIN {asin}")

    product = Product(
        user_id=UUID(user_id),
        url=clean_amazon_url(asin),
        name=data.name,
        asin=asin,
        alert_threshold=data.alert_threshold,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def get_user_products(
    db: AsyncSession,
    user_id: str,
) -> list[Product]:
    result = await db.execute(
        select(Product)
        .where(Product.user_id == UUID(user_id), Product.is_active == True)  # noqa: E712
        .order_by(desc(Product.created_at))
    )
    products = list(result.scalars().all())

    # Attach latest price to each product
    for product in products:
        latest = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product.id)
            .order_by(desc(PriceHistory.scraped_at))
            .limit(1)
        )
        latest_record = latest.scalar_one_or_none()
        product.latest_price = latest_record.price if latest_record else None

    return products


async def get_product_detail(
    db: AsyncSession,
    product_id: UUID,
    user_id: str,
) -> Product:
    result = await db.execute(
        select(Product)
        .where(
            Product.id == product_id,
            Product.user_id == UUID(user_id),
        )
        .options(selectinload(Product.price_history))
    )
    product = result.scalar_one_or_none()

    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")

    # Attach latest price
    if product.price_history:
        product.latest_price = max(
            product.price_history, key=lambda p: p.scraped_at
        ).price
    else:
        product.latest_price = None

    return product


async def delete_product(
    db: AsyncSession,
    product_id: UUID,
    user_id: str,
) -> None:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == UUID(user_id),
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise ProductNotFoundError(f"Product {product_id} not found")

    # Soft delete — keep the data, just mark inactive
    product.is_active = False
