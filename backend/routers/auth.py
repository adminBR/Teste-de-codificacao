## routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.base import get_db
from services.auth import login_service, register_service, refresh_service
from utils.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    MissingTokenError,
    UserCantBeCreatedError,
)
from schemas.auth import (
    UserLogin,
    UserRegister,
    Token,
    TokenOut,
    TokenRefreshOut,
    UserOut,
)

router = APIRouter()


# [] Log the user returning the tokens
@router.post("/login", response_model=TokenOut)
async def login_user(form_data: UserLogin = Form(), db: Session = Depends(get_db)):
    try:
        token = login_service(form_data, db)
        return token
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


# [] Register a new user as non-admin
@router.post("/register", response_model=UserOut)
async def register_user(
    form_data: UserRegister = Form(), db: Session = Depends(get_db)
):
    try:
        user = register_service(form_data, db)
        return user
    except UserCantBeCreatedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


# [] Refresh the access token, given the refresh token
@router.post("/refresh", response_model=TokenRefreshOut)
async def refresh_user(form_data: Token = Form(), db: Session = Depends(get_db)):
    try:
        token = refresh_service(form_data, db)
        return token
    except InvalidCredentialsError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except MissingTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
