import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import Settings
from core.logger import logger
from typing import List, Optional, Union
import ssl


class EmailNotifier:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.max_retries = 3
        self.timeout = 10  # seconds

    def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send email with retry logic and rich formatting support.
            to: Single or list of recipient emails
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML content
            cc: List of CC recipients

            bool: True if sent successfully
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = Settings.EMAIL_USER
        msg["To"] = to if isinstance(to, str) else ", ".join(to)

        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Send with retry logic
        for attempt in range(self.max_retries):
            try:
                with smtplib.SMTP(
                    Settings.SMTP_SERVER, Settings.SMTP_PORT, timeout=self.timeout
                ) as server:
                    server.starttls(context=self.ssl_context)
                    server.login(Settings.EMAIL_USER, Settings.EMAIL_PASSWORD)
                    server.send_message(msg)

                logger.info(f"Email sent to {to}")
                return True

            except smtplib.SMTPException as e:
                logger.warning(f"Email attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Failed to send email after {self.max_retries} attempts"
                    )
                    return False

        return False
