
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.error_handler import ExceptionMiddleware
from app.routers.gold import router as gold_router
from app.routers.exchange import router as exchange_router

app = FastAPI(
    title="Market Backend API",
    description="Backend hệ thống quản lý giá vàng, tỷ giá, chỉ số tài chính...",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: siết lại origin trong môi trường production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware handle exception
app.add_middleware(ExceptionMiddleware)

# Routers 
app.include_router(gold_router)
app.include_router(exchange_router)

