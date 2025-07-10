from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.config import get_settings
from backend.routers import generate
from backend.routers.auth import router as auth_router
import os
from backend.routers import password_reset
from backend.routers import admin


from backend.deps import get_current_user
from fastapi import FastAPI, Request, Depends
from backend.routers import generate, forms, submit
from backend.routers import pages
settings = get_settings()
from backend.routers import creations  # ← ייבוא חדש

app = FastAPI(title="AutoForms API", version="0.1.0")

# טעינת תבניות
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
print("🔍 Template dir:", os.path.join(os.path.dirname(__file__), "templates"))

# הרשמת ראוטרים
app.include_router(admin.router, prefix="/admin", tags=["Admin"]) # 2. הוספת הראוטר
app.include_router(password_reset.router)

app.include_router(password_reset.router)

app.include_router(creations.router)

app.include_router(auth_router)  # בלי prefix
app.include_router(generate.router)

app.include_router(forms.router)
app.include_router(submit.submit_router)
app.include_router(pages.router)
for r in app.routes:
    print("📜", r.path, r.methods)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# דף בריאות
@app.get("/healthz", tags=["infra"])
async def health_check():
    return {"status": "ok"}

# דף בית
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/test-generator", response_class=HTMLResponse)
async def test_generator(request: Request):
    return templates.TemplateResponse("test-generator.html", {"request": request})

# דף בדיקה
@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("home.html",
                                      {"request": request, "user": user})
# ✅ הרצה מקומית (מותרת רק כשהקובץ נמצא בתוך backend)
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8080))  # fallback to 8080 for local dev
    uvicorn.run(app, host="0.0.0.0", port=port)

