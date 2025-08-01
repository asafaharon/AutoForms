from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from backend.config import get_settings
from backend.routers import generate, forms, submit, pages, creations, password_reset, admin, websocket, submissions, unsubscribe
from backend.routers import templates as template_router
from backend.routers.auth import router as auth_router
from backend.deps import get_current_user
from backend.db import close_db_connection
from backend.services.security import validate_production_security, get_security_headers
from backend.services.error_handler import handle_404_error, handle_500_error, handle_general_error
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import os

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 AutoForms API starting up...")
    
    try:
        # Test database connection first
        from backend.db import get_db
        db = await get_db()
        await db.command('ping')
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        if settings.app_env == "production":
            raise SystemExit(1)
    
    # Validate production security
    try:
        security_errors = validate_production_security()
        if security_errors and settings.app_env == "production":
            print("❌ Security validation failed in production mode")
            for error in security_errors:
                print(f"   {error}")
    except Exception as e:
        print(f"⚠️ Security validation error: {e}")
    
    try:
        from backend.services.db_indexes import create_indexes
        await create_indexes()
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create database indexes: {e}")
    
    print(f"✅ AutoForms API ready on {settings.host}:{settings.port}")
    yield
    
    # Shutdown
    print("🔄 AutoForms API shutting down...")
    try:
        await close_db_connection()
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")

app = FastAPI(title="AutoForms API", version="0.1.0", lifespan=lifespan)

# Load templates and static files
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
print("🔍 Template dir:", os.path.join(os.path.dirname(__file__), "templates"))

# Static files configuration
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print("📁 Static files mounted at /static")
else:
    print("⚠️ Static directory not found, skipping static file serving")

# Register routers
app.include_router(admin.router, prefix="/admin", tags=["Admin"]) # 2. Add the router
app.include_router(password_reset.router)

app.include_router(creations.router)

app.include_router(auth_router)  # Without prefix
app.include_router(generate.router)

app.include_router(forms.router)
app.include_router(submit.submit_router)
app.include_router(pages.router)
app.include_router(websocket.router)
app.include_router(template_router.router)
app.include_router(submissions.router)
app.include_router(unsubscribe.router)
for r in app.routes:
    # WebSocket routes don't have methods attribute
    methods = getattr(r, 'methods', {'WebSocket'})
    print("📜", r.path, methods)

# Security Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Add security headers
    headers = get_security_headers()
    for header, value in headers.items():
        response.headers[header] = value
    
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Error Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 404:
        return handle_404_error(request, exc)
    return handle_general_error(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return handle_general_error(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return handle_500_error(request, exc)

# Health Check Endpoints
@app.get("/health", tags=["infra"])
@app.get("/healthz", tags=["infra"])
async def health_check():
    """Basic health check for load balancers"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/ready", tags=["infra"])
async def readiness_check():
    """Comprehensive readiness check for production"""
    import time
    
    start_time = time.time()
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        from backend.db import get_db
        db = await get_db()
        await db.command("ping")
        checks["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        checks["status"] = "unhealthy"
    
    # Environment configuration check
    try:
        settings = get_settings()
        config_status = "healthy"
        if settings.openai_key == "sk-test-key":
            config_status = "degraded"
        checks["checks"]["configuration"] = {
            "status": config_status, 
            "environment": settings.app_env
        }
    except Exception as e:
        checks["checks"]["configuration"] = {"status": "unhealthy", "message": str(e)}
        checks["status"] = "unhealthy"
    
    # OpenAI API check (optional, non-blocking)
    try:
        import openai
        openai.api_key = settings.openai_key
        checks["checks"]["openai"] = {"status": "available"}
    except Exception as e:
        checks["checks"]["openai"] = {"status": "unavailable", "message": "Non-critical"}
    
    # Response time
    checks["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate status code
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)

@app.get("/health/live", tags=["infra"])
async def liveness_check():
    """Liveness check - basic application responsiveness"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running"
    }

# Home page
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/test-generator", response_class=HTMLResponse)
async def test_generator(request: Request):
    return templates.TemplateResponse("test-generator.html", {"request": request})

@app.get("/demo-submissions", response_class=HTMLResponse)
async def demo_submissions(request: Request):
    return templates.TemplateResponse("demo_submission.html", {"request": request})

@app.get("/sharing-guide", response_class=HTMLResponse)
async def sharing_guide(request: Request):
    return templates.TemplateResponse("sharing_guide.html", {"request": request})

@app.get("/complete-demo", response_class=HTMLResponse)
async def complete_demo(request: Request):
    return templates.TemplateResponse("complete_demo.html", {"request": request})

# Test page
@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("home.html",
                                      {"request": request, "user": user})

@app.get("/embed/{form_id}", response_class=HTMLResponse)
async def embed_form(form_id: str, request: Request):
    """Standalone form page for iframe embedding"""
    try:
        from backend.services.form_embedding import create_embeddable_form_page
        from backend.db import get_db
        
        # Handle demo form specially
        if form_id == "demo-form-123":
            demo_html = '''
            <form action="/api/submissions/submit/demo-form-123" method="POST" class="max-w-md mx-auto space-y-4">
                <input type="hidden" name="form_id" value="demo-form-123">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Name</label>
                    <input type="text" name="name" class="w-full border border-slate-300 rounded-lg px-3 py-2" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
                    <input type="email" name="email" class="w-full border border-slate-300 rounded-lg px-3 py-2" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Message</label>
                    <textarea name="message" class="w-full border border-slate-300 rounded-lg px-3 py-2 h-20"></textarea>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg">
                    Submit Demo
                </button>
            </form>
            '''
            embed_html = create_embeddable_form_page(demo_html, form_id)
            return HTMLResponse(content=embed_html)
        
        db = await get_db()
        # Try to find form by _id first (MongoDB ObjectId)
        from bson import ObjectId
        from bson.errors import InvalidId
        
        form_doc = None
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            form_doc = await db.forms.find_one({"_id": form_obj_id})
        except InvalidId:
            # If not valid ObjectId, try as string
            form_doc = await db.forms.find_one({"id": form_id})
        
        if not form_doc:
            return HTMLResponse(
                content=f"<h1>Form not found</h1><p>The requested form with ID '{form_id}' does not exist.</p>",
                status_code=404
            )
        
        if not form_doc.get("is_active", True):
            return HTMLResponse(
                content="<h1>Form inactive</h1><p>This form is no longer accepting submissions.</p>",
                status_code=410
            )
        
        # Create embeddable page
        embed_html = create_embeddable_form_page(form_doc["html"], form_id)
        return HTMLResponse(content=embed_html)
        
    except Exception as e:
        print(f"Error creating embed page: {e}")
        return HTMLResponse(
            content="<h1>Error</h1><p>Unable to load form.</p>",
            status_code=500
        )
# Local execution (allowed only when file is inside backend)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8009)
