from fastapi import APIRouter, Request
from utils.templates import templates

router = APIRouter(tags=["home"])


@router.get("/")
def homepage(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})
