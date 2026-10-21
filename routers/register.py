from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Form
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User
from schemas.reg_schema import UserCreate
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
    try:
        user_data = UserCreate.model_validate(
            {
                "username": username,
                "email": email,
                "password": password,
            }
        )
    except ValidationError as error:
        field = error.errors()[0]["loc"][0]
        validation_messages = {
            "username": "Username must be 3-15 characters",
            "email": "Enter a valid email address",
            "password": "Password must be at least 6 characters long",
        }
        message = validation_messages.get(
            field,
            "Please check your registration details",
        )
        return RedirectResponse(
            url=f"/auth/register?{urlencode({'error': message})}",
            status_code=303,
        )

    existing_user = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_user:
        return RedirectResponse(
            url="/auth/register?error=Username+already+exists",
            status_code=303,
        )

    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_email:
        return RedirectResponse(
            url=f"/auth/register?{urlencode({'error': 'This email is already associated with an account'})}",
            status_code=303,
        )
    
    new_user = User(
        username=user_data.username,
        email=str(user_data.email),
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        if existing_email:
            return RedirectResponse(
                url=f"/auth/register?{urlencode({'error': 'This email is already associated with an account'})}",
                status_code=303,
            )
        raise

    db.refresh(new_user)

    return RedirectResponse(
        url="/auth/login?success=Account+created",
        status_code=303,
    )
