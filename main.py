"""Main entry point for the application."""
from rag.manager import store_document
import logging
import sys

from config import Config
from rag import query, delete_document


def setup_logging(config: Config) -> None:
    """
    Setup logging for the application.
    
    Args:
        config: The configuration object.
    """
    log_level = logging.getLevelNamesMapping()[config.log_level]

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console output
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    stdout_handler.setFormatter(stdout_format)
    logger.addHandler(stdout_handler)

    # File output
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)


def main():
    """Main function."""
    config = Config()
    setup_logging(config)

    store_document(config.session_log)

    chunks = query("What did Jams do?")

    for chunk in chunks:
        print(f"Chunk {chunk.id}: {chunk}")
        print("----------------------------------")

    delete_document(config.session_log)


if __name__ == "__main__":
    main()
