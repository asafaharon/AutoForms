import os
from tempfile import NamedTemporaryFile
from xhtml2pdf import pisa

def html_to_pdf_file(html: str) -> str:
    """
    יוצר קובץ PDF זמני מ־HTML באמצעות xhtml2pdf.
    מחזיר את הנתיב לקובץ.
    """

    # עטיפת HTML בסיסית עם תמיכה ב־RTL (מוגבלת ב-xhtml2pdf) וגופן עברי
    full_html = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
      <meta charset="utf-8">
      <style>
        @page {{
          size: A4;
          margin: 2cm;
        }}
        body {{
          font-family: Helvetica, sans-serif;
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
        result = pisa.CreatePDF(full_html, dest=tmp)
        if result.err:
            raise Exception("Failed to generate PDF with xhtml2pdf")
        return tmp.name
