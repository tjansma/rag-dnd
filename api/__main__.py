import sys
import os

# Fix for Windows console encoding (UnicodeEncodeError)
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')    # pyrefly: ignore
    sys.stderr.reconfigure(encoding='utf-8')    # pyrefly: ignore

from config import Config
from log import setup_logging

config = Config()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app",
                host=config.api_ip,
                port=config.api_port,
                reload=config.api_auto_reload,
                log_level=config.log_level.lower())
