import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.scrapers.amazon import ScrapeResult


async def test_add_product_success(client: AsyncClient, mock_auth: str):
    response = await client.post(
        "/api/v1/products",
        json={
            "url": "https://www.amazon.it/dp/B0CHXMJRP3",
            "name": "Test Product",
            "alert_threshold": 99.99,
        },
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["asin"] == "B0CHXMJRP3"
    assert data["name"] == "Test Product"


async def test_add_product_invalid_url(client: AsyncClient, mock_auth: str):
    response = await client.post(
        "/api/v1/products",
        json={
            "url": "https://www.ebay.com/item/123",
            "name": "Test Product",
        },
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 422


async def test_add_product_duplicate(client: AsyncClient, mock_auth: str):
    payload = {
            "url": "https://www.amazon.it/dp/B0CHXMJRP3",
            "name": "Test Product",
    }
    await client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": "Bearer faketoken"},
    )
    response = await client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 409


async def test_list_products(client: AsyncClient, mock_auth: str):
    await client.post(
        "/api/v1/products",
        json={"url": "https://www.amazon.it/dp/B0CHXMJRP3", "name": "Product 1"},
        headers={"Authorization": "Bearer faketoken"},
    )
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_products_no_token(client: AsyncClient):
    response = await client.get("/api/v1/products")
    assert response.status_code == 401


async def test_delete_product(client: AsyncClient, mock_auth: str):
    create = await client.post(
        "/api/v1/products",
        json={"url": "https://www.amazon.it/dp/B0CHXMJRP3", "name": "Product 1"},
        headers={"Authorization": "Bearer faketoken"},
    )
    product_id = create.json()["id"]

    response = await client.delete(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 204

    # Verify it's gone from the list
    list_response = await client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert len(list_response.json()) == 0


async def test_manual_scrape_trigger(client: AsyncClient, mock_auth: str):
    # Mock the scraper so we don't hit Amazon in tests
    mock_result = ScrapeResult(
        asin="B0CHXMJRP3",
        price=89.99,
        currency="EUR",
        is_available=True,
        raw_price="€ 89,99",
    )
    with patch(
        "app.scrapers.amazon.scrape_amazon_product",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        # Add a product first
        await client.post(
            "/api/v1/products",
            json={
                "url": "https://www.amazon.it/dp/B0CHXMJRP3",
                "name": "Test Product",
                "alert_threshold": 99.99,
            },
            headers={"Authorization": "Bearer faketoken"},
        )       

        # Trigger scrape
        response = await client.post(
            "/api/v1/products/scrape",
            headers={"Authorization": "Bearer faketoken"},
        )
        assert response.status_code == 202