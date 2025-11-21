import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import Settings


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.settings.gmail_username
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(self.settings.gmail_smtp_host, self.settings.gmail_smtp_port) as smtp:
            smtp.starttls()
            smtp.login(self.settings.gmail_username, self.settings.gmail_app_password)
            smtp.send_message(msg)

