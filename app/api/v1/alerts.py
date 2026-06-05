from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.alert import AlertResponse
from app.services.alert_service import (
    get_user_alerts,
    mark_alert_read,
    AlertNotFoundError,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await get_user_alerts(db, user_id, unread_only=unread_only)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def read_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    try:
        return await mark_alert_read(db, alert_id, user_id)
    except AlertNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))