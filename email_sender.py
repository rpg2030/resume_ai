
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))


def send_email(to_email, subject, message):
    """
    Basic SMTP mail sender.
    Not using anything fancy here — just enough to shoot an email.
    """

    mail = MIMEMultipart()
    mail["From"] = SMTP_EMAIL
    mail["To"] = to_email
    mail["Subject"] = subject
    mail.attach(MIMEText(message, "plain"))

    try:
        smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        smtp.starttls()

        smtp.login(SMTP_LOGIN, SMTP_PASS)

        smtp.sendmail(SMTP_EMAIL, to_email, mail.as_string())
        smtp.quit()

        print(f"[MAIL] sent → {to_email}")
        return True

    except Exception as err:
        print("[MAIL ERROR]", err)
        return False
