import os
from dotenv import load_dotenv
from jira import JIRA
import openai
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import json
from datetime import datetime

load_dotenv()
jira = JIRA(
    server=os.getenv("JIRA_SERVER"),
    basic_auth=(os.getenv("JIRA_USERNAME"), os.getenv("JIRA_API_TOKEN")),
)
