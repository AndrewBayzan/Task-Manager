from fastapi import APIRouter, Request, Cookie, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse

from db import get_db
from models import User, Project, UserProject, RoleEnum, Task

router = APIRouter(prefix="/projects", tags=["Projects page"])
templates = Jinja2Templates(directory="templates")

def ensure_user(user_id: int | None, db: Session):
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    return user


def get_project_or_redirect(project_id: int, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    return project


def has_project_access(user_id: int, project: Project, db: Session) -> bool:
    if project.owner_id == user_id:
        return True
    access = db.query(UserProject).filter(
        UserProject.project_id == project.id,
        UserProject.user_id == user_id
    ).first()
    return bool(access)

@router.get("/")
def projects(
    request: Request,
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user
    
    owned_projects = db.query(Project).filter(Project.owner_id == user_id).all()

    member_projects = db.query(Project).join(UserProject).filter(UserProject.user_id == user_id).all()

    all_projects = list(set(owned_projects + member_projects))

    return templates.TemplateResponse("project.html", {
        "request": request,
        "projects": all_projects,
        "username" : user.username
    })

@router.post("/create_project")
def create_project(
    project_name: str = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = Project(project_name=project_name, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)

    user_project = UserProject(user_id=user_id, project_id=project.id, role=RoleEnum.admin)
    db.add(user_project)
    db.commit()
    
    return RedirectResponse(url="/projects", status_code=303)

@router.get("/{project_id}")
def project_management(
    request: Request,
    project_id: int,
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project

    if not has_project_access(user.id, project, db):
        return RedirectResponse(url="/projects", status_code=303)

    return templates.TemplateResponse("management.html", {
        "request": request,
        "project": project
    })

@router.post("/{project_id}/add_task")
def add_task(
    project_id: int,
    task_title: str = Form(...),
    assigned_user: str| None = Form(None),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    assigned = None
    if assigned_user:
        assigned = db.query(User).filter(User.username == assigned_user).first()

    task = Task(
        title=task_title, 
        project_id=project_id,
        assigned_user_id=assigned.id if assigned else None)
    db.add(task)
    db.commit()
    db.refresh(task)


    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@router.post("/{project_id}/delete_task")
def del_task(
    project_id: int,
    task_id: int = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project

    if not has_project_access(user.id, project, db):
        return RedirectResponse(url="/projects", status_code=303)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    
    if task:
        db.delete(task)
        db.commit()

    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@router.post("/{project_id}/update_task")
def update_task(
    project_id: int,
    task_title: str = Form(...),
    task_id: int = Form(...),
    assigned_user: str | None = Form(None),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
        ).first()
    
    if not task:
        return RedirectResponse(url="/projects", status_code=303)
    
    access = db.query(UserProject).filter(
        UserProject.project_id == project_id,
        UserProject.user_id == user_id
    ).first()

    if project.owner_id != user_id and not access:
        return RedirectResponse(url="/projects", status_code=303)



    task.title = task_title
    if assigned_user:
        assigned = db.query(User).filter(User.username == assigned_user).first()
        task.assigned_user_id = assigned.id if assigned else None
    else:
        task.assigned_user_id = None


    db.commit()
    
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@router.post("/change_pname")
def change_pname(
    project_id: int,
    user_id: int | None = Cookie(default=None),    
    new_name: str = Form(...),
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user
    
    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project
    
    if not has_project_access(user.id, project, db):
        return RedirectResponse(url="/projects", status_code=303)
    
    project.project_name = new_name
    db.commit()
    
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@router.post("/{project_id}/add_user")
def add_user(
    project_id: int,
    username: str = Form(...),
    user_id: int | None = Cookie(default=None),  
    db: Session = Depends(get_db)
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project
    
    if not has_project_access(user.id, project, db):
        return RedirectResponse(url="/projects", status_code=303)

    new_user = db.query(User).filter(User.username == username).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    already_member = db.query(UserProject).filter(
        UserProject.user_id == new_user.id,
        UserProject.project_id == project.id
    ).first()
    if already_member:
        raise HTTPException(status_code=400, detail="Пользователь уже добавлен в проект")

    user_project = UserProject(
        user_id=new_user.id,
        project_id=project.id,
        role=RoleEnum.member
    )
    db.add(user_project)
    db.commit()

    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
