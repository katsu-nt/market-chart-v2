from fastapi import FastAPI
from app.scheduler import start_scheduler
from app.routers import gold_prices
from app.utils.logger import get_logger

app = FastAPI()

logger = get_logger(__name__)

@app.on_event("startup")
def startup_event():
    start_scheduler()
    logger.info("✅ App started")

@app.get("/")
def read_root():
    return {"message": "Gold price tracking app is running"}

app.include_router(gold_prices.router)