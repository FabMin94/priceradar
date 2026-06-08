from app.core.amazon import extract_asin, is_amazon_url, clean_amazon_url


def test_extract_asin_dp():
    assert extract_asin("https://www.amazon.it/dp/B0CHXMJRP3") == "B0CHXMJRP3"


def test_extract_asin_gp():
    assert extract_asin("https://www.amazon.it/gp/product/B0CHXMJRP3") == "B0CHXMJRP3"


def test_extract_asin_with_ref():
    url = "https://www.amazon.com/Some-Product/dp/B0CHXMJRP3/ref=sr_1_1"
    assert extract_asin(url) == "B0CHXMJRP3"


def test_extract_asin_invalid():
    assert extract_asin("https://www.google.com") is None


def test_amazon_url_is_valid():
    assert is_amazon_url("https://www.amazon.it/dp/B0CHXMJRP3") is True


def test_amazon_url_is_invalid():
    assert is_amazon_url("https://www.ebay.com/item/123") is False


def test_clean_amazon_url():
    assert clean_amazon_url("B0CHXMJRP3") == "https://www.amazon.com/dp/B0CHXMJRP3"