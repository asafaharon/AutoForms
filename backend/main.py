from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.config import get_settings
from backend.routers import generate, forms, submit, pages, creations, password_reset, admin
from backend.routers.auth import router as auth_router
from backend.deps import get_current_user
from backend.db import close_db_connection
import os

settings = get_settings()

app = FastAPI(title="AutoForms API", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    print(f"🚀 AutoForms API starting up in {settings.environment} mode...")
    print(f"🌐 Base URL: {settings.base_url}")
    try:
        from backend.services.db_indexes import create_indexes
        await create_indexes()
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create database indexes: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    print("🔄 AutoForms API shutting down...")
    await close_db_connection()

# טעינת תבניות
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
print("🔍 Template dir:", os.path.join(os.path.dirname(__file__), "templates"))

# הרשמת ראוטרים
app.include_router(admin.router, prefix="/admin", tags=["Admin"]) # 2. הוספת הראוטר
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

    uvicorn.run(app, host="127.0.0.1", port=8083)
