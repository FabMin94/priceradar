from app.scrapers.amazon import parse_price
from app.core.amazon import extract_asin


def test_parse_price_euros():
    price, currency = parse_price("€ 29,99")
    assert price == 29.99
    assert currency == "EUR"


def test_parse_price_dollars():
    price, currency = parse_price("$19,99")
    assert price == 19.99
    assert currency == "USD"


def test_parse_price_european_format():
    price, currency = parse_price("1.299,99")
    assert price == 1299.99
    assert currency == "EUR"


def test_parse_price_invalid():
    price, currency = parse_price("Currently unavailable")
    assert price is None


def test_extract_asin_dp_url():
    url = "https://www.amazon.it/dp/B00ZRD99C0"
    assert extract_asin(url) == "B00ZRD99C0"


def test_extract_asin_gp_url():
    url = "https://www.amazon.it/gp/product/B00ZRD99C0"
    assert extract_asin(url) == "B00ZRD99C0"


def test_extract_asin_long_url():
    url = "https://www.amazon.it/Some-Product/dp/B00ZRD99C0/ref=sr_1_1"
    assert extract_asin(url) == "B00ZRD99C0"


def test_extract_asin_invalid():
    url = "https://www.google.com"
    assert extract_asin(url) is None