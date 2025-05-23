import pytest
from unittest.mock import Mock
from workflows.triage import TriageWorkflow
from awr.models import JiraTicket, Priority


@pytest.fixture
def mock_triage():
    triage = TriageWorkflow()
    triage.jira = Mock()
    triage.chroma = Mock()
    triage.embedder = Mock()
    triage.notifier = Mock()
    return triage


def test_process_new_ticket(mock_triage):
    mock_ticket = JiraTicket(
        id="TEST-1", summary="Test", description="Test", priority=Priority.MEDIUM
    )
    mock_triage.jira.get_ticket.return_value = mock_ticket
    mock_triage.chroma.query.return_value = {"ids": [[]]}  # no match

    mock_triage.process("TEST-1")  # test

    # verify
    mock_triage.jira.update_ticket.assert_called()
    assert "AI_NEW" in mock_triage.jira.update_ticket.call_args[1]["labels"]
