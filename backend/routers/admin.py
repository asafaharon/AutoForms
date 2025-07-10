from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

# Correct imports for dependencies and models
from backend.deps import get_current_admin_user
from backend.db import get_db
from backend.models.user import UserPublic

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: UserPublic = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_db)  # Inject DB dependency
):
    """
    Displays the admin dashboard with system statistics.
    """
    # Import templates here to avoid circular dependency
    from backend.main import templates

    # Fetch data from the database
    total_users = await db.users.count_documents({})
    # Assuming 'forms' and 'submissions' collections exist based on other routers
    total_forms = await db.forms.count_documents({})
    total_submissions = await db.submissions.count_documents({})

    context = {
        "request": request,
        "user": user,
        "total_users": total_users,
        "total_forms": total_forms,
        "total_submissions": total_submissions
    }

    return templates.TemplateResponse("admin_dashboard.html", context)