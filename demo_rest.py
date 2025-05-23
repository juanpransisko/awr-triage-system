import argparse
from awr.jira_rest import JiraClientREST
from awr.chroma import ChromaDB
from workflow.triage import TriageWorkflow
from awr.messaging import EmailNotifier
from xml.etree import ElementTree as ET
from config.settings import settings
from awr.logger import logger


def build_description(awr: ET.Element) -> str:
    def text(field):
        return awr.findtext(field) or "N/A"

    return f"""\
        { text('JIRA_AWR_Description') }

        AWR Document Ref: { text('AWR_Document_Reference') }
        Version: { text('AWR_Document_Version') }

        Short Work Desc:
        {text('AWR_DOC_Short_Work_Desc')}

        Customer Request Summary:
        {text('AWR_DOC_CUST_REQ_Summary')}

        Customer Request Details:
        {text('AWR_DOC_CUST_REQ_Details')}

        Business Solution:
        {text('AWR_DOC_Business_Solution')}

        Wiki:
        {text('WIKI_PAGE_URL')} - {text('WIKI_PAGE_Heading')}
        {text('WIKI_PAGE_Details')}
    """


def parse_awr_xml(xml_path: str) -> list[dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    tickets = []

    for awr in root.findall("AWRData"):
        tickets.append(
            {
                "summary": awr.findtext("JIRA_AWR_Title"),
                "description": build_description(awr),
            }
        )
    return tickets


def load_dummy_data_to_jira(xml_path: str):
    jira = JiraClientREST()
    tickets = parse_awr_xml(xml_path)

    for idx, ticket in enumerate(tickets, start=1):
        try:
            issue_key = jira.create_ticket(
                summary=ticket["summary"], description=ticket["description"]
            )
            if issue_key:
                logger.info(f"[{idx}] Created ticket {issue_key}")
                # Optionally add a comment or update
                jira.add_comment(issue_key, "Ticket auto-created from XML load.")
                jira.update_ticket(issue_key, fields={"labels": ["auto-loaded"]})
            else:
                logger.error(f"[{idx}] Failed to create ticket: {ticket['summary']}")
        except Exception as e:
            logger.exception(f"[{idx}] Exception while creating ticket: {e}")


def process_single(ticket_id):
    workflow = TriageWorkflow()
    workflow.process(ticket_id)


def process_batch():
    jira = JiraClientREST()
    workflow = TriageWorkflow()

    try:
        issues = jira.get_open_tickets(label="AI_NEW")
    except Exception as e:
        logger.error(f"Failed to retrieve open tickets: {e}")
        return

    for issue in issues:
        issue_key = issue.get("key")
        if not issue_key:
            logger.warning("Skipping issue with missing key")
            continue
        try:
            workflow.process(issue_key)
            logger.info(f"Processed ticket {issue_key}")
        except Exception as e:
            logger.error(f"Failed to process ticket {issue_key}: {e}")


def send_email(to, subject, body):
    notifier = EmailNotifier()
    notifier.send(to=to, subject=subject, body=body)


def main():
    parser = argparse.ArgumentParser(description="AWR Demo Runner")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["load-dummy", "process-single", "process-batch", "send-email"],
    )
    parser.add_argument("--xml-path", help="Path to dummy XML data")
    parser.add_argument("--ticket-id", help="Jira ticket ID to process")
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body")

    args = parser.parse_args()

    if args.mode == "load-dummy":
        if not args.xml_path:
            raise ValueError("Missing --xml-path for load-dummy")
        load_dummy_data_to_jira(args.xml_path)

    elif args.mode == "process-single":
        if not args.ticket_id:
            raise ValueError("Missing --ticket-id for process-single")
        process_single(args.ticket_id)

    elif args.mode == "process-batch":
        process_batch()

    elif args.mode == "send-email":
        if not all([args.to, args.subject, args.body]):
            raise ValueError("Missing --to, --subject or --body for send-email")
        send_email(args.to, args.subject, args.body)


if __name__ == "__main__":
    main()
