import os
import chromadb
from chromadb.utils import embedding_functions
from jira import JIRA
import openai
from email.mime.text import MIMEText
import smtplib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class AWRTriageSystem:
    def __init__(self):
        self.jira = JIRA(
            server=os.getenv("JIRA_SERVER"),
            basic_auth=(os.getenv("JIRA_USERNAME"), os.getenv("JIRA_API_TOKEN")),
        )

        # ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_PERSIST_DIR")
        )
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="awr_tickets", embedding_function=self.openai_ef
        )

        # Markers for duplicates and review flagging
        self.duplicate_threshold = 0.15
        self.review_threshold = 0.35

    def process_new_ticket(self, ticket_id: str):
        """Full processing pipeline"""
        ticket = self.jira.issue(ticket_id)
        ticket_text = self._generate_ticket_text(ticket)

        # search similar documents in vector DB
        results = self.collection.query(
            query_texts=[ticket_text], n_results=3, include=["distances", "metadatas"]
        )

        # categorize based on similarity
        if len(results["ids"][0]) > 0:
            closest = {
                "id": results["ids"][0][0],
                "distance": results["distances"][0][0],
                "metadata": results["metadatas"][0][0],
            }
            category = self._determine_category(closest["distance"])
        else:
            category = "NEW"
            closest = None

        # apply changes
        self._update_ticket(ticket, category, closest)

        # store in vector DB (except duplicates)
        if category != "DUPLICATE":
            self._store_in_vector_db(ticket, ticket_text)

    def _generate_ticket_text(self, ticket) -> str:
        """Generate embedding text from Jira ticket"""
        return f"""
        AWR Ticket: {ticket.key}
        Summary: {ticket.fields.summary}
        Description: {ticket.fields.description or 'No description'}
        Type: {ticket.fields.issuetype}
        Priority: {ticket.fields.priority}
        Components: {', '.join(c.name 
            for c in ticket.fields.components) 
            if hasattr(ticket.fields, 'components') else 'None'
        }
        """.strip()

    def _determine_category(self, distance: float) -> str:
        """Classify based on similarity distance"""
        if distance <= self.duplicate_threshold:
            return "DUPLICATE"
        elif distance <= self.review_threshold:
            return "FOR_REVIEW"
        return "NEW"

    def _update_ticket(self, ticket, category, similar_ticket=None):
        """Apply Jira updates based on category"""
        # Common updates
        updates = {
            "labels": list(set(ticket.fields.labels + [f"AI_{category}", "PROCESSED"])),
            "summary": self._format_title(
                ticket.fields.summary,
                category,
                similar_ticket["id"] if similar_ticket else None,
            ),
        }

        # Category-specific updates
        if category == "DUPLICATE":
            updates["status"] = {"name": "Pending Closure"}
            comment = self._generate_duplicate_comment(similar_ticket)
        elif category == "FOR_REVIEW":
            comment = self._generate_review_comment(similar_ticket)
        else:
            comment = "*AI Classification: NEW TICKET*\nNo similar tickets found."

        # Apply changes
        ticket.update(fields=updates)
        self.jira.add_comment(ticket.key, comment)
        self._send_notification(ticket, category, similar_ticket)

    def _store_in_vector_db(self, ticket, text: str):
        """Add ticket to ChromaDB"""
        self.collection.add(
            documents=[text],
            metadatas=[
                {
                    "key": ticket.key,
                    "summary": ticket.fields.summary,
                    "status": str(ticket.fields.status),
                    "created": ticket.fields.created,
                }
            ],
            ids=[ticket.key],
        )

    # ... (Include all helper methods from previous examples for comments/emails)

    def dispute_resolution_workflow(self, ticket_id: str):
        """Handle disputed classifications"""
        ticket = self.jira.issue(ticket_id)

        # Create approval task
        approval_task = self.jira.create_issue(
            project="OPS",
            summary=f"Review disputed classification: {ticket_id}",
            description=f"Dispute resolution required for {ticket_id}",
            issuetype={"name": "Task"},
            customfield_10010=ticket_id,  # Ticket link
        )

        # Update original ticket
        ticket.update(
            fields={
                "labels": [l for l in ticket.fields.labels if not l.startswith("AI_")]
                + ["DISPUTED"],
                "comment": f"Classification disputed. Approval task: {approval_task.key}",
            }
        )

        self._send_approval_request(ticket, approval_task)
