import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class AirportRequest(BaseModel):
    code: str
    name: str
    city: str


class SecurityMessageRequest(BaseModel):
    mainType: str
    subType: str
    sender: str
    message: str


class PassengerInfo(BaseModel):
    fltNo: str
    fltDate: str
    brdno: Optional[str] = None
    dept: str
    seat: Optional[str] = None
    certType: Optional[str] = None
    certNo: str
    psrName: str
    psrCName: Optional[str] = None
    suspect: Optional[str] = None
    monitortips: Optional[str] = None
    securityResult: Optional[str] = None
    bagId: Optional[str] = None
    bagStatus: Optional[str] = None
    bagrStatus: Optional[str] = None
    cbagStatus: Optional[str] = None
    sbagStatus: Optional[str] = None
    face: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("fltNo")
    @classmethod
    def validate_flt_no(cls, value: str):
        value = value.strip().upper()

        if not value:
            raise ValueError("航班号不能为空")

        if not re.fullmatch(r"[A-Z0-9]{2,12}", value):
            raise ValueError(
                "航班号只能包含大写英文字母和数字，长度为 2 至 12 位"
            )

        return value

    @field_validator("fltDate")
    @classmethod
    def validate_flt_date(cls, value: str):
        value = value.strip()

        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("航班日期必须是 YYYY-MM-DD 格式")

        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("航班日期不是有效日期") from error

        return value

    @field_validator("certNo", "dept", "psrName")
    @classmethod
    def validate_required_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("该字段不能为空")

        return value

    @field_validator("seat")
    @classmethod
    def validate_seat(cls, value: Optional[str]):
        if value is None:
            return None

        value = value.strip().upper()

        if not value:
            raise ValueError("座位号不能是空字符串")

        if not re.fullmatch(r"\d{1,3}[A-Z]", value):
            raise ValueError("座位号格式错误，例如 12A、16B、108C")

        return value

    @field_validator("remark")
    @classmethod
    def validate_remark(cls, value: Optional[str]):
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("备注不能是空字符串")

        if len(value) > 200:
            raise ValueError("备注长度不能超过 200 个字符")

        return value


class PassengerUpdate(BaseModel):
    brdno: Optional[str] = None
    dept: Optional[str] = None
    seat: Optional[str] = None
    certType: Optional[str] = None
    psrName: Optional[str] = None
    psrCName: Optional[str] = None
    suspect: Optional[str] = None
    monitortips: Optional[str] = None
    securityResult: Optional[str] = None
    bagId: Optional[str] = None
    bagStatus: Optional[str] = None
    bagrStatus: Optional[str] = None
    cbagStatus: Optional[str] = None
    sbagStatus: Optional[str] = None
    face: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("seat")
    @classmethod
    def validate_seat(cls, value: Optional[str]):
        if value is None:
            return None

        value = value.strip().upper()

        if not value:
            raise ValueError("座位号不能是空字符串")

        if not re.fullmatch(r"\d{1,3}[A-Z]", value):
            raise ValueError("座位号格式错误，例如 12A、16B、108C")

        return value

    @field_validator("remark")
    @classmethod
    def validate_remark(cls, value: Optional[str]):
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("备注不能是空字符串")

        if len(value) > 200:
            raise ValueError("备注长度不能超过 200 个字符")

        return value
