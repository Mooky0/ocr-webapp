
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from models import Image, NotificationSubscription

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
PASSWORD = os.getenv("PASSWORD")


def send_notification(subscribers: list[NotificationSubscription], image: Image):
    context = ssl.create_default_context()

    body = (
        f"OCR processing for image '{image.filename}' has completed.\n\n"
        f"Status: {image.ocr_status}\n"
        f"Description: {image.description}\n"
    )
    if image.ocr_text:
        body += f"\nExtracted text:\n{image.ocr_text}\n"

    for sub in subscribers:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = sub.email
        message["Subject"] = f"OCR Complete: {image.filename}"
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SENDER_EMAIL, PASSWORD)
                server.sendmail(SENDER_EMAIL, sub.email, message.as_string())
            logger.info(f"Email sent to {sub.email} for image {image.filename}")
        except Exception as e:
            logger.error(f"Failed to send email to {sub.email}: {e}")