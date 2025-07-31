"""
Form submission collection and management API
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, Response
from bson import ObjectId
from bson.errors import InvalidId
from backend.db import get_db
from backend.deps import get_current_user
from backend.models.form_models import FormSubmission
from backend.services.email_service import send_submission_notification
from backend.services.form_generator import detect_language_fast

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

@router.post("/submit/{form_id}")
async def submit_form(
    form_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Public endpoint to collect form submissions
    This is where external forms POST their data
    """
    try:
        db = await get_db()
        
        # Get form data from request body
        try:
            # Try JSON first
            form_data = await request.json()
        except:
            # Fallback to form-encoded data
            form_body = await request.form()
            form_data = dict(form_body)
        
        # Handle demo and fallback forms specially
        if form_id in ["demo-form-123", "fallback-contact", "fallback-registration", "fallback-feedback", "fallback-survey", "fallback-general"]:
            # Create demo submission record
            form_titles = {
                "demo-form-123": "Demo Contact Form",
                "fallback-contact": "Contact Form (Fallback)",
                "fallback-registration": "Registration Form (Fallback)",
                "fallback-feedback": "Feedback Form (Fallback)",
                "fallback-survey": "Survey Form (Fallback)",
                "fallback-general": "General Form (Fallback)"
            }
            
            submission = FormSubmission(
                id=str(uuid.uuid4()),
                form_id=form_id,
                form_title=form_titles.get(form_id, "Demo Form"),
                data=form_data,
                submitted_at=datetime.utcnow(),
                    user_agent=request.headers.get("user-agent"),
                referrer=request.headers.get("referer")
            )
            
            # For demo/fallback forms, just log it instead of saving to database
            print(f"📝 {form_titles.get(form_id, 'Demo')} submission received: {form_data}")
            
            if form_id == "demo-form-123":
                message = "Demo form submitted successfully! In a real form, this data would be saved to your dashboard."
            else:
                message = "Fallback form submitted successfully! This form was generated when AI was unavailable."
            
            return JSONResponse(
                content={
                    "success": True,
                    "message": message,
                    "submission_id": submission.id
                },
                status_code=201
            )
        
        # Get the form details
        
        form_doc = None
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            form_doc = await db.forms.find_one({"_id": form_obj_id})
        except InvalidId:
            # If not valid ObjectId, try as string
            form_doc = await db.forms.find_one({"id": form_id})
        
        if not form_doc:
            raise HTTPException(status_code=404, detail="Form not found")
        
        if not form_doc.get("is_active", True):
            raise HTTPException(status_code=410, detail="Form is no longer accepting submissions")
        
        # Create submission record
        submission = FormSubmission(
            id=str(uuid.uuid4()),
            form_id=form_id,
            form_title=form_doc.get("title", "Untitled Form"),
            data=form_data,
            submitted_at=datetime.utcnow(),
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer")
        )
        
        # Save submission to database
        await db.form_submissions.insert_one(submission.to_dict())
        
        # Update form submission count
        try:
            # Try as ObjectId first (for forms saved with _id)
            form_obj_id = ObjectId(form_id)
            await db.forms.update_one(
                {"_id": form_obj_id},
                {"$inc": {"submission_count": 1}}
            )
        except InvalidId:
            # Fallback to string id for older forms
            await db.forms.update_one(
                {"id": form_id},
                {"$inc": {"submission_count": 1}}
            )
        
        # Send email notification in background
        try:
            form_owner_id = form_doc.get("user_id")
            if form_owner_id:
                # Try to find user by ObjectId first, then by string id
                user_doc = None
                try:
                    if isinstance(form_owner_id, ObjectId):
                        user_doc = await db.users.find_one({"_id": form_owner_id})
                    else:
                        user_obj_id = ObjectId(form_owner_id)
                        user_doc = await db.users.find_one({"_id": user_obj_id})
                except (InvalidId, TypeError):
                    # Fallback to string lookup
                    user_doc = await db.users.find_one({"id": form_owner_id})
                
                if user_doc and user_doc.get("email"):
                    # Detect form language from stored language field or form content
                    form_language = form_doc.get("language", "en")
                    if form_language == "en":
                        # Fallback: detect from form content if language not stored
                        form_content = form_doc.get("prompt", "")
                        if form_content:
                            form_language = detect_language_fast(form_content)
                    
                    background_tasks.add_task(
                        send_submission_notification,
                        user_doc["email"],
                        submission,
                        form_language
                    )
                    print(f"📧 Notification queued for form owner: {user_doc.get('email')}")
                else:
                    print(f"⚠️ Form owner not found or no email: user_id={form_owner_id}")
        except Exception as e:
            # Email notification failure shouldn't stop submission
            print(f"Failed to send notification: {e}")
            import traceback
            traceback.print_exc()
        
        # Return success response
        return JSONResponse(
            content={
                "success": True,
                "message": "Form submitted successfully",
                "submission_id": submission.id
            },
            status_code=201
        )
        
    except Exception as e:
        print(f"Form submission error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process form submission: {str(e)}")

