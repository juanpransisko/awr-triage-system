import argparse
from awr.jira import JiraClient
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
    jira = JiraClient()
    tickets = parse_awr_xml(xml_path)

    for idx, ticket in enumerate(tickets, start=1):
        try:
            issue_key = jira.create_ticket(
                summary=ticket["summary"], description=ticket["description"]
            )
            print(f"[{idx}] Created: {issue_key}")
        except Exception as e:
            print(f"[{idx}] Failed to create: {ticket['summary']}\n{e}")


def process_single(ticket_id):
    workflow = TriageWorkflow()
    workflow.process(ticket_id)


def process_batch():
    jira = JiraClient()
    workflow = TriageWorkflow()

    issues = jira.get_open_tickets(label="AI_NEW")
    for issue in issues:
        workflow.process(issue.key)


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
