from pydantic import BaseModel, HttpUrl, field_validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.core.amazon import extract_asin, is_amazon_url


class ProductCreate(BaseModel):
    url: str
    name: str
    alert_threshold: Decimal | None = None

    @field_validator("url")
    @classmethod
    def validate_amazon_url(cls, v: str) -> str:
        if not is_amazon_url(v):
            raise ValueError("URL must be an Amazon product URL")
        if not extract_asin(v):
            raise ValueError("Could not extract ASIN from URL")
        return v
    

class PriceHistoryResponse(BaseModel):
    id: UUID
    price: Decimal
    currency: str
    is_available: bool
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: UUID
    user_id: UUID
    url: str
    name: str
    asin: str
    alert_threshold: Decimal | None
    is_active: bool
    created_at: datetime
    latest_price: Decimal | None = None
    price_history: list[PriceHistoryResponse] = []

    model_config = {"from_attributes": True}


class ProductSummary(BaseModel):
    id: UUID
    name: str
    asin: str
    url: str
    alert_threshold: Decimal | None
    is_active: bool
    created_at: datetime
    latest_price: Decimal | None = None

    model_config = {"from_attributes": True}