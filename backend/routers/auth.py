from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Request,
    Form,
)
from fastapi.responses import RedirectResponse

from fastapi import APIRouter, Form, Depends, HTTPException, status

from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import EmailStr
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)
from backend.db import get_db
from backend.config import get_settings
from backend.utils import validate_email, validate_password, validate_username, ValidationError

print("🔔 auth router loaded")

router = APIRouter(tags=["auth"])  # ⬅️ הסרנו את prefix="/auth"

BASE_DIR = Path(__file__).resolve().parent.parent     # backend/
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------- GET /register ----------
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    print("📥 GET /register called")
    return templates.TemplateResponse(
        "register.html",
        {"request": request},
        media_type="text/html"
    )

@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("token")
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
        media_type="text/html",
    )

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email:    EmailStr = Form(...),
    password: str = Form(...),
    db:       AsyncIOMotorDatabase = Depends(get_db),
):
    # Input validation
    if not validate_username(username):
        return HTMLResponse(content="""
        <div class="bg-red-100 text-red-700 p-3 rounded text-center mb-3">
         Username must be 3-50 characters and contain only letters, numbers, underscore, and hyphen.
        </div>
        """, status_code=400)
    
    if not validate_email(str(email)):
        return HTMLResponse(content="""
        <div class="bg-red-100 text-red-700 p-3 rounded text-center mb-3">
         Please provide a valid email address.
        </div>
        """, status_code=400)
    
    if not validate_password(password):
        return HTMLResponse(content="""
        <div class="bg-red-100 text-red-700 p-3 rounded text-center mb-3">
         Password must be at least 8 characters with uppercase, lowercase, and number.
        </div>
        """, status_code=400)

    try:
        # Check for duplicate email
        if await db.users.find_one({"email": email}):
            html = """
            <div class="bg-red-100 text-red-700 p-3 rounded text-center mb-3">
             This email is already registered. Please try a different one.
            </div>
            """
            return HTMLResponse(content=html, status_code=400)

        # Determine if the user is an admin based on configured admin emails
        settings = get_settings()
        is_admin = str(email) in settings.admin_emails

        # Create user document
        doc = {
            "username":        username,
            "email":           email,
            "hashed_password": hash_password(password),
            "created_at":      datetime.utcnow(),
            "is_admin":        is_admin,  # Set admin status
        }
        result = await db.users.insert_one(doc)
    except Exception as e:
        return HTMLResponse(content="""
        <div class="bg-red-100 text-red-700 p-3 rounded text-center mb-3">
         Registration failed. Please try again.
        </div>
        """, status_code=500)

    token = create_access_token(data={"sub": str(result.inserted_id)})

    # Handle HTMX request
    if request.headers.get("Hx-Request"):
        html = """
        <div class='text-center mt-8'>
          <h2 class='text-xl font-semibold text-green-600'>✅ Registration successful!</h2>
          <p>You can now <a href='/login' class='underline text-blue-600'>log in</a>.</p>
        </div>
        """
        resp = HTMLResponse(html)
        resp.set_cookie("token", token, httponly=True, max_age=60*60, samesite="lax")
        return resp

    # Standard browser redirect
    resp = RedirectResponse(url="/home", status_code=303)
    resp.set_cookie("token", token, httponly=True, max_age=60*60, samesite="lax")
    return resp

# POST /login
@router.post("/login")
async def login(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["hashed_password"]):
        return HTMLResponse("""
        <div class="bg-red-100 text-red-700 p-3 rounded text-center">
        Incorrect email or password. Please try again.
        </div>
        """, status_code=401)

    token = create_access_token(data={"sub": str(user["_id"])})
    html = """
    <script>
      window.location.href = '/home';
    </script>
    """
    resp = HTMLResponse(content=html)
    resp.set_cookie("token", token, httponly=True, max_age=60*60, samesite="lax")
    return resp