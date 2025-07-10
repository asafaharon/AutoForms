import smtplib, ssl

smtp_user = "asafasaf16@gmail.com"
smtp_pass = "fveqbylurycspyua"  # 16 תווים רצופים

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls(context=ssl.create_default_context())
    s.login(smtp_user, smtp_pass)
    print("✅ Authentication succeeded!")
