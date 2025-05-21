import logging
import logging.config
import os
from pathlib import Path

def setup_logging():
    """Initialize logging configuration"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.config.fileConfig(
        "config/logging_config.ini",
        defaults={'logfilename': 'logs/awr_triage.log'},
        disable_existing_loggers=False
    )
    
    return logging.getLogger("awr_triage")

logger = setup_logging()
