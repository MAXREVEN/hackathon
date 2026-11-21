"""Shapes of the JSON the front sends. Short keys (sid, upd, t...) match what the front already uses."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

ID = dict(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=200)

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("Enter a valid email address")
        return v


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return v.strip().lower()


class SubIn(BaseModel):
    id: str = Field(**ID)
    name: str = Field(min_length=1, max_length=40)


class NoteIn(BaseModel):
    id: str = Field(**ID)
    sid: str = Field(**ID)
    title: str = Field(min_length=1, max_length=100)
    body: str = Field(default="", max_length=20000)
    cr: int = Field(ge=0)
    upd: int = Field(ge=0)


class EventIn(BaseModel):
    id: str = Field(**ID)
    title: str = Field(min_length=1, max_length=80)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(default="", pattern=r"^(\d{2}:\d{2})?$")
    type: Literal["study", "class", "exam", "deadline"]


class GoalIn(BaseModel):
    id: str = Field(**ID)
    t: str = Field(min_length=1, max_length=100)
    done: int = Field(default=0, ge=0, le=1)


class FocusIn(BaseModel):
    m: int = Field(ge=0, le=100000)
    n: int = Field(ge=0, le=100000)


class TimerIn(BaseModel):
    f: int = Field(ge=1, le=180)
    b: int = Field(ge=1, le=60)


class PrefsIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=30)
    theme: Optional[Literal["auto", "light", "dark"]] = None
    fmt: Optional[Literal["paragraph", "roadmap", "spider"]] = None
    timer: Optional[TimerIn] = None
    meet: Optional[str] = Field(default=None, max_length=300)
