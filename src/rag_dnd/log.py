import logging
import sys

from .config import Config

def setup_logging(config: Config) -> None:
    """
    Setup logging for the application.
    
    Args:
        config: The configuration object.
    """
    # Ensure log level is valid
    log_level = logging.getLevelNamesMapping()[config.log_level]

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console output
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_format = logging.Formatter(u"%(name)s - %(levelname)s - %(message)s")
    stdout_handler.setFormatter(stdout_format)
    logger.addHandler(stdout_handler)

    # File output
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        u"%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
