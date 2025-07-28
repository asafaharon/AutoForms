import asyncio
import os
from tempfile import NamedTemporaryFile

# Try to import weasyprint, handle gracefully if missing
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️ WeasyPrint not available. PDF downloads will be disabled.")

def html_to_pdf_file(html: str) -> str:
    """
    יוצר קובץ PDF זמני מ־HTML באמצעות WeasyPrint.
    מחזיר את הנתיב לקובץ.
    """
    
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not installed. Please install it with: pip install weasyprint>=65.0")

    # עטיפת HTML בסיסית עם תמיכה ב־RTL וגופן בעברית
    full_html = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
      <meta charset="utf-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Alef&display=swap');
        @page {{
          size: A4;
          margin: 2cm;
        }}
        body {{
          font-family: 'Alef', sans-serif;
          direction: rtl;
          text-align: right;
          line-height: 1.6;
        }}
      </style>
    </head>
    <body>
      {html}
    </body>
    </html>
    """

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        HTML(string=full_html).write_pdf(tmp.name)
        tmp_path = tmp.name

    # Schedule cleanup after 1 hour (only if event loop is running)
    try:
        asyncio.create_task(cleanup_file_after_delay(tmp_path, 3600))
    except RuntimeError:
        # No event loop running, skip cleanup scheduling
        pass
    
    return tmp_path

def html_to_text_file(html: str, title: str = "generated_content") -> str:
    """
    Alternative download: Convert HTML to plain text file when PDF not available
    """
    import re
    from html import unescape
    
    # Remove HTML tags and decode entities
    text = re.sub('<[^<]+?>', '', html)
    text = unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text.strip())
    
    with NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as tmp:
        tmp.write(f"# {title}\n\n")
        tmp.write(text)
        tmp_path = tmp.name

    # Schedule cleanup after 1 hour (only if event loop is running)
    try:
        asyncio.create_task(cleanup_file_after_delay(tmp_path, 3600))
    except RuntimeError:
        # No event loop running, skip cleanup scheduling
        pass
    
    return tmp_path

async def cleanup_file_after_delay(file_path: str, delay_seconds: int):
    """Clean up file after specified delay."""
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Cleaned up temporary file: {file_path}")
    except Exception as e:
        print(f"❌ Failed to clean up file {file_path}: {e}")
