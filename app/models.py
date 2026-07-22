from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base



class Passenger(Base):
    __tablename__ = "passengers"
    __table_args__ = (
        UniqueConstraint(
            "cert_no",
            "flt_no",
            "flt_date",
            name="uq_passenger_cert_flight_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    cert_no: Mapped[str] = mapped_column(String, nullable=False)
    flt_no: Mapped[str] = mapped_column(String, nullable=False)
    flt_date: Mapped[str] = mapped_column(String, nullable=False)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    remark: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
