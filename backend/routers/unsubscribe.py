"""
Email unsubscribe functionality for legal compliance
"""
from fastapi import APIRouter, Request, Query, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.services.email_service import unsubscribe_email, check_unsubscribed
from backend.db import get_db
from bson import ObjectId
from datetime import datetime
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(request: Request, token: str = Query(...), email: str = Query(...)):
    """Display unsubscribe confirmation page"""
    try:
        # Verify the email and token combination is valid
        # In a production system, you'd store token->email mappings securely
        return templates.TemplateResponse("unsubscribe.html", {
            "request": request,
            "email": email,
            "token": token
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to process unsubscribe request")

@router.post("/unsubscribe", response_class=HTMLResponse)
async def process_unsubscribe(
    request: Request, 
    token: str = Form(...), 
    email: str = Form(...),
    reason: str = Form(None)
):
    """Process unsubscribe request"""
    try:
        # Store unsubscribe record in database
        db = await get_db()
        unsubscribe_id = str(ObjectId())
        
        unsubscribe_record = {
            "id": unsubscribe_id,
            "email": email,
            "unsubscribe_token": token,
            "unsubscribed_at": datetime.utcnow(),
            "reason": reason
        }
        
        await db.email_unsubscribes.insert_one(unsubscribe_record)
        
        return templates.TemplateResponse("unsubscribe_success.html", {
            "request": request,
            "email": email
        })
        
    except Exception as e:
        print(f"❌ Error processing unsubscribe: {e}")
        return templates.TemplateResponse("unsubscribe_error.html", {
            "request": request,
            "error": "Unable to process your unsubscribe request. Please try again later."
        })

@router.get("/unsubscribe/status")
async def check_unsubscribe_status(email: str = Query(...)):
    """API endpoint to check if an email is unsubscribed"""
    try:
        is_unsubscribed = await check_unsubscribed(email)
        return {"email": email, "unsubscribed": is_unsubscribed}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to check unsubscribe status")