from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapeResult:
    asin: str
    price: float | None
    currency: str
    is_available: bool
    raw_price: str | None = None


# Rotate headers to look less like a bot
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# CSS selectors Amazon uses for price (they change these often)
PRICE_SELECTORS = [
    "span.a-price span.a-offscreen",
    "#priceblock_ourprice",
    "#priceblock_dealprice",
    "span#price_inside_buybox",
    ".a-price .a-offscreen",
]


def parse_price(raw: str) -> tuple[float | None, str]:
    """Exact numeric price and currency from a raw string like '€ 29,99'."""
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
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned), currency
    except ValueError:
        return None, currency


async def scrape_amazon_product(asin: str) -> ScrapeResult:
    """Scrape price for a given Amazon ASIN."""
    url = f"https://www.amazon.com/dp/{asin}"

    failed_scrape = ScrapeResult(
        asin=asin,
        price=None,
        currency="EUR",
        is_available=False,
    )

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=10.0,
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return failed_scrape

        soup = BeautifulSoup(response.text, "html.parser")

        # Check if Amazon blocked us (CAPTCHA page)
        if "robot" in response.text.lower() or "captcha" in response.text.lower():
            return failed_scrape

        # Try each selector until one works
        raw_price = None
        for selector in PRICE_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                raw_price = element.get_text(strip=True)
                break

        if not raw_price:
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

    except httpx.RequestError:
        return failed_scrape
