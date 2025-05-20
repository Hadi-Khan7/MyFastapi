import smtplib
from email.mime.text import MIMEText

# Hardcoded Email Config
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "hadikhan7k@gmail.com"
EMAIL_PASSWORD = "ybbkcwbrsusuodgc"  # Use app password, not Gmail password

def send_verification_email(email: str, user_id: int):
    try:
        subject = "Verify Your Email"
        body = f"Click the link to verify your account: http://localhost:8000/verify/{user_id}"
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = EMAIL_USER
        message["To"] = email

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(message)
        print(f"[EMAIL SENT] to {email}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        raise Exception("Error sending email") from e


def send_task_notification(to_email: str, task_details: str):
    try:
        subject = "Task Assigned"
        body = f"New task assigned: {task_details}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"[NOTIFICATION SENT] to {to_email}")

    except Exception as e:
        print(f"[TASK EMAIL ERROR] {e}")
