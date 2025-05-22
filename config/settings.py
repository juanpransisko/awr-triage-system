import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    
    # Jira
    JIRA_SERVER = os.getenv("JIRA_SERVER")
    JIRA_USER = os.getenv("JIRA_USERNAME")
    JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
    
    # OpenAI
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    
    # Chroma
    CHROMA_PATH = Path(os.getenv(
        "CHROMA_PERSIST_DIR", "./data/chroma_db"
    )).absolute()
    
    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    @classmethod
    def validate(cls):
        missing = []
        for var in ['JIRA_SERVER', 'JIRA_USERNAME', 'JIRA_API_TOKEN',
                   'OPENAI_API_KEY', 'EMAIL_USER', 'EMAIL_PASSWORD']:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")

Settings.validate()
settings = Settings()
#s = Settings()
#print(s.JIRA_TOKEN)
