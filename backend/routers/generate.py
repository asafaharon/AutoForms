from datetime import datetime
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from bson import ObjectId
from backend.services.pdf_service import html_to_pdf_file, html_to_text_file
from backend.services.email_service import send_form_pdf
from backend.services.form_generator import generate_html_only, chat_with_gpt
from backend.services.websocket_manager import websocket_manager
from backend.deps import get_current_user, get_db
from backend.models.user import UserPublic
from backend.services.performance_monitor import perf_monitor
from backend.utils import validate_object_id

router = APIRouter(prefix="/api")


# ✅ פונקציית עזר אחידה לשימוש בדמו ובמשתמשים רשומים
def build_form_response_html(generated_html: str, for_demo: bool = False) -> str:
    escaped_html = generated_html.replace('"', '&quot;')

    save_form_html = ""
    email_form_html = ""
    
    if not for_demo:
        save_form_html = f"""
        <!-- Save Form -->
        <form hx-post="/api/save-form" hx-swap="none">
            <input type="hidden" name="html" value="{escaped_html}">
            <input type="text" name="title" placeholder="Give the form a name (e.g., November Registration)" required class="w-full border border-slate-300 px-3 py-2 rounded-lg mb-2 focus:ring-2 focus:ring-blue-400">
            <button type="submit" data-loading-text="Saving..." class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-lg transition">
                💾 Save to My Forms
            </button>
        </form>
        """
        
        email_form_html = f"""
        <form hx-post="/api/send-form-to-other-email" hx-target="#send-feedback" hx-swap="innerHTML">
            <input type="hidden" name="html" value="{escaped_html}">
            <input type="email" name="email" required placeholder="Enter an email address to send to" class="w-full border border-slate-300 px-3 py-2 rounded-lg mb-2 focus:ring-2 focus:ring-blue-400">
            <button type="submit" data-loading-text="Sending..." class="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-lg transition">
                📤 Send to Email
            </button>
            <div id="send-feedback" class="text-center text-sm mt-2 font-medium"></div>
        </form>
        """
    else:
        # For demo users, show a login prompt instead of the email form
        email_form_html = f"""
        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p class="text-blue-800 font-medium mb-2">📧 Want to send forms via email?</p>
            <a href="/register" class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition text-sm">
                Create Free Account
            </a>
        </div>
        """

    return f"""
    <section id="step-2-content" class="bg-white p-6 rounded-2xl shadow-lg border border-slate-200/80 space-y-6 fade-in">
        <div class="text-center">
            <span class="text-sm font-bold uppercase text-green-600 bg-green-100 px-3 py-1 rounded-full">Step 2</span>
            <h2 class="text-2xl font-bold mt-2">Your Result is Ready!</h2>
            <p class="text-slate-500 mt-1">Here you can see a preview and perform additional actions.</p>
        </div>
        <div class="border border-slate-200 rounded-lg overflow-hidden">
            <div class="bg-slate-100 px-4 py-2 border-b border-slate-200 text-xs font-semibold text-slate-500">Preview</div>
            <div id="result" class="p-4 bg-white max-h-[50vh] overflow-y-auto">{generated_html}</div>
        </div>
        <!-- Big Share Button -->
        <div class="pt-4 border-t border-slate-200/80">
            <a href="/share-form?preview=true" class="w-full bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 text-white font-bold py-4 px-6 rounded-xl transition-all duration-200 flex items-center justify-center text-lg shadow-lg hover:shadow-xl">
                🔗 Share This Form
                <span class="ml-2 text-sm opacity-90">(Get link, embed code, QR code)</span>
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
            {save_form_html}
            <form method="post" action="/api/download-pdf" target="_blank">
                <input type="hidden" name="html" value="{escaped_html}">
                <input type="hidden" name="title" value="Generated Content">
                <button type="submit" class="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg transition">
                    ⬇️ Download PDF
                </button>
            </form>
            {email_form_html}
        </div>
        <div class="pt-4 border-t border-slate-200/80">
            <form hx-post="/api/chat-about-html" hx-target="#result" hx-swap="innerHTML" class="space-y-2">
                <label class="block text-slate-600 font-semibold text-sm mb-1">Want to improve the form? Ask the AI:</label>
                <input type="hidden" name="html" value="{escaped_html}">
                <input name="question" type="text" required placeholder="e.g., Please add a phone number field" class="w-full p-2 border border-slate-300 rounded-lg text-sm">
                <button type="submit" data-loading-text="Thinking..." class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm transition">
                    Ask Question
                </button>
            </form>
        </div>
    </section>
    """


# ✅ למשתמש רשום
@router.post("/generate", response_class=HTMLResponse)
async def generate_html_preview(
    request: Request,
    prompt: str = Form(...),
    lang: str = Form(None)
):
    generated_html = await generate_html_only(prompt)
    if request.headers.get("Hx-Request"):
        return HTMLResponse(content=build_form_response_html(generated_html, for_demo=False))
    return JSONResponse({"html": generated_html})



@router.post("/demo-generate", response_class=HTMLResponse)
async def generate_demo_html(prompt: str = Form(...)):
    start_time = datetime.now()
    html = await generate_html_only(prompt)
    total_time = (datetime.now() - start_time).total_seconds()
    perf_monitor.record_generation_time("demo_total", total_time, cache_hit=False)
    return HTMLResponse(content=build_form_response_html(html, for_demo=True))


