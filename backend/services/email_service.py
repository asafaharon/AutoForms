import os, aiosmtplib, email.utils, mimetypes
from email.message import EmailMessage
import re
import email.utils
from email.message import EmailMessage
import mimetypes
import aiosmtplib

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM    = os.getenv("EMAIL_FROM", SMTP_USER)  # ברירת מחדל אם לא הוגדר

async def send_form_link(to_email: str, link: str, title: str) -> None:
    print(f"📤 Sending form link to {to_email} with title: {title}")
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Subject"] = f'Form "{title}" from AutoForms'

    msg.set_content(f"Hello,\nThe form '{title}' is available at the following link: {link}\n\nBest regards,\nAutoForms")
    msg.add_alternative(
        f"""<html><body dir="ltr">
             <p>Hello,</p><p>The form <b>{title}</b> is available at the following link:</p>
             <p><a href="{link}">{link}</a></p><p>Best regards,<br>AutoForms</p>
           </body></html>""",
        subtype="html"
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
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
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email.strip()
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Subject"] = f'PDF file for form "{title}"'

        msg.set_content(f"Hi!\nAttached is the PDF file for the form \"{title}\".\n\nGood luck!")

        with open(pdf_path, "rb") as f:
            data = f.read()

        mimetype = mimetypes.guess_type(pdf_path)[0] or "application/pdf"
        maintype, subtype = mimetype.split("/")

        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=f"{title}.pdf"
        )

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
            timeout=20,
        )
        print("✅ PDF sent successfully.")
    except Exception as e:
        print(f"❌ Error sending PDF: {e}")

async def send_reset_email(to_email: str, link: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = "Password reset – AutoForms"

    msg.set_content(f"Click the link below to reset your password:\n{link}")

    msg.add_alternative(f"""
    <html>
      <body>
        <p>You requested a password reset:</p>
        <p><a href="{link}">Click here to reset your password.</a></p>
        <p>If you did not request this, you can ignore this message.</p>
        <br><p>– AutoForms Team</p>
      </body>
    </html>
    """, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        print(f"✅ Password reset email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send password reset email to {to_email}: {e}")
