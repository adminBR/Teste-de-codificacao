from fastapi import status


class InvalidCredentialsError(Exception):
    pass


class MissingTokenError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class UserCantBeCreatedError(Exception):
    pass


class ForbiddenAccessError(Exception):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Admins only."
