# backend/routers/submit.py
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.db import get_db

submit_router = APIRouter(tags=["submit"])

@submit_router.get("/submit/thanks", response_class=HTMLResponse)
async def submit_thanks():
    return HTMLResponse("""
        <h2 style='font-family:Arial;text-align:center;margin-top:50px'>
           ✅ Thank you! The form was successfully submitted.
        </h2>
    """)

@submit_router.post("/submit/{form_id}", status_code=status.HTTP_303_SEE_OTHER)
async def submit_form(
    form_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
):

    form_data = await request.form()


    await db.submissions.insert_one({
        "form_id": ObjectId(form_id),
        "data": dict(form_data),
        "submitted_at": datetime.utcnow(),
    })

    return RedirectResponse(url="/submit/thanks", status_code=status.HTTP_303_SEE_OTHER)
