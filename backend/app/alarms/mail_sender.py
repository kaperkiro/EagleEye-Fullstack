import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))
from app.logger import get_logger

logger = get_logger("ALARM")


SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_NAME = os.getenv("SENDER_NAME", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
RECEIVER_NAME = os.getenv("RECEIVER_NAME", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")
SUBJECT = os.getenv("SUBJECT", "")
BODY = os.getenv("BODY", "")


def send_mail():
    """
    Construct and send an alarm email via Gmail SMTP.
    Uses configured sender and receiver credentials to build a multipart
    message with subject and body, establishes a secure connection,
    logs in, and transmits the message. Errors are logged and printed.
    """
    msg = MIMEMultipart()
    msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
    msg["To"] = formataddr((RECEIVER_NAME, RECEIVER_EMAIL))
    msg["Subject"] = Header(SUBJECT, "utf-8").encode()
    msg.attach(MIMEText(BODY, "plain", "utf-8"))

    logger.info("Connecting to Gmail SMTP (587) and sending mail…")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls()  # encrypt the connection
            server.ehlo()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        logger.info("E-mail sent successfully!")
    except Exception as e:
        logger.error(f"SMTP error: {e}")
