from datetime import datetime
import logging
from pathlib import Path
import sqlite3
from typing import Optional
import subprocess

from .config import ClientConfig


def init_db(db_path):
    """
    Initialize the SQLite database with normalized schema.
    
    Args:
        db_path (str): The path to the database file.
    
    Returns:
        sqlite3.Connection: The database connection.
    """
    try:
        # Ensure data dir exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Table 1: Sessions (Stores the GUID once)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE,
                first_seen TEXT
            )
        ''')

        # Table 2: Turns (References session via INT, stores full turn)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TEXT,
                user_prompt TEXT,
                ai_response TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        conn.commit()
        return conn
    except Exception as e:
        logging.error(f"Failed to initialize DB: {e}")
        return None


def get_or_create_session(session_guid: str, cursor: sqlite3.Cursor | None=None) -> int:
    """
    Resolve session GUID to integer ID.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor.
        session_guid (str): The session GUID.
    
    Returns:
        int: The session ID.
    """
    if cursor is None:
        conn = init_db(ClientConfig.load().transcript_database)
        if conn is None:
            logging.error("Failed to initialize DB")
            raise Exception("Failed to initialize DB")
        cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM sessions WHERE guid = ?", (session_guid,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    else:
        now = datetime.now().isoformat()
        cursor.execute("INSERT INTO sessions (guid, first_seen) VALUES (?, ?)", (session_guid, now))

        if cursor.lastrowid is None:
            logging.error("Failed to create session")
            raise Exception("Failed to create session")

        return cursor.lastrowid

def get_session_info(cursor: sqlite3.Cursor, session_id: int) -> dict[str, str] | None:
    """
    Resolve session ID to session info.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor.
        session_id (int): The session ID.
    
    Returns:
        dict[str, str] | None: The session info.
    """
    cursor.execute("SELECT guid, first_seen FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    
    if row:
        return {"guid": row[0], "first_seen": row[1]}
    else:
        return None

def transcribe_turn(session_guid: str, user_prompt: str, ai_response: str) -> None:
    """
    Transcribe a turn of the conversation into the transcript database.

    Args:
        session_id (str): The GUID of the session.
        user_prompt (str): The user's prompt.
        ai_response (str): The AI's response.

    Returns:
        None
    """
    prompt = user_prompt.strip()
    response = ai_response.strip()
    timestamp = datetime.now().isoformat()

    # 4. Store in SQLite (Normalized)
    if prompt and response:
        conn = init_db(ClientConfig.load().transcript_database)
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get integer ID for session
                session_id = get_or_create_session(session_guid, cursor)
                
                # Insert Turn (Single row per Q&A pair)
                cursor.execute(
                        "INSERT INTO turns (session_id, timestamp, user_prompt, ai_response) VALUES (?, ?, ?, ?)",
                        (session_id, timestamp, prompt, response)
                    )
                conn.commit()
            except Exception as e:
                logging.error(f"DB Write Error: {e}")
            finally:
                conn.close()

def list_sessions() -> list[dict[str, str]]:
    """
    List all sessions.
    
    Returns:
        list[str]: A list of session GUIDs.
    """
    try:
        conn = init_db(ClientConfig.load().transcript_database)
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, guid, first_seen FROM sessions ORDER BY first_seen ASC")
                rows = cursor.fetchall()
                return [{"id": row[0], "guid": row[1], "first_seen": row[2]} for row in rows]
            except Exception as e:
                logging.error(f"DB Read Error: {e}")
                return []
            finally:
                conn.close()
    except Exception as e:
        logging.error(f"Failed to list sessions: {e}")
        return []

    return []

def get_session_transcript(session_id: int) -> list[dict[str, str]]:
    """
    Get transcript of specific session.
    
    Args:
        session_id (int): The ID of the session.
    
    Returns:
        list[dict[str, str]]: A list of turns in the session.
    """
    try:
        conn = init_db(ClientConfig.load().transcript_database)
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, timestamp, user_prompt, ai_response FROM turns WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
                rows = cursor.fetchall()
                return [{"id": row[0], "timestamp": row[1], "user_prompt": row[2], "ai_response": row[3]} for row in rows]
            except Exception as e:
                logging.error(f"DB Read Error: {e}")
                return []
            finally:
                conn.close()
    except Exception as e:
        logging.error(f"Failed to get session transcript: {e}")
        return []

    return []

def session_to_markdown(session_id: int) -> str:
    """
    Convert session transcript to markdown.
    
    Args:
        session_id (int): The ID of the session.
    
    Returns:
        str: The session transcript in markdown format.
    """
    db_conn = init_db(ClientConfig.load().transcript_database)
    if db_conn is None:
        raise Exception("Failed to initialize database")

    session_info = get_session_info(db_conn.cursor(), session_id)
    if session_info is None:
        raise Exception("Session not found")
    transcript = get_session_transcript(session_id)
    
    markdown_lines = [f"# Session {session_info['guid']} - {session_info['first_seen']}"]
    for index, turn in enumerate(transcript):
        markdown_lines.append(f"## Turn {index + 1}")
        markdown_lines.append(f"- Player: {turn['user_prompt']}")
        markdown_lines.append(f"- DM: {turn['ai_response']}")
        markdown_lines.append("---")

    return "\n\n".join(markdown_lines)

def transcript_summarize(id: int, 
                      prompt_file: str = ClientConfig.load().summary_prompt_file, 
                      output: Optional[str] =  None, 
                      append: bool = False) -> str:
    """
    Generate a summary for a session using the Gemini CLI.

    Args:
        id (int): The ID of the session.
        prompt_file (str, optional): The path to the summary prompt file. Defaults to ClientConfig.summary_prompt_file.
        output (Optional[str], optional): The path to the output file. Defaults to None.
        append (bool, optional): Whether to append to the output file. Defaults to False.

    Returns:
        str: The summary text.
    """
    # 1. Load Prompt
    prompt_path = Path(prompt_file).resolve()
    if not prompt_path.exists():
         raise Exception(f"Prompt file not found at {prompt_path}")
    
    prompt_text = prompt_path.read_text(encoding="utf-8")

    # 2. Load Transcript
    transcript_md = session_to_markdown(id)

    # 3. Combine
    full_payload = f"{prompt_text}\n\n--- TRANSCRIPT ---\n\n{transcript_md}"

    # 4. Call Gemini
    logging.info(f"Sending {len(full_payload)} chars to Gemini CLI...")
    
    trigger_msg = "Please follow the instructions provided in the input data to generate the logbook entry."
    
    result = subprocess.run(
            ["gemini", trigger_msg],
            input=full_payload,
            text=True,
            capture_output=True,
            encoding="utf-8",
            shell=True 
        )

    output_text = result.stdout

    if result.returncode != 0:
        logging.error(f"Gemini CLI Error:\n{result.stderr}")
    else:
        logging.debug(f"Gemini Output:\n{output_text}")
            
    # Handle Output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_text)
        logging.info(f"Saved to {output}")
            
    if append:
        logbook_path = Path(ClientConfig.load().logbook_path).resolve()
        if logbook_path.exists():
            with open(logbook_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + output_text)
            logging.info(f"Appended to {logbook_path}")
        else:
            logging.error(f"Logbook not found at {logbook_path}")

    return output_text

def get_last_turn(session_id: int) -> dict[str, str] | None:
    """
    Get the last turn of a session.
    
    Args:
        session_id (int): The ID of the session.
    
    Returns:
        dict[str, str] | None: The last turn of the session, or None if not found.
    """
    try:
        conn = init_db(ClientConfig.load().transcript_database)
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, timestamp, user_prompt, ai_response FROM turns WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1", (session_id,))
                row = cursor.fetchone()
                return {"id": row[0], "timestamp": row[1], "user_prompt": row[2], "ai_response": row[3]} if row else None
            except Exception as e:
                logging.error(f"DB Read Error: {e}")
                return None
            finally:
                conn.close()
    except Exception as e:
        logging.error(f"Failed to get last turn: {e}")
        return None
