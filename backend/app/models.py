"""SQLAlchemy ORM models."""
import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, Table, Enum
)
from sqlalchemy.orm import relationship

from .database import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    UPLOADER = "uploader"
    USER = "user"


# Many-to-many association between documents and categories
document_category = Table(
    "document_category",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="department")
    categories = relationship("Category", back_populates="department", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, default="")
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.USER)
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="users")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="categories")
    documents = relationship("Document", secondary=document_category, back_populates="categories")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    file_type = Column(String, default="")
    title = Column(String, default="")
    # visibility: "general" => whole company, "department" => department only
    visibility = Column(String, default="department")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing | ready | failed
    error = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="documents")
    categories = relationship("Category", secondary=document_category, back_populates="documents")
