from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_session
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserResponse


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


@router.post(
    "/token",
    response_model=TokenResponse,
)
def login_for_access_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: Session = Depends(get_session),
):
    user = session.scalar(
        select(User).where(
            User.username == form_data.username
        )
    )

    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    access_token = create_access_token(user.username)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

@router.get("/me")
def get_my_profile(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    user_data = UserResponse.model_validate(
        current_user
    ).model_dump(mode="json")

    return {
        "code": "0000",
        "message": "获取当前用户成功",
        "data": user_data,
    }