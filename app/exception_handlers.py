from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

ERROR_CODE_MAP = {
    400: "4000",
    401: "4001",
    403: "4003",
    404: "4004",
    405: "4005",
    409: "4009",
    422: "4220",
}


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exception: StarletteHTTPException,
    ):
        error_code = ERROR_CODE_MAP.get(
            exception.status_code,
            str(exception.status_code),
        )

        if isinstance(exception.detail, str):
            message = exception.detail
            data = None
        else:
            message = "请求处理失败"
            data = jsonable_encoder(exception.detail)

        return JSONResponse(
            status_code=exception.status_code,
            content={
                "code": error_code,
                "message": message,
                "data": data,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exception: RequestValidationError,
    ):
        return JSONResponse(
            status_code=422,
            content={
                "code": "4220",
                "message": "请求参数校验失败",
                "data": jsonable_encoder(exception.errors()),
            },
        )
