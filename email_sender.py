# import smtplib
# import os
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from dotenv import load_dotenv

# load_dotenv()

# SMTP_EMAIL = os.getenv("SMTP_EMAIL")    
# SMTP_LOGIN = os.getenv("SMTP_LOGIN")    
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  
# SMTP_HOST = os.getenv("SMTP_HOST")     
# SMTP_PORT = int(os.getenv("SMTP_PORT"))

# def send_email(to_email, subject, message):
#     try:
#         msg = MIMEMultipart()
#         msg["From"] = SMTP_EMAIL
#         msg["To"] = to_email
#         msg["Subject"] = subject
#         msg.attach(MIMEText(message, "plain"))

#         server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
#         server.starttls()
#         server.login(SMTP_LOGIN, SMTP_PASSWORD) 
#         server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
#         server.quit()

#         print("Email sent successfully to:", to_email)
#         return True

#     except Exception as e:
#         print("Email Error:", e)
#         return False

































import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# load env only once
load_dotenv()

# NOTE:
# SMTP_EMAIL  = visible "From" email (must be verified sender)
# SMTP_LOGIN  = Brevo SMTP login (looks like xyz@smtp-brevo.com)
# SMTP_PASS   = Brevo SMTP key
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

    # build the mail contents
    mail = MIMEMultipart()
    mail["From"] = SMTP_EMAIL
    mail["To"] = to_email
    mail["Subject"] = subject
    mail.attach(MIMEText(message, "plain"))

    try:
        # use TLS (Brevo requires this)
        smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        smtp.starttls()

        # login using Brevo login
        smtp.login(SMTP_LOGIN, SMTP_PASS)

        # send raw mail text
        smtp.sendmail(SMTP_EMAIL, to_email, mail.as_string())
        smtp.quit()

        print(f"[MAIL] sent → {to_email}")
        return True

    except Exception as err:
        # don't over-log errors; just print them
        print("[MAIL ERROR]", err)
        return False
