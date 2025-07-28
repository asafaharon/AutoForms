"""
Templates API Router
Provides endpoints for form template management
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional

from backend.services.form_templates import form_templates_service, FormTemplate

router = APIRouter(prefix="/api/templates", tags=["templates"])

@router.get("/", response_model=List[dict])
async def get_all_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search templates")
):
    """
    Get all form templates, optionally filtered by category or search query
    """
    try:
        if search:
            templates = form_templates_service.search_templates(search)
        elif category:
            templates = form_templates_service.get_templates_by_category(category)
        else:
            templates = form_templates_service.get_all_templates()
        
        # Convert to dict format for JSON response
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "preview_image": t.preview_image,
                "tags": t.tags
            }
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/categories")
async def get_template_categories():
    """
    Get all available template categories
    """
    try:
        categories = form_templates_service.get_categories()
        return {
            "categories": [
                {"id": cat, "name": cat.replace("_", " ").title()}
                for cat in categories
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/{template_id}")
async def get_template_by_id(template_id: str):
    """
    Get a specific template by ID, including the HTML content
    """
    try:
        template = form_templates_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "preview_image": template.preview_image,
            "tags": template.tags,
            "html": template.html
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.get("/{template_id}/preview", response_class=HTMLResponse)
async def preview_template(template_id: str):
    """
    Get template HTML for preview (returns raw HTML)
    """
    try:
        template = form_templates_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Return the HTML wrapped in a complete page for preview
        preview_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template.name} - Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
    </style>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-4xl mx-auto">
        <div class="mb-6 text-center">
            <h1 class="text-2xl font-bold text-gray-800">{template.name}</h1>
            <p class="text-gray-600">{template.description}</p>
        </div>
        {template.html}
    </div>
</body>
</html>
        """
        return HTMLResponse(content=preview_html)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview template: {str(e)}")

@router.post("/{template_id}/use", response_class=HTMLResponse)
async def use_template(template_id: str):
    """
    Use a template - returns the HTML with submission functionality
    """
    try:
        template = form_templates_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # For now, let's just return the template HTML with basic form response
        # Import the response builder from generate router
        from backend.routers.generate import build_form_response_html
        
        # Return the template HTML using the existing response builder
        return HTMLResponse(content=build_form_response_html(
            template.html, 
            for_demo=False
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Template error: {e}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Failed to use template: {str(e)}")

@router.get("/{template_id}/use-with-submissions")
async def get_template_with_submissions(template_id: str):
    """
    Get template with submission endpoints - returns JSON with all necessary data
    """
    try:
        template = form_templates_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Inject submission endpoint into the template
        form_data = inject_submission_endpoint(template.html)
        
        return {
            "template_id": template.id,
            "template_name": template.name,
            "form_id": form_data["form_id"],
            "html": form_data["html"],
            "submission_url": form_data["submission_url"],
            "embed_code": form_data["embed_code"],
            "iframe_code": form_data["iframe_code"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare template: {str(e)}")