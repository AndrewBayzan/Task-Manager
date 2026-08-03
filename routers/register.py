from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User
from schemas.reg_schema import UserCreate, UserResponse
from utils.security import hash_password

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get(
    "/register",
    response_class=HTMLResponse
)
def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "reg.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
        }
    )

@router.post(
    "/register"
)
def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    existing_user = db.query(User).filter(
        User.username == username
    ).first()

    if existing_user:
        return RedirectResponse(
            url="/auth/register?error=Username+already+exists",
            status_code=303,
        )

    existing_email = db.query(User).filter(
        User.email == email
    ).first()

    if existing_email:
        return RedirectResponse(
            url="/auth/register?error=Email+already+exists",
            status_code=303,
        )
    
    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(
        url="/auth/login?success=Account+created",
        status_code=303,
    )

