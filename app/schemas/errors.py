from pydantic import BaseModel


class ErrorBody(BaseModel):
    error: str
    message: str


class ErrorResponse(BaseModel):
    """Format imposé pour toutes les erreurs métier (400, 401, 403, 404, 409)."""

    detail: ErrorBody