@router.get("/form/{form_id}")
async def get_form_submissions(
    form_id: str,
    user = Depends(get_current_user),
    page: int = 1,
    limit: int = 50
):
    """Get submissions for a specific form (authenticated users only)"""
    try:
        db = await get_db()
        
        # Verify user owns this form - handle both dict and object formats
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        
        # Try to find form by different ID formats
        form_doc = None
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            user_obj_id = ObjectId(user_id)
            form_doc = await db.forms.find_one({"_id": form_obj_id, "user_id": user_obj_id})
        except (InvalidId, TypeError):
            pass
            
        if not form_doc:
            # Try string-based lookup
            form_doc = await db.forms.find_one({"id": form_id, "user_id": user_id})
            
        if not form_doc:
            raise HTTPException(status_code=404, detail="Form not found or access denied")
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get submissions
        cursor = db.form_submissions.find({"form_id": form_id}).sort("submitted_at", -1).skip(skip).limit(limit)
        submissions = await cursor.to_list(length=limit)
        
        # Convert ObjectId fields to strings for JSON serialization
        for submission in submissions:
            if "_id" in submission:
                submission["_id"] = str(submission["_id"])
            if "submitted_at" in submission and hasattr(submission["submitted_at"], "isoformat"):
                submission["submitted_at"] = submission["submitted_at"].isoformat()
        
        # Get total count
        total_count = await db.form_submissions.count_documents({"form_id": form_id})
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": skip + len(submissions) < total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch submissions")

@router.get("/user/all")
async def get_user_submissions(
    user = Depends(get_current_user),
    page: int = 1,
    limit: int = 20
):
    """Get all submissions for the current user's forms"""
    try:
        db = await get_db()
        
        # Get user's form IDs - handle both dict and object formats
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        # Try to find user forms by ObjectId first, then string id
        user_forms = []
        try:
            user_obj_id = ObjectId(user_id)
            user_forms = await db.forms.find({"user_id": user_obj_id}).to_list(length=None)
        except (InvalidId, TypeError):
            # Fallback to string lookup
            user_forms = await db.forms.find({"user_id": user_id}).to_list(length=None)
            
        # Extract form IDs, handling both _id and id fields
        form_ids = []
        for form in user_forms:
            if "_id" in form:
                form_ids.append(str(form["_id"]))
            elif "id" in form:
                form_ids.append(form["id"])
        
        if not form_ids:
            return {
                "submissions": [],
                "total_count": 0,
                "page": page,
                "limit": limit,
                "has_more": False
            }
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get submissions for user's forms
        cursor = db.form_submissions.find(
            {"form_id": {"$in": form_ids}}
        ).sort("submitted_at", -1).skip(skip).limit(limit)
        
        submissions = await cursor.to_list(length=limit)
        
        # Convert ObjectId fields to strings for JSON serialization
        for submission in submissions:
            if "_id" in submission:
                submission["_id"] = str(submission["_id"])
            if "submitted_at" in submission and hasattr(submission["submitted_at"], "isoformat"):
                submission["submitted_at"] = submission["submitted_at"].isoformat()
        
        # Get total count
        total_count = await db.form_submissions.count_documents({"form_id": {"$in": form_ids}})
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": skip + len(submissions) < total_count
        }
        
    except Exception as e:
        print(f"Error fetching user submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch submissions")

