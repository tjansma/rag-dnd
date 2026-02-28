"""Gemini CLI Hook for RAG"""
import sys
import json
import os
import datetime

if os.name == 'nt':
    sys.stdin.reconfigure(encoding='utf-8')     # pyrefly: ignore
    sys.stdout.reconfigure(encoding='utf-8')    # pyrefly: ignore

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ..client import RAGClient, ClientConfig

def main():
    try:
        # On Windows/CLI, usually we can just read. 
        # json.load(sys.stdin) reads until EOF.
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            print(json.dumps({"decision": "allow"}))
            return
        
        prompt = input_data.get("prompt", "")
        
        if not prompt:
             print(json.dumps({"decision": "allow"}))
             return

        # Initialize client
        config = ClientConfig.load()
        client = RAGClient(config)
        
        # Expand query if enabled
        search_query = prompt
        if config.query_expansion and input_data.get("session_id"):
            session_guid = input_data.get("session_id")
            
            expanded_query = client.expand_query(session_guid, prompt)
            if expanded_query:
                search_query = expanded_query
        
        # Query the RAG system
        results = client.query(search_query, limit=5)
        
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
        print(json.dumps(response))
        
    except Exception as e:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
