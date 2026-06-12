import asyncio
import logging
import random
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    asin: str
    price: float | None
    currency: str
    is_available: bool
    raw_price: str | None = None


# Realistic browser headers
def get_headers() -> dict:
    """Return realistic browser headers."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;"
            "q=0.8,application/signed-exchange;v=b3;q=0.7"
        ),
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Cache-Control": "max-age=0",
    }


# CSS selectors Amazon uses for price
PRICE_SELECTORS = [
    "span.a-price span.a-offscreen",
    "#priceblock_ourprice",
    "#priceblock_dealprice",
    "#priceblock_saleprice",
    "span#price_inside_buybox",
    ".a-price .a-offscreen",
    "#corePrice_feature_div span.a-offscreen",
    "#apex_offerDisplay_desktop span.a-offscreen",
    ".apexPriceToPay span.a-offscreen",
]


def parse_price(raw: str) -> tuple[float | None, str]:
    """Exact numeric price and currency from a raw string like '€ 29,99'."""
    if not raw:
        return None, "Eur"

    currency = "EUR"
    if "$" in raw:
        currency = "USD"
    elif "£" in raw:
        currency = "GBP"

    # Remove currency symbols, spaces, and normalize decimal separator
    cleaned = raw.replace("€", "").replace("$", "").replace("£", "")
    cleaned = cleaned.replace("\xa0", "").strip()

    # Handle European format (29,99) vs US format (29.99)
    if "," in cleaned and "." in cleaned:
        if cleaned.index(".") < cleaned.index(","):
            # European: 1.299,99
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 1,299.99
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned), currency
    except ValueError:
        return None, currency


async def scrape_amazon_product(asin: str) -> ScrapeResult:
    """Scrape price for a given Amazon ASIN."""
    # Try both .com and .it
    urls = [
        f"https://www.amazon.com/dp/{asin}",
        f"https://www.amazon.com/dp/{asin}?th=1&psc=1",
        f"https://www.amazon.it/dp/{asin}",
    ]

    for url in urls:
        result = await _try_scrape(asin, url)
        if result.is_available and result.price is not None:
            return result
        # Small delay between attempts
        await asyncio.sleep(random.uniform(1, 3))

    # Return last result even if unsuccessful
    return result


async def _try_scrape(asin: str, url: str) -> ScrapeResult:
    """Single scrape attempt for a URL."""
    try:
        async with httpx.AsyncClient(
            headers=get_headers(),
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            # First visit the homepage to get cookies (looks more like a real browser)
            domain = (
                "https://www.amazon.com" if ".com" in url else "https://www.amazon.it"
            )
            try:
                await client.get(domain, timeout=5.0)
                await asyncio.sleep(random.uniform(0.5, 1.5))
            except Exception:
                pass  # Homepage visit is best-effort

            response = await client.get(url)

        if response.status_code != 200:
            logger.warning(f"Amazon returned {response.status_code} for {asin}")
            return ScrapeResult(
                asin=asin, price=None, currency="EUR", is_available=False
            )

        # Check for bot detection
        page_lower = response.text.lower()
        if "captcha" in page_lower or "robot check" in page_lower:
            logger.warning(f"Amazon bot detection triggered for {asin}")
            return ScrapeResult(
                asin=asin, price=None, currency="EUR", is_available=False
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # Check if product is unavailable
        unavailable_indicators = [
            "currently unavailable",
            "non disponibile",
            "out of stock",
        ]
        if any(ind in page_lower for ind in unavailable_indicators):
            return ScrapeResult(
                asin=asin, price=None, currency="EUR", is_available=False
            )

        # Try each price selector
        raw_price = None
        for selector in PRICE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and any(c.isdigit() for c in text):
                    raw_price = text
                    logger.info(f"Found price with selector '{selector}': {raw_price}")
                    break

        if not raw_price:
            logger.warning(f"No price found for {asin} at {url}")
            return ScrapeResult(
                asin=asin,
                price=None,
                currency="EUR",
                is_available=False,
                raw_price=None,
            )

        price, currency = parse_price(raw_price)
        return ScrapeResult(
            asin=asin,
            price=price,
            currency=currency,
            is_available=price is not None,
            raw_price=raw_price,
        )

    except httpx.RequestError as e:
        logger.error(f"Request error scraping {asin}: {e}")
        return ScrapeResult(asin=asin, price=None, currency="EUR", is_available=False)
