from jira import JIRA
from jira.resources import Issue
from jira.exceptions import JIRAError
from config.settings import settings
from awr.logger import logger
import json
from typing import Optional, List, Any


class JiraClient:
    project_key = "CSP"
    approval_task_customfield = "customfield_10010"  # for ticket approvals

    def __init__(self):
        logger.info("Initializing JIRA client")
        self.project_key = settings.JIRA_PROJECT_KEY
        try:
            self.client = JIRA(
                server=settings.JIRA_SERVER,
                basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN),
                timeout=30,
            )
            logger.debug(f"Connected to JIRA at {settings.JIRA_SERVER}")
            logger.info(f"Logged in as {settings.JIRA_USERNAME}")
        except JIRAError as e:
            logger.critical(f"JIRA connection failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected connection error: {str(e)}", exc_info=True)
            raise

    def create_ticket(self, summary, description, project_key=None, issue_type="Task"):
        project_key = self.project_key
        logger.info(f"Using project key {project_key}")

        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

        try:
            logger.info(
                f"Creating issue in project '{project_key}' with summary '{summary}'"
            )
            logger.debug(f"Issue payload:\n{json.dumps(issue_dict, indent=2)}")

            new_issue = self.client.create_issue(fields=issue_dict)

            if not new_issue:
                logger.error("create_issue returned None unexpectedly.")
                return None

            logger.info(f"Issue created: {new_issue.key}")
            return new_issue.key

        except JIRAError as e:
            logger.error(f"JIRAError: {e.status_code} - {getattr(e, 'text', str(e))}")
            if hasattr(e, "response"):
                logger.error(f"JIRA response: {e.response.text}")
            logger.debug(f"Failed payload:\n{json.dumps(issue_dict, indent=2)}")
            return None

        except Exception as e:
            logger.exception("Unexpected error creating issue")
            return None

    def get_ticket(self, ticket_id: str) -> Optional[Issue]:
        logger.info(f"Fetching ticket {ticket_id}")
        try:
            ticket = self.client.issue(ticket_id)
            logger.debug(
                f"Retrieved ticket fields: {list(ticket.raw['fields'].keys())}"
            )
            # Log limited info to avoid huge dumps
            summary = (
                ticket.fields.summary if hasattr(ticket.fields, "summary") else "N/A"
            )
            logger.debug(f"Ticket {ticket_id} summary: {summary}")
            return ticket
        except JIRAError as e:
            logger.error(
                f"Failed to fetch {ticket_id}: {e.text if hasattr(e, 'text') else str(e)}"
            )
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching ticket: {str(e)}")
            raise

    def update_ticket(self, ticket: Issue, **fields) -> bool:
        changes = "\n".join([f"{k}: {v}" for k, v in fields.items()])
        logger.info(f"Updating {ticket.key} with:\n{changes}")

        try:
            ticket.update(fields=fields)
            logger.debug(f"Update successful for {ticket.key}")
            return True
        except JIRAError as e:
            logger.error(f"Update failed: {e.text if hasattr(e, 'text') else str(e)}")
            logger.debug(f"Failed fields: {fields}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected update error: {str(e)}")
            raise

    def create_approval_task(self, ticket_id: str) -> Optional[Issue]:
        logger.info(f"Creating approval task for {ticket_id}")
        issue_dict = {
            "project": {"key": self.project_key},
            "summary": f"Review disputed AWR: {ticket_id}",
            "description": f"Disputed classification for {ticket_id}",
            "issuetype": {"name": "Approval Task"},
            self.approval_task_customfield: ticket_id,
        }
        try:
            task = self.client.create_issue(fields=issue_dict)
            logger.info(f"Created approval task {task.key}")
            logger.debug(f"Task fields: {task.raw.get('fields', {})}")
            return task
        except JIRAError as e:
            logger.error(
                f"Task creation failed: {e.text if hasattr(e, 'text') else str(e)}"
            )
            logger.debug(f"Attempted payload: {json.dumps(issue_dict, indent=2)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected task creation error: {str(e)}")
            raise

    def search_tickets(self, jql: str, max_results: int = 100) -> List[Issue]:
        logger.info(f"Executing JQL: {jql}")
        try:
            issues = self.client.search_issues(jql, maxResults=max_results)
            logger.debug(f"Found {len(issues)} tickets")
            for i, issue in enumerate(issues[:3]):
                logger.debug(f"Result {i+1}: {issue.key} - {issue.fields.summary}")
            return issues
        except JIRAError as e:
            logger.error(
                f"JQL search failed: {e.text if hasattr(e, 'text') else str(e)}"
            )
            return []
        except Exception as e:
            logger.exception(f"Unexpected search error: {str(e)}")
            raise

    def add_comment(self, ticket_id: str, comment: str) -> bool:
        logger.info(f"Adding comment to {ticket_id}")
        logger.debug(f"Comment content:\n{comment}")
        try:
            self.client.add_comment(ticket_id, comment)
            logger.debug("Comment added successfully")
            return True
        except JIRAError as e:
            logger.error(f"Comment failed: {e.text if hasattr(e, 'text') else str(e)}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected comment error: {str(e)}")
            raise
