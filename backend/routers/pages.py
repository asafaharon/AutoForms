import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.deps import get_current_user, get_current_user_optional
from backend.models.user import UserPublic

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/generator", response_class=HTMLResponse)
async def generator_page(
    request: Request,
    user: UserPublic | None = Depends(get_current_user_optional)
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
    preview: bool = False,
    user = Depends(get_current_user)
):
    from backend.db import get_db
    
    # Get user's forms for selection
    user_forms = []
    selected_form = None
    
    if user:
        try:
            db = await get_db()
            # Get user ID from UserPublic object
            user_id_str = user.id  # This is already a string from the UserPublic model
            
            # Convert to ObjectId for database query
            from bson import ObjectId
            user_obj_id = ObjectId(user_id_str)
            
            # Query forms for this user
            forms_cursor = db.forms.find({"user_id": user_obj_id}).sort("created_at", -1)
            user_forms = await forms_cursor.to_list(length=50)
            
            # Convert MongoDB documents to proper format for template
            for form in user_forms:
                if "_id" in form and "id" not in form:
                    form["id"] = str(form["_id"])
            
            # If form_id specified, get that specific form
            if form_id:
                try:
                    form_obj_id = ObjectId(form_id)
                    selected_form = await db.forms.find_one({"_id": form_obj_id, "user_id": user_obj_id})
                    if selected_form and "_id" in selected_form:
                        selected_form["id"] = str(selected_form["_id"])
                except Exception as e:
                    print(f"Error finding specific form {form_id}: {e}")
                    selected_form = None
            elif user_forms:
                # Default to most recent form
                selected_form = user_forms[0]
                
        except Exception as e:
            print(f"Error loading user forms: {e}")
            import traceback
            traceback.print_exc()
    
    # Debug information
    print(f"DEBUG: User ID: {user.id if user else 'None'}")
    print(f"DEBUG: Found {len(user_forms)} forms")
    if user_forms:
        print(f"DEBUG: First form: {user_forms[0].get('title', 'No title')}")
    print(f"DEBUG: Selected form: {selected_form.get('title', 'No title') if selected_form else 'None'}")
    
    return templates.TemplateResponse(
        "share_form.html",
        {
            "request": request, 
            "form_id": form_id, 
            "preview": preview,
            "user": user,
            "user_forms": user_forms,
            "selected_form": selected_form
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user: UserPublic = Depends(get_current_user)
):
    # Redirect to home dashboard
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/home", status_code=302)
