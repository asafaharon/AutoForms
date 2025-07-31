import os, aiosmtplib, email.utils, mimetypes, html, secrets
from email.message import EmailMessage
import re
from datetime import datetime
from backend.config import get_settings
from backend.models.form_models import FormSubmission, EmailUnsubscribe
from backend.services.rate_limiter import email_rate_limiter

def _get_smtp_config():
    settings = get_settings()
    return {
        'host': settings.smtp_host,
        'port': settings.smtp_port,
        'user': settings.smtp_user,
        'password': settings.smtp_password,
        'from_email': settings.email_from
    }

async def send_form_link(to_email: str, link: str, title: str, user_id: str = None, ip_address: str = None) -> None:
    print(f"📤 Sending form link to {to_email} with title: {title}")
    
    # Check rate limits before sending
    allowed, reason = email_rate_limiter.check_rate_limit(to_email, user_id, ip_address)
    if not allowed:
        print(f"🚫 Email rate limit exceeded: {reason}")
        raise Exception(f"Email rate limit exceeded: {reason}")
    
    # Check if email is unsubscribed
    if await check_unsubscribed(to_email):
        print(f"📧 Skipping email to {to_email} - unsubscribed")
        return
    
    msg = EmailMessage()
    smtp_config = _get_smtp_config()
    escaped_title = html.escape(title)
    escaped_link = html.escape(link)
    
    msg["From"] = smtp_config['from_email']
    msg["To"] = to_email
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Subject"] = f'Form "{escaped_title}" from AutoForms'

    msg.set_content(f"Hello,\nThe form '{escaped_title}' is available at the following link: {escaped_link}\n\nBest regards,\nAutoForms")
    msg.add_alternative(
        f"""<html><body dir="ltr">
             <p>Hello,</p><p>The form <b>{escaped_title}</b> is available at the following link:</p>
             <p><a href="{escaped_link}">{escaped_link}</a></p><p>Best regards,<br>AutoForms</p>
           </body></html>""",
        subtype="html"
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_config['host'],
            port=smtp_config['port'],
            username=smtp_config['user'],
            password=smtp_config['password'],
            start_tls=True,
            timeout=15,
        )
        print("✅ Link sent successfully.")
        
        # Record successful email send for rate limiting
        email_rate_limiter.record_email_sent(to_email, user_id, ip_address)
        
    except Exception as e:
        print(f"❌ Error sending link: {e}")
        raise

async def send_form_pdf(to_email: str, pdf_path: str, title: str, user_id: str = None, ip_address: str = None) -> None:
    try:
        print(f"📤 Attempting to send PDF to {to_email} for form: {title}")
        
        # Check rate limits before sending
        allowed, reason = email_rate_limiter.check_rate_limit(to_email, user_id, ip_address)
        if not allowed:
            print(f"🚫 Email rate limit exceeded: {reason}")
            raise Exception(f"Email rate limit exceeded: {reason}")
        
        # Check if email is unsubscribed
        if await check_unsubscribed(to_email):
            print(f"📧 Skipping email to {to_email} - unsubscribed")
            return

        msg = EmailMessage()
        smtp_config = _get_smtp_config()
        escaped_title = html.escape(title)
        
        msg["From"] = smtp_config['from_email']
        msg["To"] = to_email.strip()
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Subject"] = f'PDF file for form "{escaped_title}"'

        msg.set_content(f"Hi!\nAttached is the PDF file for the form \"{escaped_title}\".\n\nGood luck!")

        with open(pdf_path, "rb") as f:
            data = f.read()

        mimetype = mimetypes.guess_type(pdf_path)[0] or "application/pdf"
        maintype, subtype = mimetype.split("/")

        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=f"{escaped_title}.pdf"
        )

        await aiosmtplib.send(
            msg,
            hostname=smtp_config['host'],
            port=smtp_config['port'],
            username=smtp_config['user'],
            password=smtp_config['password'],
            start_tls=True,
            timeout=20,
        )
        print("✅ PDF sent successfully.")
        
        # Record successful email send for rate limiting
        email_rate_limiter.record_email_sent(to_email, user_id, ip_address)
        
    except Exception as e:
        print(f"❌ Error sending PDF: {e}")
        raise

