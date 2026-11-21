from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import COOKIE_NAME
from .db import get_db
from .models import User
from .security import read_token


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = read_token(request.cookies.get(COOKIE_NAME, ""))
    user = db.get(User, uid) if uid else None
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user
