from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductSummary
from app.services.product_service import (
    create_product,
    get_user_products,
    get_product_detail,
    delete_product,
    ProductNotFoundError,
    ProductAlreadyTrackedError,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductSummary, status_code=status.HTTP_201_CREATED)
async def add_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    try:
        product = await create_product(db, data, user_id)
        product.latest_price = None
        return product
    except ProductAlreadyTrackedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    

@router.get("", response_model=list[ProductSummary])
async def list_products(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await get_user_products(db, user_id)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    try:
        return await get_product_detail(db, product_id, user_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),    
):
    try:
        await delete_product(db, product_id, user_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))    