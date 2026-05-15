from fastapi import APIRouter, Depends, HTTPException, Request, Form, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User
from schemas.reg_schema import UserCreate, UserResponse
from utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Login"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )
    
    response = RedirectResponse(
        url="/auth/profile",
        status_code=303
    )
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/profile", response_class=HTMLResponse)
def profile(
    request: Request,
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user
        }
    )

@router.get("/logout")
def logout():
    response = RedirectResponse(
        url="/auth/login",
        status_code=303
    )

    response.delete_cookie("user_id")

    return response