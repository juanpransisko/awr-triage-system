from jira import JIRA
from jira.exceptions import JIRAError
from config.settings import Settings
from awr.logger import logger
import json
from typing import Optional, Dict, Any


class JiraClient:
    def __init__(self):
        logger.info("Initializing JIRA client")
        try:
            self.client = JIRA(
                server=Settings.JIRA_SERVER,
                basic_auth=(Settings.JIRA_USER, Settings.JIRA_TOKEN),
                timeout=30,
            )
            logger.debug(f"Connected to JIRA at {Settings.JIRA_SERVER}")
            logger.info(f"Logged in as {Settings.JIRA_USER}")
        except JIRAError as e:
            logger.critical(f"JIRA connection failed: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected connection error: {str(e)}", exc_info=True)
            raise

    def get_ticket(self, ticket_id: str) -> Optional[Any]:
        logger.info(f"Fetching ticket {ticket_id}")
        try:
            ticket = self.client.issue(ticket_id)
            logger.debug(
                f"Retrieved ticket fields: {list(ticket.raw['fields'].keys())}"
            )
            logger.verbose(
                f"Ticket {ticket_id} details:\n{json.dumps(ticket.raw, indent=2, default=str)}"
            )
            return ticket
        except JIRAError as e:
            logger.error(
                f"Failed to fetch {ticket_id}: {e.text if hasattr(e, 'text') else str(e)}"
            )
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching ticket: {str(e)}")
            raise

    def update_ticket(self, ticket, **fields) -> bool:
        changes = "\n".join([f"{k}: {v}" for k, v in fields.items()])
        logger.info(f"Updating {ticket.key} with:\n{changes}")

        try:
            before = json.dumps(ticket.raw, default=str)
            ticket.update(fields=fields)
            after = json.dumps(self.client.issue(ticket.key).raw, default=str)

            logger.debug(f"Update successful for {ticket.key}")
            logger.verbose(
                f"Change comparison for {ticket.key}:\n"
                f"BEFORE:\n{before}\n\nAFTER:\n{after}"
            )
            return True
        except JIRAError as e:
            logger.error(f"Update failed: {e.text if hasattr(e, 'text') else str(e)}")
            logger.debug(f"Failed fields: {fields}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected update error: {str(e)}")
            raise

    def create_approval_task(self, ticket_id: str) -> Optional[Any]:
        logger.info(f"Creating approval task for {ticket_id}")
        try:
            task = self.client.create_issue(
                project="OPS",
                summary=f"Review disputed AWR: {ticket_id}",
                issuetype={"name": "Approval Task"},
                description=f"Disputed classification for {ticket_id}",
                customfield_10010=ticket_id,  # Link field
            )
            logger.info(f"Created approval task {task.key}")
            logger.debug(f"Task details: {task.raw}")
            return task
        except JIRAError as e:
            logger.error(f"Task creation failed: {e.text}")
            logger.debug(
                f"Attempted payload: {json.dumps({
                'project': 'OPS',
                'summary': f'Review disputed AWR: {ticket_id}',
                'issuetype': {'name': 'Approval Task'}
            }, indent=2)}"
            )
            return None
        except Exception as e:
            logger.exception(f"Unexpected task creation error: {str(e)}")
            raise

    def search_tickets(self, jql: str, max_results: int = 100) -> list:
        """utilize JQL (jira query language) for searching tickets"""
        logger.info(f"Executing JQL: {jql}")
        try:
            issues = self.client.search_issues(jql, maxResults=max_results)
            logger.debug(f"Found {len(issues)} tickets")
            if logger.isEnabledFor(logging.DEBUG):
                for i, issue in enumerate(issues[:3]):  # Log first 3 for sample
                    logger.debug(f"Result {i+1}: {issue.key} - {issue.fields.summary}")
            return issues
        except JIRAError as e:
            logger.error(f"JQL search failed: {e.text}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected search error: {str(e)}")
            raise

    def add_comment(self, ticket_id: str, comment: str) -> bool:
        logger.info(f"Adding comment to {ticket_id}")
        logger.verbose(f"Comment content:\n{comment}")
        try:
            self.client.add_comment(ticket_id, comment)
            logger.debug("Comment added successfully")
            return True
        except JIRAError as e:
            logger.error(f"Comment failed: {e.text}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected comment error: {str(e)}")
            raise


# jira = JiraClient()
# ticket = jira.get_ticket("SCRUM-3")

# if ticket:
#    jira.update_ticket(
#        ticket, labels=["AI_PROCESSED"], summary=f"{ticket.fields.summary} [PROCESSED]"
#    )
#    jira.add_comment(ticket.key, "Automated processing complete")
