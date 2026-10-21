from urllib.parse import urlencode

from fastapi import APIRouter, Request, Cookie, Depends, Form, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from routers.project import ensure_user

from db import get_db
from models import User, Friendship, FriendStatus
from utils.templates import templates


router = APIRouter(tags=["friends"], prefix="/friends")

@router.get("/")
def get_friends(
    request: Request,
    search: str | None = None,
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
    search_results = []

    search = search.strip() if search else ""
    if search:
        connected_user_ids = (
            db.query(Friendship.user_id.label("user_id"))
            .filter(Friendship.friend_id == user.id)
            .union(
                db.query(Friendship.friend_id.label("user_id"))
                .filter(Friendship.user_id == user.id)
            )
        )
        search_results = (
            db.query(User)
            .filter(
                User.id != user.id,
                User.username.ilike(f"%{search}%"),
                ~User.id.in_(connected_user_ids),
            )
            .order_by(User.username)
            .limit(20)
            .all()
        )

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
        "search": search,
        "search_results": search_results,
        "username": user.username,
        "user": user
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
    if not target_user:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'User not found'})}",
            status_code=303,
        )

    if target_user.id == user.id:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'You cannot send a friend request to yourself'})}",
            status_code=303,
        )

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
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'A friend request or friendship already exists'})}",
            status_code=303,
        )

    db.add(
        Friendship(
            user_id=user.id,
            friend_id=target_user.id,
            status=FriendStatus.pending,
        )
    )
    db.commit()

    return RedirectResponse(
        url=f"/friends?{urlencode({'success': 'Friend request sent'})}",
        status_code=303,
    )


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
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'Friend request not found'})}",
            status_code=303,
        )

    if friendship.friend_id != user.id:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'You cannot accept this friend request'})}",
            status_code=303,
        )

    if friendship.status == FriendStatus.accepted:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'This friend request has already been accepted'})}",
            status_code=303,
        )

    if friendship.status != FriendStatus.pending:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'This friend request is no longer active'})}",
            status_code=303,
        )

    friendship.status = FriendStatus.accepted
    db.commit()

    return RedirectResponse(
        url=f"/friends?{urlencode({'success': 'Friend request accepted'})}",
        status_code=303,
    )


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
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'Friendship not found'})}",
            status_code=303,
        )

    if user.id not in (friendship.user_id, friendship.friend_id):
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'You cannot remove this friend'})}",
            status_code=303,
        )

    if friendship.status != FriendStatus.accepted:
        return RedirectResponse(
            url=f"/friends?{urlencode({'error': 'Only accepted friends can be removed'})}",
            status_code=303,
        )

    db.delete(friendship)
    db.commit()

    return RedirectResponse(
        url=f"/friends?{urlencode({'success': 'Friend removed'})}",
        status_code=303,
    )