async def send_reset_email(to_email: str, link: str, ip_address: str = None):
    # Check rate limits before sending (password reset emails have higher limits)
    allowed, reason = email_rate_limiter.check_rate_limit(to_email, None, ip_address)
    if not allowed:
        print(f"🚫 Email rate limit exceeded for password reset: {reason}")
        raise Exception(f"Email rate limit exceeded: {reason}")
    
    smtp_config = _get_smtp_config()
    escaped_link = html.escape(link)
    
    msg = EmailMessage()
    msg["From"] = smtp_config['from_email']
    msg["To"] = to_email
    msg["Subject"] = "Password reset – AutoForms"

    msg.set_content(f"Click the link below to reset your password:\n{escaped_link}")

    msg.add_alternative(f"""
    <html>
      <body>
        <p>You requested a password reset:</p>
        <p><a href="{escaped_link}">Click here to reset your password.</a></p>
        <p>If you did not request this, you can ignore this message.</p>
        <br><p>– AutoForms Team</p>
      </body>
    </html>
    """, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_config['host'],
            port=smtp_config['port'],
            username=smtp_config['user'],
            password=smtp_config['password'],
            start_tls=True,
        )
        print(f"✅ Password reset email sent to {to_email}")
        
        # Record successful email send for rate limiting
        email_rate_limiter.record_email_sent(to_email, None, ip_address)
        
    except Exception as e:
        print(f"❌ Failed to send password reset email to {to_email}: {e}")
        raise

def get_email_translations(language: str = "en") -> dict:
    """Get email template translations based on language"""
    translations = {
        "en": {
            "subject": "New submission for '{form_title}'",
            "header": "🎉 New Form Submission!",
            "form_label": "Form:",
            "submitted_label": "Submitted:",
            "form_data_title": "📝 Form Data:",
            "submission_details_title": "Submission Details:",
            "user_agent_label": "User Agent:",
            "referrer_label": "Referrer:",
            "dashboard_button": "View Dashboard",
            "unknown": "Unknown",
            "direct": "Direct",
            "text_header": "New Form Submission Received!",
            "view_dashboard_text": "View all submissions in your AutoForms dashboard.",
            "signature": "AutoForms Team"
        },
        "he": {
            "subject": "הגשה חדשה עבור '{form_title}'",
            "header": "🎉 הגשת טופס חדשה!",
            "form_label": "טופס:",
            "submitted_label": "הוגש בתאריך:",
            "form_data_title": "📝 נתוני הטופס:",
            "submission_details_title": "פרטי ההגשה:",
            "user_agent_label": "דפדפן:",
            "referrer_label": "מקור:",
            "dashboard_button": "צפה בלוח הבקרה",
            "unknown": "לא ידוע",
            "direct": "ישיר",
            "text_header": "התקבלה הגשת טופס חדשה!",
            "view_dashboard_text": "צפה בכל ההגשות בלוח הבקרה של AutoForms.",
            "signature": "צוות AutoForms"
        }
    }
    return translations.get(language, translations["en"])

