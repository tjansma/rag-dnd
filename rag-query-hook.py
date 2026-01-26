"""Gemini CLI Hook for RAG"""
import sys
import json
import os
import datetime

if os.name == 'nt':
    sys.stdin.reconfigure(encoding='utf-8')     # pyrefly: ignore
    sys.stdout.reconfigure(encoding='utf-8')    # pyrefly: ignore

DEBUG = False

# DEBUG LOGGING - use a very simple path
debug_file = r"C:\Development\src\_AI\rag_dnd\hook_debug.log"

def log_debug(msg):
    if DEBUG:
        try:
            with open(debug_file, "a") as f:
                f.write(f"[{datetime.datetime.now()}] {msg}\n")
        except:
            pass

# Log immediately
log_debug("--- Hook Script Started (Windows Safe) ---")

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client_config import ClientConfig
from rag_client import RAGClient

def main():
    try:
        # On Windows/CLI, usually we can just read. 
        # json.load(sys.stdin) reads until EOF.
        log_debug("Reading stdin via json.load...")
        
        try:
            input_data = json.load(sys.stdin)
            log_debug("JSON loaded successfully")
        except json.JSONDecodeError:
            log_debug("Failed to decode JSON from stdin")
            print(json.dumps({"decision": "allow"}))
            return
        
        prompt = input_data.get("prompt", "")
        log_debug(f"Prompt: '{prompt}'")
        
        if not prompt:
             print(json.dumps({"decision": "allow"}))
             return

        # Initialize client
        config = ClientConfig()
        client = RAGClient(config)
        
        # Expand query if enabled
        search_query = prompt
        if config.query_expansion and input_data.get("session_id"):
            log_debug("Expanding query...")
            session_guid = input_data.get("session_id")
            
            expanded_query = client.expand_query(session_guid, prompt)
            if expanded_query:
                search_query = expanded_query
            else:
                log_debug("Query expansion failed")
        
        # Query the RAG system
        log_debug("Querying RAG system...")
        results = client.query(search_query, limit=5)
        log_debug(f"Results found: {len(results)}")
        
        if not results:
             print(json.dumps({"decision": "allow"}))
             return
             
        # Format context
        context_text = "RAG KNOWLEDGE BASE:\n"
        for i, res in enumerate(results, 1):
            context_text += f"\n--- SOURCE {i}: {res.source_document} ---\n{res.text}\n"
            
        # Return response with additionalContext
        response = {
            "decision": "allow",
            "hookSpecificOutput": {
                "additionalContext": context_text
            }
        }
        log_debug("Sending response with context")
        print(json.dumps(response))
        
    except Exception as e:
        log_debug(f"CRITICAL ERROR: {str(e)}")
        import traceback
        log_debug(traceback.format_exc())
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
