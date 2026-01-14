"""Main entry point for the application."""
import sys

from config import Config
from log import setup_logging
from rag import query, delete_document, update_document, store_document


def main():
    """Main function."""
    config = Config()
    setup_logging(config)

    store_document(config.session_log)

    chunks = query("What did Jams do?")

    update_document(config.session_log)

    delete_document(config.session_log)


if __name__ == "__main__":
    main()
