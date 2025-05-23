import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    JIRA_SERVER = os.getenv("JIRA_SERVER")
    JIRA_USERNAME = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_MODEL_DIMENSIONS = int(os.getenv("AZURE_OPENAI_MODEL_DIMENSIONS"))
    AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

    CHROMA_PATH = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")).absolute()

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default fallback: TLS port
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    ESCALATION_HOURS = int(os.getenv("ESCALATION_HOURS", 24))
    XML_SOURCE = os.getenv("XML_SOURCE")

    @classmethod
    def validate(cls):
        """Validate critical env vars exist before application boot."""
        required_vars = [
            "JIRA_SERVER",
            "JIRA_USERNAME",
            "JIRA_API_TOKEN",
            "OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_API_KEY",
            "CHROMA_PERSIST_DIR",
            "SMTP_SERVER",
            "SMTP_PORT",
            "EMAIL_USER",
            "EMAIL_PASSWORD",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )


Settings.validate()
settings = Settings()
