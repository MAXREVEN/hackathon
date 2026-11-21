"""Database tables. Every user-owned row has user_id, so one user never sees another's data."""
import time

from sqlalchemy import BigInteger, Boolean, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now_ms() -> int:
    return int(time.time() * 1000)


def _user_fk():
    return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(40))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    # preferences
    theme: Mapped[str] = mapped_column(String(8), default="auto")
    default_format: Mapped[str] = mapped_column(String(12), default="paragraph")
    timer_focus: Mapped[int] = mapped_column(Integer, default=25)
    timer_break: Mapped[int] = mapped_column(Integer, default=5)
    meet_link: Mapped[str] = mapped_column(String(300), default="")


class Subject(Base):
    __tablename__ = "subjects"
    user_id: Mapped[int] = _user_fk()
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer, default=0)


class Note(Base):
    __tablename__ = "notes"
    # Deleting a subject deletes its notes (done by the database itself).
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "subject_id"], ["subjects.user_id", "subjects.id"], ondelete="CASCADE"),
    )
    user_id: Mapped[int] = _user_fk()
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    subject_id: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[int] = mapped_column(BigInteger)


class Event(Base):
    __tablename__ = "events"
    user_id: Mapped[int] = _user_fk()
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    date: Mapped[str] = mapped_column(String(10))       # YYYY-MM-DD
    time: Mapped[str] = mapped_column(String(5), default="")
    type: Mapped[str] = mapped_column(String(10))


class Goal(Base):
    __tablename__ = "goals"
    user_id: Mapped[int] = _user_fk()
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    text: Mapped[str] = mapped_column(String(100))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)


class FocusDay(Base):
    __tablename__ = "focus_days"
    user_id: Mapped[int] = _user_fk()
    day: Mapped[str] = mapped_column(String(10), primary_key=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    blocks: Mapped[int] = mapped_column(Integer, default=0)


class Summary(Base):
    """One 'I AM LOST!' press = one row. content is JSON text."""
    __tablename__ = "summaries"
    user_id: Mapped[int] = _user_fk()
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    format: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    content: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True)
