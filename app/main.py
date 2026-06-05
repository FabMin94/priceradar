import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base, engine
from app.models import product  # noqa: F401
from app.api.v1.products import router as products_router
from app.api.v1.alerts import router as alerts_router
from app.core.scheduler import scheduler, setup_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_scheduler()
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(
    title="PriceRadar",
    description="Amazon price tracker with alerts",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(products_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "priceradar"}
