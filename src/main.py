from datetime import timedelta
from typing import List

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

import db, schemas, models, crud, security


app = FastAPI()


@app.on_event('startup')
async def startup():
    await db.database.connect()


@app.on_event('shutdown')
async def shutdown():
    await db.database.disconnect()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post('/api/users', response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(db.get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail='Email already registered'
            )
    
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail='Username already registered'
            )
    
    return crud.create_user(db, user)


@app.get('/api/users/{id}', response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def get_user_by_id(id: int, db: Session = Depends(db.get_db)):
    db_user = crud.get_user(db, id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='User not found'
            )
    return db_user


@app.get('/api/users', response_model=List[schemas.UserOut], status_code=status.HTTP_200_OK)
async def get_users(skip: int = 0, limit: int = 50, db: Session = Depends(db.get_db)):
    users = crud.get_users(db, skip, limit)
    return users


@app.post('/api/login/oauth/access_token', status_code=status.HTTP_201_CREATED)
async def create_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db.get_db)):
    user = security.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    access_token = security.create_token(
        data={'username': user.username},
        expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = security.create_token(
        data={'username': user.username},
        expires_delta=timedelta(days=security.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    crud.update_last_login(db, user.id)
    return {
        'token_type': 'Bearer', 
        'access_token': access_token,
        'refresh_token': refresh_token
        }
    

@app.post('/api/login/oauth/access_token/refresh')
async def refresh_access_token(refresh_token: schemas.RefreshToken):
    username = None
    try:
        payload = jwt.decode(
            refresh_token.refresh_token, 
            security.SECRET_KEY, 
            algorithms=[security.ALGORITHM]
            )
        username: str = payload.get('username')
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid credentials',
                headers={'WWW-Authenticate': 'Bearer'}
                )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Signature has expired'
        )
        
    access_token = security.create_token(
        data={'username': username},
        expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        'token_type': 'Bearer', 
        'access_token': access_token,
    }


@app.get('/api/auth/current_user', response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def get_current_user(current_user: models.User = Depends(security.get_current_user)):
    return current_user


@app.get('/api/blogs', status_code=status.HTTP_200_OK)
async def get_blogs(skip: int = 0, limit: int = 50, db: Session = Depends(db.get_db)):
    blogs = []
    result = crud.get_blogs(db, skip, limit)
    
    for row in result:
        blog = schemas.BlogOut(
            id=row['id'],
            author=row['username'],
            title=row['title'],
            chief_description=row['chief_description'],
            content=row['content'],
            created_time=row['created_time'],
            modified_time=row['modified_time']
        )
        blogs.append(blog)
    
    return blogs


@app.get('/api/blogs/{id}', status_code=status.HTTP_200_OK)
async def get_blog_by_id(id: int, db: Session = Depends(db.get_db)):
    result_row = crud.get_blog(db, id)
    if result_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Blog not found'
        )
    
    blog = schemas.BlogOut(
        id=result_row['id'],
        author=result_row['username'],
        title=result_row['title'],
        chief_description=result_row['chief_description'],
        content=result_row['content'],
        created_time=result_row['created_time'],
        modified_time=result_row['modified_time']
        )
        
    return blog


@app.post('/api/blogs', response_model=schemas.BlogOut, status_code=status.HTTP_201_CREATED)
async def create_blog(blog: schemas.BlogCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(db.get_db)):
    return crud.create_blog(db, blog, current_user.id)


@app.patch('/api/blogs/{id}', status_code=status.HTTP_200_OK)
async def update_blog(blog: schemas.BlogUpdate, id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(db.get_db)):
    db_blog = crud.get_blog_by_id(db, id)
    author = crud.get_user(db, db_blog.author)
    if author.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Permission denied'
        )
    
    crud.update_blog(db, id, blog)
    return crud.get_blog(db, id)


@app.delete('/api/blogs/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def del_blog(id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(db.get_db)):
    db_blog = crud.get_blog_by_id(db, id)
    
    if db_blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Blog not found'
        )
    
    author = crud.get_user(db, db_blog.author)
    if author.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Permission denied'
        )
        
    crud.del_blog(db, id)
    return
