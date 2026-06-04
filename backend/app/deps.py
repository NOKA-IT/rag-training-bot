"""FastAPI dependencies for authentication and role-based access control."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .auth import decode_access_token
from .models import User, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise _credentials_exc
    user_id = payload.get("sub")
    if user_id is None:
        raise _credentials_exc
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    if current.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current


def require_uploader(current: User = Depends(get_current_user)) -> User:
    """Admins and uploaders can upload / create categories."""
    if current.role not in (Role.ADMIN, Role.UPLOADER):
        raise HTTPException(status_code=403, detail="Uploader privileges required")
    return current
