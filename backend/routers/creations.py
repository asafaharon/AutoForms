from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.db import get_db
from backend.deps import get_current_user
from backend.services.pdf_service import html_to_pdf_file
from backend.services.email_service import send_form_pdf
from bson import ObjectId
import os

router = APIRouter(prefix="/api", tags=["creations"])

@router.post("/creations/{cid}/email-pdf")
async def send_creation_pdf(
    cid: str,
    tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db.creations.find_one({"_id": ObjectId(cid), "user_id": user["_id"]})
    if not doc:
        raise HTTPException(404)

    pdf_path = html_to_pdf_file(doc["html"])

    async def task():
        try:
            await send_form_pdf(user["email"], pdf_path, doc["prompt"][:50])
        finally:
            try:
                os.remove(pdf_path)
            except FileNotFoundError:
                pass

    tasks.add_task(task)
    return {"msg": "PDF נשלח למייל 🎉"}
