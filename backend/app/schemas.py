"""Pydantic schemas for request/response validation."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from .models import Role


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Department ----------
class DepartmentBase(BaseModel):
    name: str
    description: str = ""


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- User ----------
class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    role: Role = Role.USER
    department_id: Optional[int] = None


class UserUpdate(BaseModel):
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Role] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: Role
    is_active: bool
    department_id: Optional[int] = None
    department: Optional[DepartmentOut] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Category ----------
class CategoryCreate(BaseModel):
    name: str
    department_id: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    department_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Document ----------
class DocumentOut(BaseModel):
    id: int
    filename: str
    title: str
    file_type: str
    visibility: str
    department_id: Optional[int] = None
    uploaded_by: Optional[int] = None
    chunk_count: int
    status: str
    error: str
    created_at: datetime
    categories: List[CategoryOut] = []

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRequest(BaseModel):
    question: str
    department_id: Optional[int] = None
    category_ids: Optional[List[int]] = None


class Source(BaseModel):
    document_id: int
    filename: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
