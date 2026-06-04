"""User management endpoints (admin only)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Department
from ..auth import hash_password
from ..schemas import UserCreate, UserUpdate, UserOut
from ..deps import require_admin

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate,
                db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if payload.department_id is not None:
        if not db.query(Department).get(payload.department_id):
            raise HTTPException(status_code=400, detail="Department not found")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int,
                payload: UserUpdate,
                db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.department_id is not None:
        user.department_id = payload.department_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int,
                db: Session = Depends(get_db),
                current: User = Depends(require_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    db.delete(user)
    db.commit()
