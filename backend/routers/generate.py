from datetime import datetime
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from bson import ObjectId
from backend.services.pdf_service import html_to_pdf_file
from backend.services.email_service import send_form_pdf
from backend.services.form_generator import generate_html_only, chat_with_gpt
from backend.deps import get_current_user, get_db
from backend.models.user import UserPublic

router = APIRouter(prefix="/api")


# ✅ פונקציית עזר אחידה לשימוש בדמו ובמשתמשים רשומים
def build_form_response_html(generated_html: str, for_demo: bool = False) -> str:
    escaped_html = generated_html.replace('"', '&quot;')

    save_form_html = ""
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
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200/80">
            {save_form_html}
            <form method="post" action="/api/download-pdf" target="_blank">
                <input type="hidden" name="html" value="{escaped_html}">
                <input type="hidden" name="title" value="Generated Form">
                <button type="submit" class="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg transition">
                    ⬇️ Download PDF
                </button>
            </form>
            <form hx-post="/api/send-form-to-other-email" hx-target="#send-feedback" hx-swap="innerHTML">
                <input type="hidden" name="html" value="{escaped_html}">
                <input type="email" name="email" required placeholder="Enter an email address to send to" class="w-full border border-slate-300 px-3 py-2 rounded-lg mb-2 focus:ring-2 focus:ring-blue-400">
                <button type="submit" data-loading-text="Sending..." class="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-lg transition">
                    📤 Send to Email
                </button>
                <div id="send-feedback" class="text-center text-sm mt-2 font-medium"></div>
            </form>
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
    html = await generate_html_only(prompt)
    return HTMLResponse(content=build_form_response_html(html, for_demo=True))


@router.post("/save-form", response_class=HTMLResponse)
async def save_form(
    title: str = Form(...),
    html: str = Form(...),
    user: UserPublic = Depends(get_current_user),
    db=Depends(get_db)
):
    doc = {
        "user_id": ObjectId(user.id),
        "title": title,
        "html": html,
        "created_at": datetime.utcnow(),
    }
    await db.forms.insert_one(doc)
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
        pdf_path = html_to_pdf_file(html)
        filename = f"{title.replace(' ', '_')}.pdf"
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return HTMLResponse(f"<p class='text-red-500'>❌ Download failed: {e}</p>", status_code=500)
