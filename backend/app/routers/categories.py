"""Category management endpoints. Uploaders create categories in their dept."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, Department, User, Role
from ..schemas import CategoryCreate, CategoryOut
from ..deps import require_uploader, get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=List[CategoryOut])
def list_categories(department_id: Optional[int] = None,
                    db: Session = Depends(get_db),
                    current: User = Depends(get_current_user)):
    q = db.query(Category)
    if department_id is not None:
        q = q.filter(Category.department_id == department_id)
    elif current.role != Role.ADMIN and current.department_id is not None:
        # Non-admins see their department's categories plus global (None) ones
        q = q.filter(
            (Category.department_id == current.department_id)
            | (Category.department_id.is_(None))
        )
    return q.all()


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate,
                    db: Session = Depends(get_db),
                    current: User = Depends(require_uploader)):
    dept_id = payload.department_id
    # Uploaders may only create categories within their own department
    if current.role == Role.UPLOADER:
        dept_id = current.department_id
        if dept_id is None:
            raise HTTPException(status_code=400,
                                detail="Uploader has no assigned department")
    if dept_id is not None and not db.query(Department).get(dept_id):
        raise HTTPException(status_code=400, detail="Department not found")

    category = Category(name=payload.name, department_id=dept_id,
                        created_by=current.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int,
                    db: Session = Depends(get_db),
                    current: User = Depends(require_uploader)):
    category = db.query(Category).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if current.role == Role.UPLOADER and category.department_id != current.department_id:
        raise HTTPException(status_code=403,
                            detail="Cannot delete category outside your department")
    db.delete(category)
    db.commit()
