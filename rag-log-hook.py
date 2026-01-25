import sys
import json
import logging

from client_config import ClientConfig
from rag_client import transcribe_turn

# Setup logging for errors
logging.basicConfig(
    filename='rag_log_hook_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # 1. Read Input
        raw_input = sys.stdin.read()
        if not raw_input:
            print(json.dumps({"decision": "continue"}))
            return

        # 2. Parse JSON
        try:
            input_data = json.loads(raw_input)
        except json.JSONDecodeError:
            logging.error("Invalid JSON received")
            print(json.dumps({"decision": "continue"}))
            return

        # 3. Extract & Transcribe Data
        transcribe_turn(input_data.get("session_id"),
                        input_data.get("prompt"),
                        input_data.get("prompt_response"))

        # 4. Return success
        print(json.dumps({"decision": "continue"}))

    except Exception as e:
        # Catch-all to prevent CLI hanging
        logging.critical(f"Critical Hook Error: {e}")
        print(json.dumps({"decision": "continue"}))

if __name__ == "__main__":
    main()