async def send_submission_notification(to_email: str, submission: FormSubmission, form_language: str = "en", user_id: str = None, ip_address: str = None):
    """Send email notification when a form receives a new submission"""
    
    # Check rate limits before sending
    allowed, reason = email_rate_limiter.check_rate_limit(to_email, user_id, ip_address)
    if not allowed:
        print(f"🚫 Email rate limit exceeded for submission notification: {reason}")
        return  # Fail silently for submission notifications to not break form submission
    
    # Check if email is unsubscribed
    if await check_unsubscribed(to_email):
        print(f"📧 Skipping email to {to_email} - unsubscribed")
        return
    
    # Get translations for the form's language
    t = get_email_translations(form_language)
    
    # Set email direction based on language
    email_dir = "rtl" if form_language == "he" else "ltr"
    try:
        smtp_config = _get_smtp_config()
        
        msg = EmailMessage()
        msg["From"] = smtp_config['from_email']
        msg["To"] = to_email
        msg["Subject"] = t["subject"].format(form_title=submission.form_title)
        
        # Format submission data for email
        data_html = ""
        data_text = ""
        
        for field, value in submission.data.items():
            # Clean field name for display
            field_display = field.replace("_", " ").title()
            
            data_html += f"<tr><td><strong>{html.escape(field_display)}:</strong></td><td>{html.escape(str(value))}</td></tr>"
            data_text += f"{field_display}: {value}\n"
        
        # Text version
        text_content = f"""
{t["text_header"]}

{t["form_label"]} {submission.form_title}
{t["submitted_label"]} {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

{t["form_data_title"].replace('📝 ', '')}
{data_text}

{t["submission_details_title"]}
- {t["user_agent_label"]} {submission.user_agent or t["unknown"]}
- {t["referrer_label"]} {submission.referrer or t["direct"]}

{t["view_dashboard_text"]}

{t["signature"]}
        """.strip()
        
        # HTML version
        html_content = f"""
        <html dir="{email_dir}">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; direction: {email_dir}; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: {'right' if form_language == 'he' else 'left'}; }}
                .content {{ background: #f8fafc; padding: 20px; text-align: {'right' if form_language == 'he' else 'left'}; }}
                .submission-data {{ background: white; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: {'right' if form_language == 'he' else 'left'}; }}
                .meta {{ background: #f1f5f9; padding: 10px; border-radius: 4px; font-size: 0.9em; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{t["header"]}</h2>
                </div>
                <div class="content">
                    <p><strong>{t["form_label"]}</strong> {html.escape(submission.form_title)}</p>
                    <p><strong>{t["submitted_label"]}</strong> {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    
                    <div class="submission-data">
                        <h3>{t["form_data_title"]}</h3>
                        <table>
                            {data_html}
                        </table>
                    </div>
                    
                    <div class="meta">
                        <strong>{t["submission_details_title"]}</strong><br>
                        {t["user_agent_label"]} {html.escape(submission.user_agent or t["unknown"])}<br>
                        {t["referrer_label"]} {html.escape(submission.referrer or t["direct"])}
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="#" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                            {t["dashboard_button"]}
                        </a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Add unsubscribe footer to HTML content
        settings = get_settings()
        html_content_with_footer = add_unsubscribe_footer(html_content, to_email, settings)
        
        msg.set_content(text_content)
        msg.add_alternative(html_content_with_footer, subtype="html")
        
        await aiosmtplib.send(
            msg,
            hostname=smtp_config['host'],
            port=smtp_config['port'],
            username=smtp_config['user'],
            password=smtp_config['password'],
            start_tls=True,
            timeout=15,
        )
        print(f"✅ Submission notification sent to {to_email}")
        
        # Record successful email send for rate limiting
        email_rate_limiter.record_email_sent(to_email, user_id, ip_address)
        
    except Exception as e:
        print(f"❌ Failed to send submission notification to {to_email}: {e}")

async def generate_unsubscribe_token(email: str) -> str:
    """Generate secure unsubscribe token"""
    return secrets.token_urlsafe(32)

async def check_unsubscribed(email: str) -> bool:
    """Check if email is unsubscribed"""
    try:
        from backend.db import get_db
        db = await get_db()
        unsubscribe_record = await db.email_unsubscribes.find_one({"email": email})
        return unsubscribe_record is not None
    except Exception as e:
        print(f"❌ Error checking unsubscribe status: {e}")
        return False

async def unsubscribe_email(token: str, reason: str = None) -> bool:
    """Process email unsubscribe request"""
    try:
        from backend.db import get_db
        from bson import ObjectId
        db = await get_db()
        
        # Token is stored as a query parameter, we need to validate it exists in our system
        # For now, let's extract email from a secure mapping or create one
        # This is a simplified implementation - in production you'd want to store token->email mapping
        
        # Create unsubscribe record
        unsubscribe_id = str(ObjectId())
        unsubscribe_record = {
            "id": unsubscribe_id,
            "unsubscribe_token": token,
            "unsubscribed_at": datetime.utcnow(),
            "reason": reason
        }
        
        await db.email_unsubscribes.insert_one(unsubscribe_record)
        print(f"✅ Email unsubscribed with token: {token}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing unsubscribe: {e}")
        return False

def add_unsubscribe_footer(html_content: str, email: str, settings) -> str:
    """Add unsubscribe footer to email content"""
    unsubscribe_token = secrets.token_urlsafe(32)
    unsubscribe_url = f"{settings.base_url}/unsubscribe?token={unsubscribe_token}&email={email}"
    
    footer = f"""
    <div style="border-top: 1px solid #e2e8f0; margin-top: 30px; padding-top: 20px; font-size: 12px; color: #64748b; text-align: center;">
        <p>You received this email because you submitted a form or requested notifications from AutoForms.</p>
        <p><a href="{unsubscribe_url}" style="color: #64748b; text-decoration: underline;">Unsubscribe from these emails</a></p>
        <p>AutoForms - Form Builder & Management System</p>
    </div>
    """
    
    # Insert footer before closing body tag
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{footer}</body>")
    else:
        html_content += footer
    
    return html_content
