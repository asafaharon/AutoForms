"""
Production error handling and logging
"""
import traceback
import uuid
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import logging

# Setup templates for error pages
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

class ErrorHandler:
    """Production error handling service"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup production logging"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Configure logging format
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # Console output
                # Add file handler for production
                # logging.FileHandler('app.log') if os.getenv("APP_ENV") == "production" else logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("autoforms")
    
    def log_error(self, error: Exception, request: Request = None, user_id: str = None):
        """Log error with context"""
        error_id = str(uuid.uuid4())[:8]
        
        context = {
            "error_id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
        }
        
        if request:
            context.update({
                "url": str(request.url),
                "method": request.method,
                "user_agent": request.headers.get("user-agent", "unknown")
            })
        
        # Log the error
        self.logger.error(f"Error {error_id}: {error}", extra=context)
        
        # In production, you might want to send to external service like Sentry
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            # import sentry_sdk
            # sentry_sdk.capture_exception(error)
            pass
        
        return error_id
    
    def create_error_response(self, request: Request, status_code: int, error: Exception = None, user_id: str = None):
        """Create error response with appropriate template"""
        
        # Log the error if provided
        error_id = None
        if error:
            error_id = self.log_error(error, request, user_id)
        
        # Determine if we should show debug info
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Common template context
        context = {
            "request": request,
            "error_id": error_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "debug": debug
        }
        
        # Add error details for debug mode
        if debug and error:
            context["error_details"] = traceback.format_exc()
        
        # Choose template based on status code
        if status_code == 404:
            template_name = "errors/404.html"
        elif status_code >= 500:
            template_name = "errors/500.html"
        else:
            template_name = "errors/500.html"  # Default to 500 template
        
        try:
            return templates.TemplateResponse(
                template_name,
                context,
                status_code=status_code
            )
        except Exception as template_error:
            # Fallback if template fails
            self.logger.error(f"Template error: {template_error}")
            return HTMLResponse(
                content=f"""
                <html>
                    <head><title>Error {status_code}</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1>Error {status_code}</h1>
                        <p>Something went wrong. Please try again later.</p>
                        <a href="/">Go Home</a>
                    </body>
                </html>
                """,
                status_code=status_code
            )

# Global error handler instance
error_handler = ErrorHandler()

def handle_404_error(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return error_handler.create_error_response(request, 404)

def handle_500_error(request: Request, exc: Exception):
    """Handle 500 errors"""
    return error_handler.create_error_response(request, 500, exc)

def handle_general_error(request: Request, exc: Exception):
    """Handle general exceptions"""
    status_code = getattr(exc, 'status_code', 500)
    return error_handler.create_error_response(request, status_code, exc)