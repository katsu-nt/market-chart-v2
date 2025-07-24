from fastapi import FastAPI
from app.scheduler import start_scheduler
from app.routers import gold_prices
from app.utils.logger import get_logger
from app.database import Base, engine  # ✅ Thêm phần này để tạo bảng

app = FastAPI()
logger = get_logger(__name__)

@app.on_event("startup")
def startup_event():
    logger.info("🔧 Creating DB tables if not exists...")
    Base.metadata.create_all(bind=engine)

    start_scheduler()
    logger.info("✅ App started")

@app.get("/")
def read_root():
    return {"message": "Gold price tracking app is running"}

app.include_router(gold_prices.router)
