import secrets
from typing import Annotated

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="Passenger API Key",
    description="调用旅客安检接口所需的 API Key",
    auto_error=False,
)


def verify_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="缺少 X-API-Key 请求头",
        )

    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=403,
            detail="API Key 不正确",
        )