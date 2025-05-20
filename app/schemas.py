from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# For registration input
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# For response (excluding password)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_verified: bool

    class Config:
        orm_mode = True

# For login response (optional)
class Token(BaseModel):
    access_token: str
    token_type: str

# Task schema for creating task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: datetime
    priority: str
    assignee_email: EmailStr

# Task response schema
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    deadline: datetime
    priority: str
    status: str
    file_path: Optional[str]

    class Config:
        orm_mode = True
