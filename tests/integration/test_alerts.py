from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.scrapers.amazon import ScrapeResult


async def _setup_alert(client: AsyncClient) -> dict:
    """Helper: add product, scrape below threshold, return alert."""
    await client.post(
        "/api/v1/products",
        json={
            "url": "https://www.amazon.it/dp/B0CHXMJRP3",
            "name": "Test Product",
            "alert_threshold": 99.99,
        },
        headers={"Authorization": "Bearer faketoken"},
    )

    mock_result = ScrapeResult(
        asin="B0CHXMJRP3",
        price=79.99,  # below threshold
        currency="EUR",
        is_available=True,
        raw_price="€ 79,99",
    )
    with patch(
        "app.scrapers.amazon.scrape_amazon_product",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        await client.post(
            "/api/v1/products/scrape",
            headers={"Authorization": "Bearer faketoken"},
        )

    response = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer faketoken"},
    )
    return response.json()[0]


async def test_alert_triggered_when_price_below_threshold(
    client: AsyncClient, mock_auth: str
):
    alert = await _setup_alert(client)
    assert float(alert["price_at_alert"]) == 79.99
    assert float(alert["threshold"]) == 99.99
    assert alert["is_read"] is False


async def test_list_alerts_unread_only(client: AsyncClient, mock_auth: str):
    await _setup_alert(client)

    response = await client.get(
        "/api/v1/alerts?unread_only=true",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_mark_alert_read(client: AsyncClient, mock_auth: str):
    alert = await _setup_alert(client)
    alert_id = alert["id"]

    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/read",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True

    # Unread list should now be empty
    unread = await client.get(
        "/api/v1/alerts?unread_only=true",
        headers={"Authorization": "Bearer faketoken"},
    )

    assert len(unread.json()) == 0


async def test_alerts_no_token(client: AsyncClient):
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 401
