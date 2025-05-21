import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Jira
    JIRA_SERVER = os.getenv("JIRA_SERVER")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
    
    # ChromaDB
    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
    
    # OpenAI
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    
    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    
    # Escalation
    ESCALATION_TIME_HOURS = 24
