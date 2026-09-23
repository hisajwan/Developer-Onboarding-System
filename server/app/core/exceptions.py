"""Domain-level errors and the single place that maps them to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class. Subclasses set the HTTP status and a stable machine-readable code."""

    status_code = 500
    code = "app_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "not_authenticated"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"


class AccountAlreadyExistsError(AppError):
    status_code = 409
    code = "account_already_exists"


class InvalidDocumentError(AppError):
    status_code = 422
    code = "invalid_document"


class DocumentTooLargeError(AppError):
    status_code = 413
    code = "document_too_large"


class LinterError(AppError):
    """The snippet linter ran but failed (crashed, timed out, or returned something unreadable)."""

    status_code = 502
    code = "linter_failed"


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
