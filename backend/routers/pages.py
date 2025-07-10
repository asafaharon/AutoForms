import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.deps import get_current_user
from backend.models.user import UserPublic

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/generator", response_class=HTMLResponse)
async def generator_page(
    request: Request,
    user: UserPublic = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "test-generator.html",
        {"request": request, "user": user}
    )

@router.get("/demo-generator", response_class=HTMLResponse)
async def demo_generator_page(request: Request):
    return templates.TemplateResponse("demo-generator.html", {"request": request})
