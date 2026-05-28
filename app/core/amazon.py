import re
from urllib.parse import urlparse


ASIN_PATTERN = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})")


def extract_asin(url: str) -> str | None:
    """Extract ASIN from an Amazon product URL."""
    match = ASIN_PATTERN.search(url)
    return match.group(1) if match else None


def is_amazon_url(url: str) -> bool:
    """Check if URL is an Amazon domain."""
    try:
        hostname = urlparse(url).hostname or ""
        return "amazon." in hostname
    except Exception:
        return False
    

def clean_amazon_url(asin: str) -> str:
    """Return a canonical Amazon URL from an ASIN."""
    return f"https://www.amazon.com/dp/{asin}"