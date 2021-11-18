from datetime import datetime, timedelta

from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

import crud
import db
import schemas


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token',
    )
    
    
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(raw_password: str, hashed_password):
    return pwd_context.verify(raw_password, hashed_password)

def authenticate_user(username: str, password: str, db: Session):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expired_time = datetime.utcnow() + expires_delta
    to_encode.update({'exp': expired_time})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('username')
        if username is None:
            raise credentials_exception   
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Signature has expired'
        )
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
