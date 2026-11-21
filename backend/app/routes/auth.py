import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import COOKIE_NAME, COOKIE_SECURE, SESSION_DAYS
from ..db import get_db
from ..models import User
from ..schemas import LoginIn, SignupIn
from ..security import burn_time, hash_password, login_limiter, make_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _start_session(response: Response, user: User) -> None:
    # httponly: JavaScript cannot read it (protects against XSS theft). samesite=lax: blocks cross-site POSTs.
    response.set_cookie(COOKIE_NAME, make_token(user.id), max_age=SESSION_DAYS * 86400,
                        httponly=True, samesite="lax", secure=COOKIE_SECURE, path="/")


def public_user(u: User) -> dict:
    return {"name": u.name, "email": "" if u.is_guest else u.email, "guest": 1 if u.is_guest else 0}


@router.post("/signup")
def signup(body: SignupIn, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "An account with this email already exists. Log in instead.")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists. Log in instead.")
    _start_session(response, user)
    return public_user(user)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    if not login_limiter.allow(f"{ip}|{body.email}"):
        raise HTTPException(429, "Too many attempts. Try again in a few minutes.")
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None:
        burn_time()
    if user is None or user.is_guest or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    _start_session(response, user)
    return public_user(user)


@router.post("/guest")
def guest(response: Response, db: Session = Depends(get_db)):
    user = User(email=f"guest-{secrets.token_hex(8)}@guest.invalid", name="Student", is_guest=True,
                password_hash=hash_password(secrets.token_urlsafe(24)))
    db.add(user)
    db.commit()
    _start_session(response, user)
    return public_user(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
