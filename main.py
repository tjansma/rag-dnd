from pathlib import Path

from config import Config
from rag import store_document

def main():
    config = Config()

    store_document(config.session_log, config)


if __name__ == "__main__":
    main()
