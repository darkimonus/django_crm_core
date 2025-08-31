class DomainError(Exception):
    """
    Base domain error (validation/logic).
    """


class BackdatedIntervalError(DomainError):
    """
    Attempt to close/open version with incorrect time window
    (e.g., change_ts <= current.valid_from).
    """


class TypeCodeNotFound(DomainError):
    """
    The specified type_code is not in EntityType reference.
    """
