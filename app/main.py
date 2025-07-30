from fastapi import FastAPI
from app.scheduler import start_scheduler
from app.routers import gold_prices
from app.utils.logger import get_logger
from app.database import Base, engine 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = get_logger(__name__)
#Middle ware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#App start up
@app.on_event("startup")
def startup_event():
    logger.info("🔧 Creating DB tables if not exists...")
    Base.metadata.create_all(bind=engine)

    start_scheduler()
    logger.info("✅ App started")

app.include_router(gold_prices.router)
