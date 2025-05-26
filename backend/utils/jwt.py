## utils/jwt.py
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
import jwt
from sqlalchemy.orm import Session

from config import SECRET_KEY_AUTH, JWT_ALGORITHM, OAUTH_LOGIN_REFERENCE
from database.models import User  # Import User model
from database.base import get_db  # Import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH_LOGIN_REFERENCE)


# Take values, how long it will last and a secret key to generate and return a jwt token
def create_access_token(data: dict, expire_minutes: int) -> str:
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_AUTH, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# Returns the values extracted from the jwt token
def decode_token_str(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY_AUTH, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# Returns the user id extracted from the bearer token
def get_current_user_id_from_token(token: str = Depends(oauth2_scheme)) -> int:
    payload = decode_token_str(token)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token: subject missing"
        )
    try:
        user_id = int(user_id_str)
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token: subject is not a valid ID",
        )


# Dependency to get the current User object
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    payload = decode_token_str(token)
    user_id_str = payload.get("sub")

    if user_id_str is None:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token: subject missing"
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token: subject is not a valid ID",
        )

    # Since the userbase is unknown, the func will also check on the db to validate the token
    user = db.query(User).filter(User.usr_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
