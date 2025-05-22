from app.awr import JiraClient, ChromaDB, EmbeddingEngine
from app.utils.config import settings
from app.utils.logger import logger

class TicketTriage:
    THRESHOLDS = {
        "Critical": {"duplicate": 0.85, "review": 0.65},
        "High": {"duplicate": 0.80, "review": 0.60},
        "Medium": {"duplicate": 0.75, "review": 0.55},
        "Low": {"duplicate": 0.70, "review": 0.50}
    }

    def __init__(self):
        self.jira = JiraClient()
        self.chroma = ChromaDB()
        self.embedder = EmbeddingEngine()

    def process(self, ticket_id: str):
        # 1. Get ticket data
        ticket = self.jira.get_ticket(ticket_id)
        if not ticket:
            return

        # 2. Generate embedding
        text = f"{ticket['summary']}\n{ticket['description']}"
        embedding = self.embedder.generate(text)

        # 3. Query similar tickets
        results = self.chroma.query(embedding)
        
        # 4. Classify
        if not results['ids'][0]:
            self._handle_new(ticket)
            return

        best_score = 1 - results['distances'][0][0]  # Convert to similarity
        thresholds = self.THRESHOLDS.get(ticket['priority'], self.THRESHOLDS["Medium"])

        if best_score >= thresholds['duplicate']:
            self._tag_duplicate(ticket, results['metadatas'][0][0])
        elif best_score >= thresholds['review']:
            self._tag_review(ticket, results['metadatas'][0][0])
        else:
            self._handle_new(ticket)

    def _tag_duplicate(self, ticket, match):
        updates = {
            "labels": ticket['labels'] + ["AI_DUPLICATE"],
            "summary": f"{ticket['summary']} [DUPLICATE: {match['id']}]"
        }
        self.jira.update_ticket(ticket['id'], updates)

    def _tag_review(self, ticket, match):
        updates = {
            "labels": ticket['labels'] + ["AI_REVIEW"],
            "summary": f"{ticket['summary']} [REVIEW NEEDED: {match['id']}]"
        }
        self.jira.update_ticket(ticket['id'], updates)

    def _handle_new(self, ticket):
        self.jira.update_ticket(ticket['id'], {
            "labels": ticket['labels'] + ["AI_NEW"]
        })
        # Store in ChromaDB
        self.chroma.add_ticket(
            ticket['id'],
            self.embedder.generate(f"{ticket['summary']}\n{ticket['description']}"),
            {"priority": ticket['priority'], "type": "AWR"}
        )
