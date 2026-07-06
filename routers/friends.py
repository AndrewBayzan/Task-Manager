from fastapi import APIRouter, Request, Cookie, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from routers.project import ensure_user

from db import get_db
from models import User, Friendship, FriendStatus


router = APIRouter(tags=["friends"], prefix="/friends")

templates = Jinja2Templates(directory="templates")


@router.get("/")
def get_friends(
    request: Request,
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.user_id == user.id,
                Friendship.friend_id == user.id,
            )
        )
        .all()
    )

    friends = []
    incoming_requests = []
    outgoing_requests = []

    for friendship in friendships:
        if friendship.status == FriendStatus.accepted:
            if friendship.user_id == user.id:
                friends.append({"friendship": friendship, "user": friendship.friend})
            else:
                friends.append({"friendship": friendship, "user": friendship.user})
        elif friendship.status == FriendStatus.pending:
            if friendship.friend_id == user.id:
                incoming_requests.append({"friendship": friendship, "user": friendship.user})
            elif friendship.user_id == user.id:
                outgoing_requests.append({"friendship": friendship, "user": friendship.friend})

    return templates.TemplateResponse("friends.html", {
        "request": request,
        "friends": friends,
        "incoming_requests": incoming_requests,
        "outgoing_requests": outgoing_requests,
        "username": user.username,
    })


@router.post("/friend_invite")
def friend_invite(
    friend_username: str = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    target_user = db.query(User).filter(User.username == friend_username).first()
    if not target_user or target_user.id == user.id:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(Friendship)
        .filter(
            or_(
                and_(Friendship.user_id == user.id, Friendship.friend_id == target_user.id),
                and_(Friendship.user_id == target_user.id, Friendship.friend_id == user.id),
            )
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Request already exists")

    db.add(
        Friendship(
            user_id=user.id,
            friend_id=target_user.id,
            status=FriendStatus.pending,
        )
    )
    db.commit()

    return RedirectResponse(url="/friends", status_code=303)


@router.post("/accept")
def accept_friend(
    friendship_id: int = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friendship.friend_id != user.id or friendship.status != FriendStatus.pending:
        raise HTTPException(status_code=403, detail="Access denied")

    friendship.status = FriendStatus.accepted
    db.commit()

    return RedirectResponse(url="/friends", status_code=303)


@router.post("/reject")
def reject_friend(
    friendship_id: int = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friendship.friend_id != user.id or friendship.status != FriendStatus.pending:
        raise HTTPException(status_code=403, detail="Access denied")

    friendship.status = FriendStatus.rejected
    db.commit()

    return RedirectResponse(url="/friends", status_code=303)
