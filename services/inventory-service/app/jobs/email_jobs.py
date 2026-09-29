from app.core.email import send_email


def send_email_job(to_email: str, subject: str, body: str) -> None:
    send_email(to_email, subject, body)