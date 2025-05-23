from datetime import datetime, timedelta
from core import JiraClient, EmailNotifier
from config.settings import Settings
from core.logger import logger


class EscalationWorkflow:
    def __init__(self):
        self.jira = JiraClient()
        self.notifier = EmailNotifier()

    def check_stale(self):
        cutoff = datetime.now() - timedelta(hours=Settings.ESCALATION_HOURS)
        jql = f'labels = AI_REVIEW AND updated < "{cutoff.strftime("%Y-%m-%d %H:%M")}"'

        try:
            issues = self.jira.client.search_issues(jql)
            for issue in issues:
                self._escalate(issue)
        except Exception as e:
            logger.error(f"Escalation failed: {str(e)}")

    def _escalate(self, issue):
        self.jira.update_ticket(
            issue.key,
            labels=[l for l in issue.fields.labels if l != "AI_REVIEW"] + ["ESCALATED"],
            comment=f"Auto-escalated after {Settings.ESCALATION_HOURS}h inactivity",
        )
        self.notifier.send(
            to="managers@company.com",
            subject=f"Escalated: {issue.key}",
            body=f"Ticket {issue.key} requires attention",
        )
