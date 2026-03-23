import logging
import os
import sys
import warnings

from .config import Config

class HarmlessAIWarningsFilter(logging.Filter):
    """Filters out known, harmless warnings from external AI libraries."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "flash_attn is not installed" in msg:
            return False
        if "incorrect regex pattern" in msg:
            return False
        if "`torch_dtype` is deprecated" in msg:
            return False
        return True

def setup_logging(config: Config) -> None:
    """
    Setup logging for the application.
    
    Args:
        config: The configuration object.
    """
    # Force HuggingFace to keep quiet (it attaches its own unformatted handlers)
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Suppress Python's runtime warnings for the known HF tokenizer issue (match anywhere)
    warnings.filterwarnings("ignore", message=".*incorrect regex pattern.*")
    warnings.filterwarnings("ignore", message=".*torch_dtype.*deprecated.*")
    # Also ignore generic SyntaxWarnings from transformers library parsing
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="transformers.*")
    
    ai_filter = HarmlessAIWarningsFilter()
    
    # Ensure log level is valid
    log_level = logging.getLevelNamesMapping()[config.log_level]

    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Mute noisy third-party loggers
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    # Console output
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_format = logging.Formatter(u"%(name)s - %(levelname)s - %(message)s")
    stdout_handler.setFormatter(stdout_format)
    stdout_handler.addFilter(ai_filter)
    logger.addHandler(stdout_handler)

    # File output
    if config.log_file:
        if not os.path.exists(os.path.dirname(config.log_file)):
            os.makedirs(os.path.dirname(config.log_file))
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(log_level)
        file_handler.addFilter(ai_filter)
        file_format = logging.Formatter(
            u"%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
