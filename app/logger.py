import logging
import os
from typing import Dict

class CustomFormatter(logging.Formatter):
    """Custom formatter for colored console output."""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[34m"
    white = "\x1b[37m"
    underline = "\x1b[4m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(name)12s - %(levelname)-8s | %(message)-2s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class LoggerFactory:
    """Singleton factory for creating and managing loggers."""
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerFactory, cls).__new__(cls)
            # Clear root logger handlers to prevent double logging
            logging.getLogger('').handlers.clear()
            # Suppress noisy third-party loggers
            for lib in ['paho.mqtt', 'numpy', 'asyncio']:
                logging.getLogger(lib).setLevel(logging.WARNING)
        return cls._instance

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            logger.propagate = False  # Prevent propagation to root logger

            # Add console handler if none exist
            if not logger.handlers:
                ch = logging.StreamHandler()
                ch.setFormatter(CustomFormatter())
                logger.addHandler(ch)

                # Add file handler for persistent logging
                log_file = os.path.join(os.path.dirname(__file__), "..", "eagleeye.log")
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ))
                logger.addHandler(fh)

            self._loggers[name] = logger
        return self._loggers[name]

# Global factory instance
logger_factory = LoggerFactory()

def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger by name."""
    return logger_factory.get_logger(name)