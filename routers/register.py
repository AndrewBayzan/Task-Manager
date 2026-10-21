from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User
from utils.security import hash_password
from utils.templates import templates

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_email = db.query(User).filter(
            User.email == email
        ).first()
        if existing_email:
            return RedirectResponse(
                url="/auth/register?error=Email+already+exists",
                status_code=303,
            )
        raise

    db.refresh(new_user)

    return RedirectResponse(
        url="/auth/login?success=Account+created",
        status_code=303,
    )
