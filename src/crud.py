from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.sql.sqltypes import Integer

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
    
def get_blogs(db: Session, skip: int = 0, limit: int = 50):
    raw_sql = 'SELECT b.id, u.username, b.title, b.chief_description, b.content, b.created_time, b.modified_time FROM blog b INNER JOIN user u ON b.author = u.id LIMIT :limit OFFSET :offset'
    stat = text(raw_sql).bindparams(
        bindparam('offset', type_=Integer),
        bindparam('limit', type_=Integer)
    )
    return db.execute(stat, {'offset': skip, 'limit': limit}).fetchall()

def get_blog(db: Session, id: int):
    raw_sql = 'SELECT b.id, u.username, b.title, b.chief_description, b.content, b.created_time, b.modified_time FROM blog b INNER JOIN user u ON b.author = u.id WHERE b.id = :id'
    stat = text(raw_sql).bindparams(
        bindparam('id', type_=Integer)
    )
    return db.execute(stat, {'id': id}).first()

def get_blog_by_id(db: Session, id: int):
    return db.query(models.Blog).filter(models.Blog.id==id).first()
    
def create_blog(db: Session, blog: schemas.BlogCreate, user_id: int):
    db_blog = models.Blog(author=user_id, title=blog.title, chief_description=blog.chief_description, content=blog.content, created_time=datetime.utcnow())
    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog

def update_blog(db: Session, id: int, blog: schemas.BlogUpdate):
    db.query(models.Blog).filter(models.Blog.id==id).update(dict(title=blog.title, chief_description=blog.chief_description, content=blog.content, modified_time=datetime.utcnow()))
    db.commit()

def del_blog(db: Session, id: int):
    db.query(models.Blog).filter(models.Blog.id==id).delete()
    db.commit()
