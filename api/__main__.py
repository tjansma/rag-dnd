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
