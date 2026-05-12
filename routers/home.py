from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["home"])

templates = Jinja2Templates(directory="templates")

@router.get("/")
def homepage(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
