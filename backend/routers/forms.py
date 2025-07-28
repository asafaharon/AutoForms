from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Form, Request, BackgroundTasks, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from tempfile import NamedTemporaryFile
import atexit

from backend.config import get_settings, Settings
from backend.db import get_db
from backend.deps import get_current_user
from backend.models.user import UserPublic
from backend.services.email_service import send_form_link, send_form_pdf
from backend.services.pdf_service import html_to_pdf_file
from backend.utils import validate_object_id

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
router = APIRouter(prefix="/api", tags=["forms"])

# Track temporary files for cleanup
_temp_files = []

def cleanup_temp_files():
    """Clean up temporary files at application shutdown."""
    for file_path in _temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
    _temp_files.clear()

# Register cleanup function
atexit.register(cleanup_temp_files)

@router.get("/forms")
async def list_forms(user: UserPublic = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    user_obj_id = validate_object_id(user.id)
    cursor = db.forms.find({"user_id": user_obj_id}, {"html": 0, "schema": 0})
    forms = await cursor.to_list(length=None)
    for f in forms: f["id"] = str(f.pop("_id"))
    return forms

@router.post("/forms/{fid}/email", status_code=status.HTTP_202_ACCEPTED)
async def email_form(
    fid: str,
    tasks: BackgroundTasks,
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    doc = await db.forms.find_one(
        {"_id": fid_obj, "user_id": user_obj_id},
        {"title": 1},
    )
    if not doc:
        raise HTTPException(404, "Form not found")

    link = f"{settings.base_url}/api/forms/public/{fid}"
    tasks.add_task(send_form_link, user.email, link, doc["title"])
    return {"msg": "The email is on its way 🎉"}

@router.get("/forms/public/{fid}", response_class=HTMLResponse)
async def get_form_public(fid: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    fid_obj = validate_object_id(fid)
    doc = await db.forms.find_one({"_id": fid_obj}, {"html": 1})
    if not doc:
        raise HTTPException(404, "Form not found")
    return HTMLResponse(doc["html"])

@router.get("/forms/{fid}", response_class=HTMLResponse)
async def view_form(
    fid: str,
    request: Request,
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    doc = await db.forms.find_one({"_id": fid_obj, "user_id": user_obj_id})
    if not doc:
        raise HTTPException(404)
    doc["_id"] = str(doc["_id"])
    return templates.TemplateResponse("form_view.html", {"request": request, "form": doc})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user_obj_id = validate_object_id(user.id)
    cursor = db.forms.find({"user_id": user_obj_id}, {"title": 1, "created_at": 1})
    forms = await cursor.to_list(100)
    for f in forms:
        f["_id"] = str(f["_id"])
    return templates.TemplateResponse("dashboard.html", {"request": request, "forms": forms})

@router.get("/forms/{fid}/download")
async def download_form(
    fid: str,
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    doc = await db.forms.find_one(
        {"_id": fid_obj, "user_id": user_obj_id},
        {"html": 1, "title": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Generate PDF from HTML
    try:
        pdf_path = html_to_pdf_file(doc["html"])
        # Track file for cleanup
        _temp_files.append(pdf_path)
        filename = f"{doc['title'].replace(' ', '_')}.pdf"
        return FileResponse(pdf_path, filename=filename, media_type="application/pdf")
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Fallback to HTML if PDF generation fails
        with NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
            tmp.write(doc["html"])
            tmp.flush()
            # Track file for cleanup
            _temp_files.append(tmp.name)
            filename = f"{doc['title'].replace(' ', '_')}.html"
            return FileResponse(tmp.name, filename=filename, media_type="text/html")

@router.delete("/forms/{fid}", response_class=PlainTextResponse)
async def delete_form(fid: str, user: UserPublic = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    res = await db.forms.delete_one({"_id": fid_obj, "user_id": user_obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    return "✅ Successfully deleted"

@router.post("/forms/{fid}/email-pdf", status_code=status.HTTP_202_ACCEPTED)
async def email_form_pdf(
    fid: str,
    tasks: BackgroundTasks,
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    doc = await db.forms.find_one({"_id": fid_obj, "user_id": user_obj_id})
    if not doc:
        raise HTTPException(404, "Form not found")

    title = doc.get("title", "Untitled form")
    html = doc.get("html", "")
    if not html:
        raise HTTPException(400, "The form does not contain any HTML content.")

    pdf_path = html_to_pdf_file(html)
    tasks.add_task(send_form_pdf, user.email, pdf_path, title)
    # Note: The temporary PDF file is not deleted here, consider a cleanup strategy.
    return {"msg": "PDF is on its way to your email ✉️"}

@router.post("/forms/{fid}/chat", response_class=HTMLResponse)
async def chat_with_form(
    fid: str,
    question: str = Form(...),
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    doc = await db.forms.find_one({"_id": fid_obj, "user_id": user_obj_id})
    if not doc:
        return HTMLResponse("Form not found", status_code=404)

    html = doc.get("html", "")
    from backend.services.form_generator import chat_with_gpt
    reply = await chat_with_gpt(html, question)

    await db.forms.update_one(
        {"_id": fid_obj, "user_id": user_obj_id},
        {"$set": {"html": reply}}
    )
    return HTMLResponse("<p class='text-green-700'>Form updated via GPT ✅</p>" + reply)

@router.post("/forms/{fid}/update", response_class=HTMLResponse)
async def update_form_html(
    fid: str,
    html: str = Form(...),
    user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    fid_obj = validate_object_id(fid)
    user_obj_id = validate_object_id(user.id)
    result = await db.forms.update_one(
        {"_id": fid_obj, "user_id": user_obj_id},
        {"$set": {"html": html}}
    )
    if result.modified_count == 1:
        return HTMLResponse("<p class='text-green-700'>✅ Form updated successfully.</p>")
    return HTMLResponse("<p class='text-yellow-700'>No changes were made.</p>")

@router.get("/forms/{fid}/confirm-delete", response_class=HTMLResponse)
async def confirm_delete(fid: str):
    return HTMLResponse(f"""
    <div class='bg-white rounded-lg p-6 w-80 space-y-4'>
      <h2 class='text-lg font-semibold text-red-700'>Delete form?</h2>
      <p class='text-sm text-gray-600'>This action cannot be undone.</p>
      <div class='flex gap-2'>
        <button hx-delete='/api/forms/{fid}'
                hx-target='#modal' hx-swap='innerHTML'
                class='bg-red-600 text-white px-4 py-2 rounded'>Delete</button>
        <button onclick='closeModal()'
                class='bg-gray-300 px-4 py-2 rounded'>Cancel</button>
      </div>
    </div>""")