from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


def get_current_user(x_username: str = Header(...), db: Session = Depends(get_db)) -> User:
    """Get or create user by username header."""
    user = db.execute(select(User).where(User.username == x_username)).scalar_one_or_none()
    if user is None:
        user = User(username=x_username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user
