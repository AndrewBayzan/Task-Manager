from fastapi import APIRouter, Request, Cookie, Depends, Form, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from db import get_db
from models import (
    FriendStatus,
    Friendship,
    Project,
    RoleEnum,
    Task,
    TaskStatus,
    User,
    UserProject,
)
from utils.templates import templates

router = APIRouter(prefix="/projects", tags=["Projects page"])

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

    return templates.TemplateResponse(request, "project.html", {
        "request": request,
        "projects": all_projects,
        "username": user.username,
        "user_id": user.id,
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


@router.post("/{project_id}/delete")
def delete_project(
    project_id: int,
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project

    if project.owner_id != user.id:
        return RedirectResponse(
            url="/projects?error=Only+the+project+owner+can+delete+this+project",
            status_code=303,
        )

    db.delete(project)
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

    friendships = db.query(Friendship).filter(
        Friendship.status == FriendStatus.accepted,
        or_(
            Friendship.user_id == user.id,
            Friendship.friend_id == user.id,
        ),
    ).all()
    friend_ids = [
        friendship.friend_id if friendship.user_id == user.id else friendship.user_id
        for friendship in friendships
    ]
    project_member_ids = [
        membership.user_id for membership in project.user_projects
    ]
    project_member_ids.append(project.owner_id)
    friends = (
        db.query(User)
        .filter(
            User.id.in_(friend_ids),
            ~User.id.in_(project_member_ids),
        )
        .order_by(User.username)
        .all()
        if friend_ids
        else []
    )

    return templates.TemplateResponse(request, "management.html", {
        "request": request,
        "project": project,
        "friends": friends,
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

@router.post("/{project_id}/toggle_task_status")
def toggle_task_status(
    project_id: int,
    task_id: int = Form(...),
    done: int = Form(0),
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

    if not task:
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    task.status = TaskStatus.done if done == 1 else TaskStatus.in_progress
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
    friend_id: int = Form(...),
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

    new_user = db.query(User).filter(User.id == friend_id).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="User not found")

    already_member = db.query(UserProject).filter(
        UserProject.user_id == new_user.id,
        UserProject.project_id == project.id
    ).first()
    if new_user.id == project.owner_id or already_member:
        return RedirectResponse(
            url=f"/projects/{project_id}?error=User+is+already+a+project+member",
            status_code=303,
        )

    is_friend = db.query(Friendship).filter(
        Friendship.status == FriendStatus.accepted,
        or_(
            and_(
                Friendship.user_id == user.id,
                Friendship.friend_id == new_user.id,
            ),
            and_(
                Friendship.user_id == new_user.id,
                Friendship.friend_id == user.id,
            ),
        ),
    ).first()
    if not is_friend:
        raise HTTPException(
            status_code=403,
            detail="Only accepted friends can be added to a project",
        )

    user_project = UserProject(
        user_id=new_user.id,
        project_id=project.id,
        role=RoleEnum.member
    )
    db.add(user_project)
    db.commit()

    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@router.post("/{project_id}/remove_member")
def remove_member(
    project_id: int,
    member_id: int = Form(...),
    user_id: int | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    user = ensure_user(user_id, db)
    if isinstance(user, RedirectResponse):
        return user

    project = get_project_or_redirect(project_id, db)
    if isinstance(project, RedirectResponse):
        return project

    if project.owner_id != user.id:
        return RedirectResponse(
            url=f"/projects/{project_id}?error=Only+the+project+owner+can+remove+members",
            status_code=303,
        )

    if member_id == project.owner_id:
        return RedirectResponse(
            url=f"/projects/{project_id}?error=The+project+owner+cannot+be+removed",
            status_code=303,
        )

    membership = db.query(UserProject).filter(
        UserProject.project_id == project.id,
        UserProject.user_id == member_id,
    ).first()
    if not membership:
        return RedirectResponse(
            url=f"/projects/{project_id}?error=Project+member+not+found",
            status_code=303,
        )

    db.delete(membership)
    db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
