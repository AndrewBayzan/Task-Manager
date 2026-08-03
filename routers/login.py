from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User, Project, UserProject, Task
from schemas.reg_schema import UserCreate, UserResponse
from utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Login"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
        }
    )

@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(
            url="/auth/login?error=Invalid+username+or+password",
            status_code=303,
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
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    owned_projects = db.query(Project).filter(Project.owner_id == user.id).all()
    member_projects = db.query(Project).join(UserProject).filter(UserProject.user_id == user.id).all()
    assigned_tasks = db.query(Task).filter(Task.assigned_user_id == user.id).all()

    project_map = {project.id: project for project in owned_projects + member_projects}
    all_projects = list(project_map.values())

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "request": request,
            "user": user,
            "owned_projects": owned_projects,
            "member_projects": member_projects,
            "assigned_tasks": assigned_tasks,
            "all_projects": all_projects
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