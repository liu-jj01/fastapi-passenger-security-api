import json
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Passenger
from app.schemas import PassengerInfo, PassengerUpdate, SecurityMessageRequest
from app.security import verify_api_key

router = APIRouter(
    prefix="/security",
    tags=["旅客安检"],
    dependencies=[Depends(verify_api_key)],
)


def build_passenger_response(passenger_record: Passenger) -> dict:
    """把 JSON 业务字段与独立的 remark 列合并后返回。"""
    stored_data = json.loads(passenger_record.data_json)

    # 过滤普通字段中的 None，但保留 remark 字段。
    passenger_data = {
        key: value
        for key, value in stored_data.items()
        if value is not None
    }

    passenger_data["remark"] = passenger_record.remark
    return passenger_data


@router.post("/passenger")
def receive_passenger(
    request: SecurityMessageRequest,
    session: Session = Depends(get_session),
):
    if request.mainType != "SCRC":
        raise HTTPException(status_code=400, detail="mainType 必须是 SCRC")

    if request.subType != "PSIF":
        raise HTTPException(status_code=400, detail="subType 必须是 PSIF")

    if request.sender.strip() == "":
        raise HTTPException(status_code=400, detail="sender 不能为空")

    try:
        message_data = json.loads(request.message)
        passenger = PassengerInfo(**message_data)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="message 不是合法的 JSON 字符串",
        ) from error
    except ValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=jsonable_encoder(error.errors()),
        ) from error

    # remark 使用独立数据库列保存，其他业务字段仍保存在 data_json。
    passenger_data = passenger.model_dump(
        exclude={"remark"},
        exclude_none=True,
    )
    passenger_record = Passenger(
        cert_no=passenger.certNo,
        flt_no=passenger.fltNo,
        flt_date=passenger.fltDate,
        data_json=json.dumps(passenger_data, ensure_ascii=False),
        remark=passenger.remark,
    )

    session.add(passenger_record)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="该旅客在该航班日期的数据已经存在",
        ) from error

    total = session.scalar(
        select(func.count()).select_from(Passenger)
    ) or 0

    return {
        "code": "0000",
        "message": "旅客安检信息接收并保存成功",
        "data": {
            "mainType": request.mainType,
            "subType": request.subType,
            "sender": request.sender,
            "passenger": build_passenger_response(passenger_record),
            "total": total,
        },
    }


@router.put("/passenger")
def update_passenger(
    certNo: str,
    fltNo: str,
    fltDate: str,
    request: PassengerUpdate,
    session: Session = Depends(get_session),
):
    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="至少需要提供一个要更新的字段",
        )

    passenger_record = session.scalar(
        select(Passenger).where(
            Passenger.cert_no == certNo,
            Passenger.flt_no == fltNo,
            Passenger.flt_date == fltDate,
        )
    )

    if passenger_record is None:
        raise HTTPException(
            status_code=404,
            detail="没有找到对应的旅客航班数据",
        )

    # remark 单独更新；其他字段继续更新 data_json。
    remark_was_provided = "remark" in update_data
    remark_value = update_data.pop("remark", None)

    passenger_data = json.loads(passenger_record.data_json)
    passenger_data.pop("remark", None)
    passenger_data.update(update_data)

    validation_data = {
        **passenger_data,
        "remark": (
            remark_value
            if remark_was_provided
            else passenger_record.remark
        ),
    }

    try:
        updated_passenger = PassengerInfo(**validation_data)
    except ValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=jsonable_encoder(error.errors()),
        ) from error

    stored_data = updated_passenger.model_dump(
        exclude={"remark"},
        exclude_none=True,
    )
    passenger_record.data_json = json.dumps(
        stored_data,
        ensure_ascii=False,
    )
    passenger_record.remark = updated_passenger.remark
    session.commit()

    return {
        "code": "0000",
        "message": "旅客安检信息更新成功",
        "data": build_passenger_response(passenger_record),
    }


@router.get("/passenger")
def query_passenger(
    certNo: str,
    fltNo: str,
    fltDate: str,
    session: Session = Depends(get_session),
):
    passenger_record = session.scalar(
        select(Passenger).where(
            Passenger.cert_no == certNo,
            Passenger.flt_no == fltNo,
            Passenger.flt_date == fltDate,
        )
    )

    if passenger_record is None:
        raise HTTPException(
            status_code=404,
            detail="没有找到对应的旅客航班数据",
        )

    return {
        "code": "0000",
        "message": "查询成功",
        "data": build_passenger_response(passenger_record),
    }


@router.delete("/passenger")
def delete_passenger(
    certNo: str,
    fltNo: str,
    fltDate: str,
    session: Session = Depends(get_session),
):
    passenger_record = session.scalar(
        select(Passenger).where(
            Passenger.cert_no == certNo,
            Passenger.flt_no == fltNo,
            Passenger.flt_date == fltDate,
        )
    )

    if passenger_record is None:
        raise HTTPException(
            status_code=404,
            detail="没有找到需要删除的旅客航班数据",
        )

    session.delete(passenger_record)
    session.commit()

    return {
        "code": "0000",
        "message": "旅客安检信息删除成功",
        "data": {
            "certNo": certNo,
            "fltNo": fltNo,
            "fltDate": fltDate,
        },
    }


@router.get("/passengers")
def query_passenger_list(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    certNo: Optional[str] = None,
    fltNo: Optional[str] = None,
    fltDate: Optional[str] = None,
    psrName: Optional[str] = Query(default=None, min_length=1, max_length=50),
    sortBy: Literal["id", "createdAt"] = "id",
    sortOrder: Literal["asc", "desc"] = "desc",
    session: Session = Depends(get_session),
):
    filters = []

    if certNo:
        filters.append(Passenger.cert_no == certNo)

    if fltNo:
        filters.append(Passenger.flt_no == fltNo)

    if fltDate:
        filters.append(Passenger.flt_date == fltDate)

    if psrName:
        filters.append(
            func.json_extract(
                Passenger.data_json,
                "$.psrName",
            ).like(f"%{psrName.strip()}%")
        )

    total_statement = select(func.count()).select_from(Passenger)
    if filters:
        total_statement = total_statement.where(*filters)

    total = session.scalar(total_statement) or 0
    offset = (page - 1) * pageSize

    sort_column_map = {
        "id": Passenger.id,
        "createdAt": Passenger.created_at,
    }
    sort_column = sort_column_map[sortBy]
    order_expression = (
        asc(sort_column)
        if sortOrder == "asc"
        else desc(sort_column)
    )

    query_statement = select(Passenger)
    if filters:
        query_statement = query_statement.where(*filters)

    query_statement = (
        query_statement
        .order_by(order_expression)
        .limit(pageSize)
        .offset(offset)
    )

    passenger_records = session.scalars(query_statement).all()
    passenger_list = []

    for passenger_record in passenger_records:
        passenger_data = build_passenger_response(passenger_record)
        passenger_data["id"] = passenger_record.id
        passenger_data["createdAt"] = passenger_record.created_at
        passenger_list.append(passenger_data)

    total_pages = (total + pageSize - 1) // pageSize

    return {
        "code": "0000",
        "message": "查询成功",
        "data": {
            "list": passenger_list,
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "totalPages": total_pages,
        },
    }
