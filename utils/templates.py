from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from db import SessionLocal
from models import User


def add_current_user(request: Request):
    raw_user_id = request.cookies.get("user_id")
    if not raw_user_id:
        return {"current_user": None}

    try:
        user_id = int(raw_user_id)
    except ValueError:
        return {"current_user": None}

    with SessionLocal() as db:
        current_user = db.get(User, user_id)

    return {"current_user": current_user}


templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates"),
    context_processors=[add_current_user],
)
