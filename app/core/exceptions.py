"""Domain exceptions and audit action enum."""

from enum import StrEnum


# ── Domain Exceptions ─────────────────────────────────────────────────────────


class AppException(Exception):
    """Base exception for all application domain errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when an entity is not found."""

    def __init__(self, entity: str, entity_id: int | str | None = None):
        detail = f"{entity} not found" if entity_id is None else f"{entity} {entity_id} not found"
        super().__init__(message=detail, status_code=404)


class ForbiddenException(AppException):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    """Raised on duplicate or conflicting state."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message=message, status_code=409)


class ValidationException(AppException):
    """Raised on business-rule validation failures."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)


# ── Audit Action Enum ─────────────────────────────────────────────────────────


class AuditAction(StrEnum):
    # Auth
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    ACCEPT_INVITATION = "ACCEPT_INVITATION"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"
    FORGOT_PASSWORD_UNKNOWN = "FORGOT_PASSWORD_UNKNOWN"
    RESET_PASSWORD = "RESET_PASSWORD"

    # Admin
    CHANGE_ROLE = "CHANGE_ROLE"
    CHANGE_STATUS = "CHANGE_STATUS"
    INVITE_EVALUATOR = "INVITE_EVALUATOR"
    RESEND_INVITATION = "RESEND_INVITATION"
    REVOKE_INVITATION = "REVOKE_INVITATION"

    # Events
    CREATE_EVENT_MANUAL = "CREATE_EVENT_MANUAL"
    IMPORT_EVENT = "IMPORT_EVENT"
    UPDATE_EVENT = "UPDATE_EVENT"
    DELETE_EVENT = "DELETE_EVENT"
    ADD_EVENT_EVALUATOR = "ADD_EVENT_EVALUATOR"
    DELETE_EVENT_EVALUATOR = "DELETE_EVENT_EVALUATOR"

    # Groups
    CREATE_GROUP = "CREATE_GROUP"
    UPDATE_GROUP = "UPDATE_GROUP"
    DELETE_GROUP = "DELETE_GROUP"
    ASSIGN_GROUP_EVALUATOR = "ASSIGN_GROUP_EVALUATOR"
    DELETE_GROUP_EVALUATOR = "DELETE_GROUP_EVALUATOR"

    # Participants
    ADD_PARTICIPANT = "ADD_PARTICIPANT"
    UPDATE_PARTICIPANT = "UPDATE_PARTICIPANT"
    DELETE_PARTICIPANT = "DELETE_PARTICIPANT"
    MOVE_PARTICIPANT = "MOVE_PARTICIPANT"

    # Activities
    CREATE_ACTIVITY = "CREATE_ACTIVITY"
    UPDATE_ACTIVITY = "UPDATE_ACTIVITY"
    DELETE_ACTIVITY = "DELETE_ACTIVITY"

    # Records
    CREATE_RECORD = "CREATE_RECORD"
    UPDATE_RECORD = "UPDATE_RECORD"
    DELETE_RECORD = "DELETE_RECORD"
    BULK_SUBMIT_RECORDS = "BULK_SUBMIT_RECORDS"

    # Age categories
    CREATE_AGE_CATEGORY = "CREATE_AGE_CATEGORY"
    DELETE_AGE_CATEGORY = "DELETE_AGE_CATEGORY"

    # Diplomas
    CREATE_DIPLOMA = "CREATE_DIPLOMA"
    UPDATE_DIPLOMA = "UPDATE_DIPLOMA"
    DELETE_DIPLOMA = "DELETE_DIPLOMA"
