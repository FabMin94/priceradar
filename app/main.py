from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.base import Base, engine
from app.models import product # noqa: F401


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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "priceradar"}