@router.delete("/{submission_id}")
async def delete_submission(
    submission_id: str,
    user = Depends(get_current_user)
):
    """Delete a specific submission (form owner only)"""
    try:
        db = await get_db()
        
        # Get submission
        submission_doc = await db.form_submissions.find_one({"id": submission_id})
        if not submission_doc:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Verify user owns the form - handle both dict and object formats
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        
        # Try to find form by different ID formats
        form_doc = None
        form_id = submission_doc["form_id"]
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            user_obj_id = ObjectId(user_id)
            form_doc = await db.forms.find_one({"_id": form_obj_id, "user_id": user_obj_id})
        except (InvalidId, TypeError):
            pass
            
        if not form_doc:
            # Try string-based lookup
            form_doc = await db.forms.find_one({"id": form_id, "user_id": user_id})
            
        if not form_doc:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete submission
        result = await db.form_submissions.delete_one({"id": submission_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Update form submission count
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            await db.forms.update_one(
                {"_id": form_obj_id},
                {"$inc": {"submission_count": -1}}
            )
        except (InvalidId, TypeError):
            # Fallback to string id
            await db.forms.update_one(
                {"id": form_id},
                {"$inc": {"submission_count": -1}}
            )
        
        return {"success": True, "message": "Submission deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete submission")

@router.get("/export/{form_id}")
async def export_submissions(
    form_id: str,
    user = Depends(get_current_user),
    format: str = "json"  # json, csv
):
    """Export form submissions in various formats"""
    try:
        db = await get_db()
        
        # Verify user owns this form - handle both dict and object formats
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        
        # Try to find form by different ID formats
        form_doc = None
        try:
            # Try as ObjectId first
            form_obj_id = ObjectId(form_id)
            user_obj_id = ObjectId(user_id)
            form_doc = await db.forms.find_one({"_id": form_obj_id, "user_id": user_obj_id})
        except (InvalidId, TypeError):
            pass
            
        if not form_doc:
            # Try string-based lookup
            form_doc = await db.forms.find_one({"id": form_id, "user_id": user_id})
            
        if not form_doc:
            raise HTTPException(status_code=404, detail="Form not found or access denied")
        
        # Get all submissions
        submissions = await db.form_submissions.find({"form_id": form_id}).sort("submitted_at", -1).to_list(length=None)
        
        # Convert ObjectId fields to strings for JSON serialization
        for submission in submissions:
            if "_id" in submission:
                submission["_id"] = str(submission["_id"])
            if "submitted_at" in submission and hasattr(submission["submitted_at"], "isoformat"):
                submission["submitted_at"] = submission["submitted_at"].isoformat()
        
        if format.lower() == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if submissions:
                # Get all unique field names
                field_names = set()
                for sub in submissions:
                    field_names.update(sub["data"].keys())
                
                # Add metadata fields
                all_fields = ["submission_id", "submitted_at"] + sorted(field_names)
                
                writer = csv.DictWriter(output, fieldnames=all_fields)
                writer.writeheader()
                
                for sub in submissions:
                    row = {
                        "submission_id": sub["id"],
                        "submitted_at": sub["submitted_at"],
                    }
                    # Add form data
                    row.update(sub["data"])
                    writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={form_doc['title']}_submissions.csv"}
            )
        
        else:  # JSON format
            return {
                "form_title": form_doc["title"],
                "form_id": form_id,
                "export_date": datetime.utcnow().isoformat(),
                "total_submissions": len(submissions),
                "submissions": submissions
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to export submissions")