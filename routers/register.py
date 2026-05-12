from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="register", tags="register")

templates = Jinja2Templates(directory="reg.html")

