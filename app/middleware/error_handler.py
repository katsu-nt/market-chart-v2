from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from pydantic import ValidationError
import logging
import traceback

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except StarletteHTTPException as e:
            # 404, 403, 401...
            return JSONResponse(
                status_code=e.status_code,
                content={"status": "error", "message": e.detail}
            )
        except RequestValidationError as e:
            # Lỗi validate input query/body/params
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Validation error",
                    "detail": e.errors()
                }
            )
        except ValidationError as e:
            # Lỗi validate pydantic (response, model custom)
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Validation error",
                    "detail": e.errors()
                }
            )
        except IntegrityError as e:
            # Lỗi constraint SQL (dupe key, unique, not null...)
            logging.error(f"IntegrityError: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Database integrity error",
                    "detail": str(e.orig) if hasattr(e, "orig") else str(e)
                }
            )
        except DataError as e:
            # Lỗi data nhập vào DB sai kiểu, out of range, ...
            logging.error(f"DataError: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Database data error",
                    "detail": str(e.orig) if hasattr(e, "orig") else str(e)
                }
            )
        except SQLAlchemyError as e:
            # Các lỗi SQLAlchemy khác
            logging.error(f"SQLAlchemyError: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Database error",
                    "detail": str(e)
                }
            )
        except Exception as e:
            # Lỗi không xác định khác
            logging.exception("Unhandled Exception")
            # Ghi rõ traceback cho log, ẩn chi tiết khi trả cho user (hoặc chỉ show trong dev)
            detail = traceback.format_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": str(e),
                    # "detail": detail    # Bỏ comment nếu muốn debug trên dev
                }
            )
