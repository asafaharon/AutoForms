import os, aiosmtplib, email.utils, mimetypes, html
from email.message import EmailMessage
import re
from backend.config import get_settings
from backend.models.form_models import FormSubmission

def _get_smtp_config():
    settings = get_settings()
    return {
        'host': settings.smtp_host,
        'port': settings.smtp_port,
        'user': settings.smtp_user,
        'password': settings.smtp_password,
        'from_email': settings.email_from
    }

async def send_form_link(to_email: str, link: str, title: str) -> None:
    print(f"📤 Sending form link to {to_email} with title: {title}")
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
    except Exception as e:
        print(f"❌ Error sending link: {e}")

async def send_form_pdf(to_email: str, pdf_path: str, title: str) -> None:
    try:
        print(f"📤 Attempting to send PDF to {to_email} for form: {title}")

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
    except Exception as e:
        print(f"❌ Error sending PDF: {e}")

async def send_reset_email(to_email: str, link: str):
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
    except Exception as e:
        print(f"❌ Failed to send password reset email to {to_email}: {e}")

async def send_submission_notification(to_email: str, submission: FormSubmission):
    """Send email notification when a form receives a new submission"""
    try:
        smtp_config = _get_smtp_config()
        
        msg = EmailMessage()
        msg["From"] = smtp_config['from_email']
        msg["To"] = to_email
        msg["Subject"] = f"New submission for '{submission.form_title}'"
        
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
New Form Submission Received!

Form: {submission.form_title}
Submitted: {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Form Data:
{data_text}

Submission Details:
- IP Address: {submission.ip_address or 'Unknown'}
- User Agent: {submission.user_agent or 'Unknown'}
- Referrer: {submission.referrer or 'Direct'}

View all submissions in your AutoForms dashboard.

AutoForms Team
        """.strip()
        
        # HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8fafc; padding: 20px; }}
                .submission-data {{ background: white; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; }}
                .meta {{ background: #f1f5f9; padding: 10px; border-radius: 4px; font-size: 0.9em; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎉 New Form Submission!</h2>
                </div>
                <div class="content">
                    <p><strong>Form:</strong> {html.escape(submission.form_title)}</p>
                    <p><strong>Submitted:</strong> {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    
                    <div class="submission-data">
                        <h3>📝 Form Data:</h3>
                        <table>
                            {data_html}
                        </table>
                    </div>
                    
                    <div class="meta">
                        <strong>Submission Details:</strong><br>
                        IP Address: {html.escape(submission.ip_address or 'Unknown')}<br>
                        User Agent: {html.escape(submission.user_agent or 'Unknown')}<br>
                        Referrer: {html.escape(submission.referrer or 'Direct')}
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="#" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                            View Dashboard
                        </a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")
        
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
        
    except Exception as e:
        print(f"❌ Failed to send submission notification to {to_email}: {e}")
