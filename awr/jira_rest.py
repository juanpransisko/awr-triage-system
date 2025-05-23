import requests
import json
import time
import random
from typing import Optional, List
from config.settings import settings
from awr.logger import logger


class JiraClientREST:
    def __init__(self):
        # self.base_url = settings.JIRA_SERVER
        self.base_url = "https://devjfto.atlassian.net"
        self.auth = (settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
        self.headers = {"Content-Type": "application/json"}
        self.project_key = settings.JIRA_PROJECT_KEY
        self.approval_task_customfield = "customfield_10010"
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update(self.headers)
        self.timeout = 30  # seconds

        logger.info("Initializing JIRA REST client")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Logged in as {settings.JIRA_USERNAME}")

    def _request(self, method, endpoint, max_retries=3, backoff_factor=1, **kwargs):
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Request URL: {url}")
        if "json" in kwargs:
            logger.debug(
                f"Request JSON payload: {json.dumps(kwargs['json'], indent=2)}"
            )
        try:
            response = requests.request(
                method,
                url,
                auth=self.auth,
                headers=self.headers,
                timeout=30,
                **kwargs,
            )
            logger.debug(f"Response code: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            response.raise_for_status()
            if response.text:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def create_ticket(
        self,
        summary: str,
        description: str,
        project_key: Optional[str] = None,
        issue_type: str = "Task",
    ) -> Optional[str]:
        project_key = project_key or self.project_key
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
        }
        logger.info(
            f"Creating issue in project '{project_key}' with summary '{summary}'"
        )
        response = self._request("POST", "/rest/api/2/issue", json=payload)
        if response and "key" in response:
            logger.info(f"Issue created: {response['key']}")
            return response["key"]
        logger.error(f"Failed to create issue. Response: {response}")
        return None

    def get_ticket(self, ticket_id: str) -> Optional[dict]:
        logger.info(f"Fetching ticket {ticket_id}")
        response = self._request("GET", f"/rest/api/2/issue/{ticket_id}")
        if response:
            logger.debug(f"Ticket {ticket_id} fetched successfully")
        else:
            logger.error(f"Failed to fetch ticket {ticket_id}")
        return response

    def get_open_tickets(self, label: Optional[str] = None, max_results: int = 50):
        jql = f"project = {self.project_key} AND statusCategory != Done"
        if label:
            jql += f" AND labels = {label}"
        params = {"jql": jql, "maxResults": max_results}
        data = self._request("GET", "/rest/api/2/search", params=params)
        return data.get("issues", []) if data else []

    def update_ticket(self, ticket_id: str, fields: dict) -> bool:
        logger.info(f"Updating ticket {ticket_id} with fields: {fields}")
        payload = {"fields": fields}
        response = self._request("PUT", f"/rest/api/2/issue/{ticket_id}", json=payload)
        if response is None:  # PUT returns empty on success
            logger.info(f"Ticket {ticket_id} updated successfully")
            return True
        logger.error(f"Failed to update ticket {ticket_id}. Response: {response}")
        return False

    def create_approval_task(self, ticket_id: str) -> Optional[str]:
        logger.info(f"Creating approval task for {ticket_id}")
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"Review disputed AWR: {ticket_id}",
                "description": f"Disputed classification for {ticket_id}",
                "issuetype": {"name": "Approval Task"},
                self.approval_task_customfield: ticket_id,
            }
        }
        response = self._request("POST", "/rest/api/2/issue", json=payload)
        if response and "key" in response:
            logger.info(f"Approval task created: {response['key']}")
            return response["key"]
        logger.error(f"Failed to create approval task. Response: {response}")
        return None

    def search_tickets(self, jql: str, max_results: int = 100) -> List[dict]:
        logger.info(f"Searching tickets with JQL: {jql}")
        params = {"jql": jql, "maxResults": max_results}
        response = self._request("GET", "/rest/api/2/search", params=params)
        if response and "issues" in response:
            logger.info(f"Found {len(response['issues'])} issues")
            return response["issues"]
        logger.error(f"JQL search failed. Response: {response}")
        return []

    def add_comment(self, ticket_id: str, comment: str) -> bool:
        logger.info(f"Adding comment to ticket {ticket_id}")
        payload = {"body": comment}
        response = self._request(
            "POST", f"/rest/api/2/issue/{ticket_id}/comment", json=payload
        )
        if response and "id" in response:
            logger.info(f"Comment added with ID {response['id']}")
            return True
        logger.error(f"Failed to add comment. Response: {response}")
        return False
