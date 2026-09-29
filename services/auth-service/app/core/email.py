import smtplib
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, [to_email], message.as_string())