from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Alert, Product


class AlertNotFoundError(Exception):
    pass


async def get_user_alerts(
    db: AsyncSession,
    user_id: str,
    unread_only: bool = False,
) -> list[Alert]:
    """Get all alerts for products owned by user."""
    query = (
        select(Alert)
        .join(Product, Alert.product_id == Product.id)
        .where(Product.user_id == UUID(user_id))
        .options(selectinload(Alert.product))
        .order_by(Alert.triggered_at.desc())
    )

    if unread_only:
        query = query.where(Alert.is_read == False)  # noqa: E712

    result = await db.execute(query)
    alerts = list(result.scalars().all())

    # Attach product name for convenience
    for alert in alerts:
        alert.product_name = alert.product.name if alert.product else None

    return alerts


async def mark_alert_read(
    db: AsyncSession,
    alert_id: UUID,
    user_id: str,
) -> Alert:
    """Mark a single alert as read."""
    result = await db.execute(
        select(Alert)
        .join(Product, Alert.product_id == Product.id)
        .where(
            Alert.id == alert_id,
            Product.user_id == UUID(user_id),
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise AlertNotFoundError(f"Alert {alert_id} not found")

    alert.is_read = True
    await db.flush()
    return alert
