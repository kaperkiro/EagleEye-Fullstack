import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from app.logger import get_logger
from app.config import RECEIVER_EMAIL

logger = get_logger("ALARM")

SENDER_EMAIL = "eagleeyelarm@gmail.com"
SENDER_NAME = "EagleEye Alarm!"
APP_PASSWORD = "iybxtpkptqdczuhc"
RECEIVER_NAME = "Mottagarens Namn"
SUBJECT = "ALARM!!!"
BODY = "There is a thief in your store!!!"


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

        logger.info("E-post sent successfully!")
    except Exception as e:
        logger.error(f"SMTP error: {e}")
