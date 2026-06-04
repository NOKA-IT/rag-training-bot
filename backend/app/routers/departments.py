"""Department management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Department, User
from ..schemas import DepartmentCreate, DepartmentOut
from ..deps import require_admin, get_current_user

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db),
                     _: User = Depends(get_current_user)):
    return db.query(Department).all()


@router.post("", response_model=DepartmentOut, status_code=201)
def create_department(payload: DepartmentCreate,
                      db: Session = Depends(get_db),
                      _: User = Depends(require_admin)):
    if db.query(Department).filter(Department.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Department already exists")
    dept = Department(name=payload.name, description=payload.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}", status_code=204)
def delete_department(dept_id: int,
                      db: Session = Depends(get_db),
                      _: User = Depends(require_admin)):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(dept)
    db.commit()
