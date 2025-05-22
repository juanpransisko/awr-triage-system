import smtplib
from email.mime.text import MIMEText
from config.settings import Settings
from core.logger import logger

class EmailNotifier:
    def send(self, to: str, subject: str, body: str):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = Settings.EMAIL_USER
        msg['To'] = to

        try:
            with smtplib.SMTP(Settings.SMTP_SERVER, Settings.SMTP_PORT) as server:
                server.starttls()
                server.login(Settings.EMAIL_USER, Settings.EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email sent to {to}")
        except Exception as e:
            logger.error(f"Email failed: {str(e)}")
