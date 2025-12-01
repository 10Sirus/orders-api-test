"""
Custom exceptions
exceptions.py
"""

class DomainError(Exception):
    status_code = 500
    code = ""

    def __init__(self, message: str, status_code: int = None, code: str = None):
        self.message = message
        self.code = code
        if status_code:
            self.status_code = status_code
        if code:
            self.code = code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, message="Not found"):
        self.code = "not found"
        super().__init__(message, status_code=404, code="not found")


class ConflictError(DomainError):
    def __init__(self, message="Conflict"):
        self.code = "conflict"
        super().__init__(message, status_code=409, code="conflict")



class ValidationError(DomainError):
    def __init__(self, message="Validation failed"):
        self.code = "validation failed"
        super().__init__(message, status_code=400, code="validation failed")


class PreconditionFailedError(DomainError):
    def __init__(self, message="Precondition failed"):
        self.code = "precondition failed"
        super().__init__(message, status_code=412, code="precondition failed")


class InternalServerError(DomainError):
    """Raised when an unexpected internal error occurs."""
    def __init__(self, message="Internal server error"):
        self.code = "internal server error"
        super().__init__(message, status_code=500, code="internal server error")
