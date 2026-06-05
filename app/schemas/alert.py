from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class AlertResponse(BaseModel):
    id: UUID
    product_id: UUID
    price_at_alert: Decimal
    threshold: Decimal
    triggered_at: datetime
    is_read: bool
    product_name: str | None = None

    model_config = {"from_attributes": True}