from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from db import SessionLocal
from models import FriendStatus, Friendship, User


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
        incoming_friend_requests = 0
        if current_user:
            incoming_friend_requests = (
                db.query(Friendship)
                .filter(
                    Friendship.friend_id == current_user.id,
                    Friendship.status == FriendStatus.pending,
                )
                .count()
            )

    return {
        "current_user": current_user,
        "incoming_friend_requests": incoming_friend_requests,
    }


templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates"),
    context_processors=[add_current_user],
)
