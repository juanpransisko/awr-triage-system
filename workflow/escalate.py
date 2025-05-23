from datetime import datetime, timedelta
from awr.jira import JiraClient
from awr.messaging import EmailNotifier
from config.settings import settings
from awr.logger import logger


class EscalationWorkflow:
    def __init__(self):
        self.jira = JiraClient()
        self.notifier = EmailNotifier()

    def run(self):
        """entry point for the escalation check."""
        try:
            stale_issues = self._get_stale_issues()
            for issue in stale_issues:
                self._escalate_issue(issue)
        except Exception as e:
            logger.error(f"[Escalation] Workflow failed: {str(e)}")

    def _get_stale_issues(self):
        """Finds tickets labeled 'AI_REVIEW' and not updated within the escalation window."""
        cutoff_time = datetime.now() - timedelta(hours=settings.ESCALATION_HOURS)
        cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M")
        jql = f'labels = AI_REVIEW AND updated < "{cutoff_str}"'

        logger.info(f"[Escalation] Executing JQL: {jql}")
        issues = self.jira.search_tickets(jql)
        logger.info(f"[Escalation] Found {len(issues)} stale tickets")
        return issues

    def _escalate_issue(self, issue):
        """Updates the ticket and sends notification."""
        new_labels = [label for label in issue.fields.labels if label != "AI_REVIEW"]
        new_labels.append("ESCALATED")

        logger.info(f"[Escalation] Escalating issue {issue.key}")

        self.jira.update_ticket(
            issue,
            labels=new_labels,
            comment=f"Auto-escalated after {settings.ESCALATION_HOURS}h inactivity",
        )

        self.notifier.send(
            to=settings.EMAIL_USER,
            subject=f"[Escalation] {issue.key} needs attention",
            body=f"The ticket {issue.key} has been escalated after {settings.ESCALATION_HOURS} hours of inactivity.",
        )
