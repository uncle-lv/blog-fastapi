from datetime import datetime

from sqlalchemy.orm import Session

import models, schemas, security


def get_user(db: Session, id: int):
    return db.query(models.User).filter(models.User.id==id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email==email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username==username).first()

def get_users(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.hash_password(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password, avatar_url=user.avatar_url, created_time=datetime.utcnow())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_last_login(db: Session, id: int):
    db.query(models.User).filter(models.User.id==id).update(dict(last_login=datetime.utcnow()))
    db.commit()