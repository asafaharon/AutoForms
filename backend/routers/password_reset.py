from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# Removed pydantic dependency - using str for email
from backend.db import get_db
from backend.services.auth_service import create_access_token, decode_token, hash_password
from backend.services.email_service import send_reset_email
from bson import ObjectId
import os

router = APIRouter(tags=["password_reset"])

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password(email: str = Form(...), db=Depends(get_db)):
    user = await db.users.find_one({"email": email})
    if not user:
        return HTMLResponse("This email does not exist in the system.", status_code=200)

    token = create_access_token({"sub": str(user["_id"])}, expires_minutes=15)
    link = f"http://127.0.0.1:8083/reset-password?token={token}"
    await send_reset_email(email, link)

    return HTMLResponse("You have received an email to update your password.", status_code=200)

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.post("/reset-password")
async def reset_password_post(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(400, "טוקן לא תקין")
    except Exception:
        raise HTTPException(400, "טוקן פג תוקף או לא תקין")

    hashed = hash_password(password)
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"hashed_password": hashed}})
    return HTMLResponse("✅ The password has been updated. You can log in with the new password.")
