from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    avatar_url: str
    email: EmailStr
    
    
class UserCreate(UserBase):
    password: str
    

class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: int
    
    class Config:
        orm_mode = True
        
        
class TokenBase(BaseModel):
    token_type: str
    

class RefreshToken(TokenBase):
    refresh_token: str


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
    

class BlogBase(BaseModel):
    title: str
    chief_description: str
    content: str
    
    
class BlogCreate(BlogBase):
    pass


class BlogOut(BlogBase):
    id: int
    author: str
    created_time: datetime
    modified_time: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        

class BlogUpdate(BlogBase):
    pass
    
