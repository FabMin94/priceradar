import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    """Configure and register all scheduled jobs."""
    from app.db.base import AsyncSessionLocal
    from app.services.scraper_service import scrape_all_products

    async def run_scrape_job():
        async with AsyncSessionLocal() as db:
            await scrape_all_products(db)

    scheduler.add_job(
        run_scrape_job,
        trigger=IntervalTrigger(hours=6),
        id="scrape_all_products",
        name="Scrape all active products",
        replace_existing=True,
        misfire_grace_time=300,  # if job is late by up to 5 min, still run it
    )

    logger.info("Scheduler configured")
