import os, aiosmtplib, email.utils, mimetypes, html
from email.message import EmailMessage
import re
from backend.config import get_settings

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
