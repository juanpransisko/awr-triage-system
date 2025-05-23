import logging
import logging.config
import os
import sys
from pathlib import Path


def setup_logging():
    log_dir = Path(os.getenv("LOG_PATH", "logs")).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / "awr_triage.log"  # default

    # absolute config file path
    config_path = Path("config/logging_config.ini").resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Logging config not found: {config_path}")

    logging.config.fileConfig(
        fname=config_path,
        defaults={"logfilename": str(log_file_path)},
        disable_existing_loggers=False,
    )

    return logging.getLogger("awr_triage")


logger = setup_logging()
logger.info("Logger initialized.")
