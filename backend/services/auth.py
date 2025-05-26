## services/auth.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Response
from datetime import datetime, timezone

from utils.hashing import verify_password, get_password_hash
from utils.jwt import create_access_token, decode_token_str
from utils.exceptions import (
    InvalidCredentialsError,
    UserCantBeCreatedError,
    InvalidTokenError,
    MissingTokenError,
)

from database.models import User
from schemas.auth import (
    Token,
    TokenOut,
    TokenRefreshOut,
    UserLogin,
    UserRegister,
    UserOut,
)


def login_service(data: UserLogin, db: Session) -> TokenOut:
    user = db.query(User).filter(User.usr_email == data.username).first()

    # Check if the user exists and if password if valid
    if user is None or not verify_password(data.password, user.usr_password):
        raise InvalidCredentialsError

    # Using usr_id as a generic way to get user info from the token later
    _access_token = create_access_token({"sub": user.usr_id}, 30)
    _refresh_token = create_access_token({"sub": user.usr_id}, 10080)

    return TokenOut(access_token=_access_token, refresh_token=_refresh_token)


def register_service(data: UserRegister, db: Session) -> UserOut:
    # Check if email is used already and then create user if not
    existing_user = db.query(User).filter(User.usr_email == data.email).first()
    if existing_user:
        raise UserCantBeCreatedError

    hashed_password = get_password_hash(data.password)
    new_user = User(
        usr_name=data.name,
        usr_email=data.email,
        usr_password=hashed_password,
        usr_isadmin=False,
    )

    db.add(new_user)
    db.commit()

    # Refreshing to get the usr_id generate by the database
    db.refresh(new_user)

    return UserOut.model_validate(new_user)


# Extra raises on refresh to help the frontend debug
def refresh_service(data: Token, db: Session) -> TokenRefreshOut:

    refresh_token_str = data.refresh_token
    # Check if theres a refresh token before trying to decode
    if not refresh_token_str:
        raise MissingTokenError

    payload = decode_token_str(refresh_token_str)

    if not payload:
        raise InvalidTokenError

    # Try to get a valid usr_id from the refresh token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: Missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: User identifier format incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check that the user still exists in the database
    user = db.query(User).filter(User.usr_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a new access token for the user
    new_access_token = create_access_token({"sub": str(user.usr_id)}, expire_minutes=30)

    return TokenRefreshOut(access_token=new_access_token)
