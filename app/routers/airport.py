from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from app.schemas import AirportRequest

router = APIRouter(prefix="/airport", tags=["机场"])


@router.get("")
def get_airport(code: str):
    return {
        "resultCode": "0000",
        "message": "查询成功",
        "data": {
            "code": code,
            "name": "长沙黄花国际机场",
            "city": "长沙",
        },
    }


@router.post("")
def add_airport(request: AirportRequest):
    return {
        "resultCode": "0000",
        "message": "接收成功",
        "data": jsonable_encoder(request),
    }
