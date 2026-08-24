"""Application-level errors and their FastAPI exception handlers.

All messages returned to the client are in French; internal code (class/attribute
names, log messages) stays in English.
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for domain errors that should be surfaced to the API client."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every error response follows the same {"detail": ...} shape."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # exc.errors() can carry the raw exception instance in ctx["error"]
        # (e.g. a ValueError raised by a @model_validator) — not JSON
        # serializable as-is, hence jsonable_encoder rather than passing it
        # straight to JSONResponse/json.dumps.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Données invalides.", "errors": jsonable_encoder(exc.errors())},
        )
