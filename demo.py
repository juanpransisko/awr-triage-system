from app.workflows import TicketTriage, EscalationManager
from app.utils.logger import logger

def run_poc():
    logger.info("Starting AWR Triage POC")
    
    triage = TicketTriage()
    for ticket_id in ["AWR-123", "AWR-456"]:
        triage.process(ticket_id)
    
    EscalationManager().check_stale()    
    logger.info("POC completed successfully")

if __name__ == "__main__":
    run_poc()
