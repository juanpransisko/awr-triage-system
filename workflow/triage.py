from awr.jira import JiraClient
from awr.chroma import ChromaDB
from awr.embedding import EmbeddingGenerator
from awr.messaging import EmailNotifier
from awr.models import JiraTicket
from awr.logger import logger
from config.thresholds import Thresholds
from typing import Dict, Any


class TriageWorkflow:
    def __init__(self):
        self.jira = JiraClient()
        self.chroma = ChromaDB()
        self.embedder = EmbeddingGenerator()
        self.notifier = EmailNotifier()

    def process(self, ticket_id: str):

        ticket = self.jira.get_ticket(ticket_id)
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return

        text = self._generate_ticket_text(ticket)
        try:
            embedding = self.embedder.generate(text)
        except Exception as e:
            logger.error(f"Embedding generation failed for {ticket_id}: {str(e)}")
            return

        # Query and classify tickets
        results = self.chroma.query(text)
        if not results["ids"][0]:
            self._handle_new(ticket, embedding)
            return

        best_match = results["metadatas"][0][0]
        similarity = 1 - results["distances"][0][0]  # similarity score
        thresholds = Thresholds.get(ticket.priority)

        if similarity >= thresholds["duplicate"]:
            self._handle_duplicate(ticket, best_match, similarity)
        elif similarity >= thresholds["review"]:
            self._handle_review(ticket, best_match, similarity)
        else:
            self._handle_new(ticket, embedding)

    def _generate_ticket_text(self, ticket: JiraTicket) -> str:
        """text to be included in ticket, same formating"""
        components = [
            f"[Priority: {ticket.priority}]",
            f"Title: {ticket.summary}",
            f"Description: {ticket.description or 'No description'}",
            f"Labels: {', '.join(ticket.labels) if ticket.labels else 'No labels'}",
        ]
        return "\n".join(filter(None, components))

    def _handle_duplicate(
        self, ticket: JiraTicket, match: Dict[str, Any], similarity: float
    ):
        """for tickets flagged by system to be duplicate"""
        updates = {
            "labels": list(set(ticket.labels + ["AI_DUPLICATE"])),
            "summary": f"{ticket.summary} [DUPLICATE: {match['id']}]",
        }
        self.jira.update_ticket(ticket.id, updates)
        self.notifier.send(
            to="team@company.com",
            subject=f"Duplicate detected: {ticket.id}",
            body=f"Duplicate of {match['id']} with similarity {similarity:.2f}",
        )

    def _handle_review(
        self, ticket: JiraTicket, match: Dict[str, Any], similarity: float
    ):
        """for tickets that might be of similar nature, similarity high"""
        updates = {
            "labels": list(set(ticket.labels + ["AI_REVIEW"])),
            "summary": f"{ticket.summary} [REVIEW NEEDED: {match['id']}]",
            "comment": {
                "body": f"Potential relation to {match['id']} (similarity: {similarity:.2f})\n"
                f"Original title: {match['summary']}"
            },
        }
        self.jira.update_ticket(ticket.id, updates)
        self.notifier.send(
            to="team@company.com",
            subject=f"Review needed for {ticket.id}",
            body=f"Potential relation to {match['id']} (similarity: {similarity:.2f})",
        )

    def _handle_new(self, ticket: JiraTicket, embedding):
        """entirely new tickets"""
        updates = {
            "labels": list(set(ticket.labels + ["AI_NEW"])),
            "comment": {"body": "Classified as new ticket - no similar tickets found"},
        }
        self.jira.update_ticket(ticket.id, updates)

        # Store for future comparisons
        try:
            self.chroma.add_ticket(
                ticket_id=ticket.id,
                embedding=embedding,
                metadata={
                    "summary": ticket.summary,
                    "priority": ticket.priority,
                    "created": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to store ticket {ticket.id} in ChromaDB: {str(e)}")
