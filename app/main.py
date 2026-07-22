from fastapi import FastAPI

from app.config import settings
from app.exception_handlers import register_exception_handlers
from app.request_logging import register_request_logging
from app.routers import airport, passenger


app = FastAPI(title=settings.app_name)

register_exception_handlers(app)
register_request_logging(app)

app.include_router(airport.router)
app.include_router(passenger.router)

@app.get("/health", tags=["系统"])
def health_check():
    return {
        "code": "0000",
        "message": "服务运行正常",
        "data": {
            "status": "up",
        },
    }