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

@router.get("/submissions", response_class=HTMLResponse)
async def submissions_page(
    request: Request,
    user: UserPublic = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "submissions.html",
        {"request": request, "user": user}
    )

@router.get("/share-form", response_class=HTMLResponse)
async def share_form_page(
    request: Request,
    form_id: str = None,
    preview: bool = False
):
    return templates.TemplateResponse(
        "share_form.html",
        {"request": request, "form_id": form_id, "preview": preview}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user: UserPublic = Depends(get_current_user)
):
    # Redirect to submissions dashboard for now
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/submissions", status_code=302)
