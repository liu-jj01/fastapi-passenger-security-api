import logging
import time

from fastapi import FastAPI, Request


logger = logging.getLogger("uvicorn.error")


def register_request_logging(app: FastAPI) -> None:

    @app.middleware("http")
    async def log_request(
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.exception(
                "%s %s status=500 duration=%.2fms",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.info(
            "%s %s status=%s duration=%.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Process-Time-Ms"] = (
            f"{duration_ms:.2f}"
        )

        return response