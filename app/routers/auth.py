from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["用户认证"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: UserCreate,
    session: Session = Depends(get_session),
):
    existing_user = session.scalar(
        select(User).where(User.username == request.username)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="用户名已经存在",
        )

    user = User(
        username=request.username,
        hashed_password=hash_password(request.password),
    )

    session.add(user)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="用户名已经存在",
        ) from error

    session.refresh(user)

    user_data = UserResponse.model_validate(user).model_dump(
        mode="json"
    )

    return {
        "code": "0000",
        "message": "用户注册成功",
        "data": user_data,
    }