"""Bootstrap a default admin user on first launch.

The default admin credentials are read from environment variables
(ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL). Change the password
immediately after first login in production.
"""
from .database import SessionLocal
from .models import User, Role
from .auth import hash_password
from .config import settings


def ensure_default_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == Role.ADMIN).first()
        if existing_admin:
            return
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"[init] Created default admin user '{settings.ADMIN_USERNAME}'.")
    finally:
        db.close()


if __name__ == "__main__":
    from .database import init_db
    init_db()
    ensure_default_admin()