@router.post("/save-form", response_class=HTMLResponse)
async def save_form(
    title: str = Form(...),
    html: str = Form(...),
    user: UserPublic = Depends(get_current_user),
    db=Depends(get_db)
):
    user_obj_id = validate_object_id(user.id)
    
    # First save the form to get the ID
    doc = {
        "user_id": user_obj_id,
        "title": title,
        "html": html,
        "created_at": datetime.utcnow(),
    }
    result = await db.forms.insert_one(doc)
    form_id = str(result.inserted_id)
    
    # Now update the HTML to include the correct submission URL
    import re
    
    # Add form submission functionality to the HTML
    updated_html = html
    
    # If form doesn't have an action attribute, add one
    if 'action=' not in updated_html:
        # Find form tag and add action attribute
        form_pattern = r'<form([^>]*?)>'
        def add_action(match):
            attrs = match.group(1)
            return f'<form{attrs} action="/api/submissions/submit/{form_id}" method="POST">'
        updated_html = re.sub(form_pattern, add_action, updated_html, flags=re.IGNORECASE)
    else:
        # Replace existing action with correct one
        action_pattern = r'action=["\'][^"\']*["\']'
        updated_html = re.sub(action_pattern, f'action="/api/submissions/submit/{form_id}"', updated_html, flags=re.IGNORECASE)
    
    # Ensure method is POST
    if 'method=' not in updated_html:
        updated_html = updated_html.replace('<form', '<form method="POST"', 1)
    else:
        method_pattern = r'method=["\'][^"\']*["\']'
        updated_html = re.sub(method_pattern, 'method="POST"', updated_html, flags=re.IGNORECASE)
    
    # Add hidden form_id field if not present
    if f'name="form_id"' not in updated_html:
        # Find the first form tag and add the hidden input after it
        form_start_pattern = r'(<form[^>]*?>)'
        replacement = f'\\1\n    <input type="hidden" name="form_id" value="{form_id}">'
        updated_html = re.sub(form_start_pattern, replacement, updated_html, flags=re.IGNORECASE)
    
    # Update the saved form with the corrected HTML
    await db.forms.update_one(
        {"_id": result.inserted_id},
        {"$set": {"html": updated_html}}
    )
    
    # Send WebSocket notification
    await websocket_manager.notify_form_generated(user.id, {
        "form_id": form_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat()
    })
    
    return HTMLResponse(status_code=200)


@router.post("/send-form-pdf", response_class=HTMLResponse)
async def send_form_pdf_now(
    html: str = Form(...),
    title: str = Form("Generated Form"),
    user: UserPublic = Depends(get_current_user)
):
    try:
        pdf_path = html_to_pdf_file(html)
        await send_form_pdf(user.email, pdf_path, title)
        return HTMLResponse("✅ The form was sent to your email as a PDF.")
    except Exception as e:
        return HTMLResponse(f"❌ Failed to send email: {e}", status_code=500)


@router.get("/performance-stats")
async def get_performance_stats():
    """Get performance statistics for monitoring"""
    return JSONResponse(perf_monitor.get_stats())


@router.post("/chat-about-html", response_class=HTMLResponse)
async def chat_about_html(
    html: str = Form(...),
    question: str = Form(...)
):
    try:
        reply = await chat_with_gpt(html, question)
        return HTMLResponse(content=reply)
    except Exception as e:
        return HTMLResponse(content=f"<p class='text-red-500'>❌ Chat failed: {e}</p>", status_code=500)


@router.post("/send-form-to-other-email", response_class=HTMLResponse)
async def send_form_to_other_email(
    html: str = Form(...),
    email: str = Form(...),
    user: UserPublic = Depends(get_current_user)
):
    title = "טופס שנוצר עבורך מ-AutoForms"
    try:
        pdf_path = html_to_pdf_file(html)
        await send_form_pdf(email, pdf_path, title)
        return HTMLResponse(status_code=200)
    except Exception as e:
        return HTMLResponse(f"<p class='text-red-500 font-medium'>❌ נכשל: {e}</p>", status_code=500)


@router.post("/download-pdf")
async def download_pdf(html: str = Form(...), title: str = Form("generated_form")):
    try:
        # Try PDF first
        pdf_path = html_to_pdf_file(html)
        filename = f"{title.replace(' ', '_')}.pdf"
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ImportError as e:
        # WeasyPrint not available, fallback to text file
        try:
            text_path = html_to_text_file(html, title)
            filename = f"{title.replace(' ', '_')}.txt"
            return FileResponse(
                path=text_path,
                filename=filename,
                media_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as fallback_error:
            return HTMLResponse(f"<p class='text-red-500'>❌ Download failed. PDF requires WeasyPrint installation: {e}<br>Text fallback also failed: {fallback_error}</p>", status_code=500)
    except Exception as e:
        return HTMLResponse(f"<p class='text-red-500'>❌ Download failed: {e}</p>", status_code=500)

@router.post("/download-text")
async def download_text(html: str = Form(...), title: str = Form("generated_content")):
    """Alternative download endpoint for text files"""
    try:
        text_path = html_to_text_file(html, title)
        filename = f"{title.replace(' ', '_')}.txt"
        return FileResponse(
            path=text_path,
            filename=filename,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return HTMLResponse(f"<p class='text-red-500'>❌ Text download failed: {e}</p>", status_code=500)
