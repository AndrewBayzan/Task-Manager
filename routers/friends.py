from pathlib import Path

from fastapi import APIRouter, Request, Cookie, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from routers.project import ensure_user

from db import get_db
from models import User, Friendship, FriendStatus


router = APIRouter(tags=["friends"], prefix="/friends")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


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

    return templates.TemplateResponse(request, "friends.html", {
        "request": request,
        "friends": friends,
        "incoming_requests": incoming_requests,
        "outgoing_requests": outgoing_requests,
        "username": user.username,
        "user": user
    })


@router.post("/friend_invite")
def friend_invite(
    request: Request,
    friend_username: str = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    target_user = db.query(User).filter(User.username == friend_username).first()
    if not target_user:
        return RedirectResponse(url="/friends?error=Пользователь%20не%20найден", status_code=303)

    if target_user.id == user.id:
        return RedirectResponse(url="/friends?error=Нельзя%20добавить%20самого%20себя%20в%20друзья", status_code=303)

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
        return RedirectResponse(url="/friends?error=Заявка%20уже%20отправлена", status_code=303)

    db.add(
        Friendship(
            user_id=user.id,
            friend_id=target_user.id,
            status=FriendStatus.pending,
        )
    )
    db.commit()

    return RedirectResponse(url="/friends?success=Заявка%20отправлена", status_code=303)


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
        return RedirectResponse(url="/friends?error=Заявка%20не%20найдена", status_code=303)

    if friendship.friend_id != user.id:
        return RedirectResponse(url="/friends?error=Это%20не%20ваша%20заявка", status_code=303)

    if friendship.status == FriendStatus.accepted:
        return RedirectResponse(url="/friends?error=Эта%20заявка%20уже%20принята", status_code=303)

    if friendship.status != FriendStatus.pending:
        return RedirectResponse(url="/friends?error=Эта%20заявка%20больше%20не%20активна", status_code=303)

    friendship.status = FriendStatus.accepted
    db.commit()

    return RedirectResponse(url="/friends?success=Заявка%20принята", status_code=303)


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

@router.post("/delete")
def delete_friend(
    friendship_id: int = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):

    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        return RedirectResponse(url="/friends?error=Дружба%20не%20найдена", status_code=303)

    if user.id not in (friendship.user_id, friendship.friend_id):
        return RedirectResponse(url="/friends?error=Это%20не%20ваша%20дружба", status_code=303)

    if friendship.status != FriendStatus.accepted:
        return RedirectResponse(url="/friends?error=Можно%20удалять%20только%20принятых%20друзей", status_code=303)

    db.delete(friendship)
    db.commit()

    return RedirectResponse(url="/friends?success=Друг%20удален", status_code=303)


