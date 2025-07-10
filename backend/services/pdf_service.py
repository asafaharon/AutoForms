from tempfile import NamedTemporaryFile
from weasyprint import HTML

def html_to_pdf_file(html: str) -> str:
    """
    יוצר קובץ PDF זמני מ־HTML באמצעות WeasyPrint.
    מחזיר את הנתיב לקובץ.
    """

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
        return tmp.name
