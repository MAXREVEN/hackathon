"""Everything the signed-in student owns: subjects, notes, events, goals, focus time, prefs.

Design: the front keeps its data in memory and sends a whole collection whenever it changes
(PUT = "make the server match this list"). Simple and robust for small per-student data.
"""
import json
import re
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import MAX_ITEMS
from ..db import get_db
from ..deps import current_user
from ..models import Event, FocusDay, Goal, Note, Subject, Summary, User
from ..schemas import EventIn, FocusIn, GoalIn, NoteIn, PrefsIn, SubIn
from .auth import public_user

router = APIRouter(prefix="/api", tags=["data"])
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _sync(db: Session, model, user_id: int, rows: List[dict], key: str = "id") -> None:
    """Make the user's rows in `model` equal `rows`: update existing, insert new, delete missing."""
    if len(rows) > MAX_ITEMS:
        raise HTTPException(413, "Too many items")
    keys = [r[key] for r in rows]
    if len(set(keys)) != len(keys):
        raise HTTPException(422, "Duplicate ids in request")
    existing = {getattr(o, key): o for o in db.scalars(select(model).where(model.user_id == user_id))}
    for r in rows:
        obj = existing.pop(r[key], None)
        if obj is None:
            db.add(model(user_id=user_id, **r))
        else:
            for k, v in r.items():
                setattr(obj, k, v)
    for obj in existing.values():
        db.delete(obj)
    db.commit()


# ---- bootstrap: everything the front needs after login -------------------------------------
@router.get("/bootstrap")
def bootstrap(user: User = Depends(current_user), db: Session = Depends(get_db)):
    uid = user.id
    q = lambda model, *order: list(db.scalars(select(model).where(model.user_id == uid).order_by(*order)))
    return {
        "session": public_user(user),
        "name": user.name, "theme": user.theme, "fmt": user.default_format, "meet": user.meet_link,
        "timer": {"f": user.timer_focus, "b": user.timer_break},
        "subs": [{"id": s.id, "name": s.name} for s in q(Subject, Subject.position)],
        "notes": [{"id": n.id, "sid": n.subject_id, "title": n.title, "body": n.body,
                   "cr": n.created_at, "upd": n.updated_at} for n in q(Note, Note.created_at)],
        "events": [{"id": e.id, "title": e.title, "date": e.date, "time": e.time, "type": e.type}
                   for e in q(Event, Event.date)],
        "goals": [{"id": g.id, "t": g.text, "done": 1 if g.done else 0} for g in q(Goal, Goal.position)],
        "focus": {f.day: {"m": f.minutes, "n": f.blocks} for f in q(FocusDay, FocusDay.day)},
        "hist": [{"id": s.id, "t": s.title, "f": s.format, "d": s.created_at,
                  "c": json.loads(s.content), "s": s.is_sample}
                 for s in q(Summary, Summary.created_at.desc())],
    }


# ---- collections ---------------------------------------------------------------------------
@router.put("/subjects")
def put_subjects(body: List[SubIn], user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = [{"id": s.id, "name": s.name.strip(), "position": i} for i, s in enumerate(body)]
    _sync(db, Subject, user.id, rows)
    return {"ok": True, "count": len(rows)}


@router.put("/notes")
def put_notes(body: List[NoteIn], user: User = Depends(current_user), db: Session = Depends(get_db)):
    known = set(db.scalars(select(Subject.id).where(Subject.user_id == user.id)))
    if any(n.sid not in known for n in body):
        raise HTTPException(422, "A note refers to a subject that does not exist")
    rows = [{"id": n.id, "subject_id": n.sid, "title": n.title.strip(), "body": n.body,
             "created_at": n.cr, "updated_at": n.upd} for n in body]
    _sync(db, Note, user.id, rows)
    return {"ok": True, "count": len(rows)}


@router.put("/events")
def put_events(body: List[EventIn], user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = [{"id": e.id, "title": e.title.strip(), "date": e.date, "time": e.time, "type": e.type} for e in body]
    _sync(db, Event, user.id, rows)
    return {"ok": True, "count": len(rows)}


@router.put("/goals")
def put_goals(body: List[GoalIn], user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = [{"id": g.id, "text": g.t.strip(), "done": bool(g.done), "position": i} for i, g in enumerate(body)]
    _sync(db, Goal, user.id, rows)
    return {"ok": True, "count": len(rows)}


@router.put("/focus")
def put_focus(body: Dict[str, FocusIn], user: User = Depends(current_user), db: Session = Depends(get_db)):
    if any(not _DAY.match(day) for day in body):
        raise HTTPException(422, "Focus keys must be YYYY-MM-DD dates")
    rows = [{"day": day, "minutes": v.m, "blocks": v.n} for day, v in body.items()]
    _sync(db, FocusDay, user.id, rows, key="day")
    return {"ok": True, "count": len(rows)}


# ---- preferences + account -----------------------------------------------------------------
@router.patch("/me/prefs")
def patch_prefs(body: PrefsIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.name is not None:
        user.name = body.name.strip() or user.name
    if body.theme is not None:
        user.theme = body.theme
    if body.fmt is not None:
        user.default_format = body.fmt
    if body.timer is not None:
        user.timer_focus, user.timer_break = body.timer.f, body.timer.b
    if body.meet is not None:
        user.meet_link = body.meet.strip()
    db.commit()
    return {"ok": True}


@router.delete("/me")
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Delete children explicitly (notes first) so it works on any database, then the user.
    for model in (Note, Subject, Event, Goal, FocusDay, Summary):
        db.execute(delete(model).where(model.user_id == user.id))
    db.delete(user)
    db.commit()
    return {"ok": True}


# ---- history (rows are created by POST /api/lost) --------------------------------------------
@router.delete("/summaries/{summary_id}")
def delete_summary(summary_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(Summary).where(Summary.user_id == user.id, Summary.id == summary_id))
    db.commit()
    return {"ok": True}


@router.delete("/summaries")
def clear_summaries(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(Summary).where(Summary.user_id == user.id))
    db.commit()
    return {"ok": True}
