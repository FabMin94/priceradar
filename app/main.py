from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.base import Base, engine
from app.models import product  # noqa: F401
from app.api.v1.products import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="PriceRadar",
    description="Amazon price tracker with alerts",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(products_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "priceradar"}
