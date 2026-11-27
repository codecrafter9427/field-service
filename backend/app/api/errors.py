"""HTTP error helpers with the shared error envelope."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


def api_error(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "details": details}},
    )


def not_found(entity: str = "Resource") -> HTTPException:
    return api_error(status.HTTP_404_NOT_FOUND, "not_found", f"{entity} not found")


def bad_request(code: str, message: str, details: Any = None) -> HTTPException:
    return api_error(status.HTTP_400_BAD_REQUEST, code, message, details)


def conflict(message: str = "Resource was modified", details: Any = None) -> HTTPException:
    return api_error(
        status.HTTP_409_CONFLICT,
        "conflict",
        message,
        details,
    )
