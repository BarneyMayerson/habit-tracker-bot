from typing import Any


class APIError(Exception):
    """Basic exception for all server API errors."""


class AuthenticationError(APIError):
    """AuthenticationError (ivalid token, expired token etc."""

    def __init__(self, detail: str | None = None):
        super().__init__(detail or "Authentication failed")


class AuthorizationError(APIError):
    def __init__(self):
        super().__init__("Authorization required or token expired")


class NotFoundError(APIError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found")


class ValidationError(APIError):
    def __init__(self, detail: Any = None):
        super().__init__(detail or "Validation error")


class HabitAlreadyCompletedError(APIError):
    def __init__(self):
        super().__init__("Habit already completed today")


class ServerError(APIError):
    def __init__(self, detail: str | None = None):
        super().__init__(detail or "Internal server error")
