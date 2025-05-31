from datetime import datetime
from typing import Dict, Any

from awr.jira_rest import JiraClientREST
from awr.chroma import ChromaDB
from awr.models import JiraTicket
from awr.embedding import EmbeddingGenerator
from awr.messaging import EmailNotifier
from awr.logger import logger
from config.thresholds import Thresholds
from config.settings import settings


class TriageWorkflow:
    def __init__(self):
        self.jira = JiraClientREST()
        self.chroma = ChromaDB()
        self.embedder = EmbeddingGenerator()
        self.notifier = EmailNotifier()

    def process(self, ticket_id: str):
        raw_ticket = self.jira.get_ticket(ticket_id)
        if not raw_ticket:
            logger.error(f"[Triage] Ticket not found: {ticket_id}")
            return

        fields = raw_ticket["fields"]
        ticket = JiraTicket(
            id=raw_ticket["key"],
            summary=fields["summary"],
            description=fields.get("description", ""),
            priority=fields["priority"]["name"],
            labels=fields.get("labels", []),
        )
        ticket_text = self._format_ticket_text(ticket)

        try:
            embedding = self.embedder.generate(ticket_text)
        except Exception as e:
            logger.error(
                f"[Triage] Embedding generation failed for {ticket_id}: {str(e)}"
            )
            return

        try:
            result = self.chroma.query(ticket_text)
        except Exception as e:
            logger.error(f"[Triage] ChromaDB query failed for {ticket_id}: {str(e)}")
            return

        # if not result["ids"][0]:
        #     self._classify_new(ticket, embedding)
        #     return

        # best_match = result["metadatas"][0][0]
        # similarity = 1 - result["distances"][0][0]  # Convert distance to similarity
        if not result:
            self._classify_new(ticket, embedding)
            return

        best_match = result[0]
        similarity = 1 - best_match["distance"]  # distance -> similarity
        priority = ticket["fields"].get("priority", {}).get("name", "Medium")
        priority_thresholds = Thresholds.get(priority)

        if similarity >= priority_thresholds["duplicate"]:
            self._classify_duplicate(ticket, best_match, similarity)
        elif similarity >= priority_thresholds["review"]:
            self._classify_review(ticket, best_match, similarity)
        else:
            self._classify_new(ticket, embedding)

    def _format_ticket_text(self, ticket: JiraTicket) -> str:
        """Generate a text representation for embedding."""
        parts = [
            f"[Priority: {ticket.priority}]",
            f"Title: {ticket.summary}",
            f"Description: {ticket.description or 'No description'}",
            f"Labels: {', '.join(ticket.labels) if ticket.labels else 'No labels'}",
        ]
        return "\n".join(parts)

    def _classify_duplicate(
        self, ticket: JiraTicket, match: Dict[str, Any], similarity: float
    ):
        """Update Jira and notify for duplicate ticket."""
        self.jira.update_ticket(
            ticket.id,
            {
                "labels": list(set(ticket.labels + ["AI_DUPLICATE"])),
                "summary": f"{ticket.summary} [DUPLICATE: {match.get('id')}]",
            },
        )
        self.notifier.send(
            to=settings.EMAIL_USER,
            subject=f"[Triage] Duplicate detected: {ticket.id}",
            body=(
                f"Ticket {ticket.id} was marked as a DUPLICATE of {match.get('id')} "
                f"(similarity: {similarity:.2f}).\n\nURL: {match.get('url')}"
            ),
        )

    def _classify_review(
        self, ticket: JiraTicket, match: Dict[str, Any], similarity: float
    ):
        """Update Jira and notify for ticket needing review."""
        self.jira.update_ticket(
            ticket.id,
            {
                "labels": list(set(ticket.labels + ["AI_REVIEW"])),
                "summary": f"{ticket.summary} [REVIEW NEEDED: {match.get('id')}]",
                "comment": {
                    "body": (
                        f"Possible relation to {match.get('id')} (similarity: {similarity:.2f}).\n"
                        f"URL: {match.get('url')}"
                    )
                },
            },
        )
        self.notifier.send(
            to=settings.EMAIL_USER,
            subject=f"[Triage] Review needed: {ticket.id}",
            body=(
                f"Ticket {ticket.id} is similar to {match.get('id')} "
                f"(similarity: {similarity:.2f}).\n\nURL: {match.get('url')}"
            ),
        )

    def _classify_new(self, ticket: JiraTicket, embedding):
        """Update Jira and ingest new ticket into ChromaDB."""
        self.jira.update_ticket(
            ticket.id,
            {
                "labels": list(set(ticket.labels + ["AI_NEW"])),
                "comment": {
                    "body": "Classified as new ticket — no similar match found."
                },
            },
        )
        try:
            self.chroma.add_ticket(
                ticket_id=ticket.id,
                embedding=embedding,
                metadata={
                    "id": ticket.id,
                    "summary": ticket.summary,
                    "priority": ticket.priority,
                    "created": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(
                f"[Triage] Failed to store ticket {ticket.id} in ChromaDB: {str(e)}"
            )
