"""Configuration management for AutoPilot."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Load configuration from .env file."""

    # Email (IMAP)
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
    EMAIL_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", 993))

    # Slack
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    # Ollama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:cloud")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Schedule
    SCHEDULE_CRON = os.getenv("SCHEDULE_CRON", "0 9 * * 1")  # Default: Monday 9 AM
    SCHEDULE_ENABLED = os.getenv("SCHEDULE_ENABLED", "true").strip().lower() == "true"


    # Email Processing
    MAX_EMAILS = int(os.getenv("MAX_EMAILS", "5"))


    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "autopilot.log")

    @staticmethod
    def validate():
        """Validate required configuration."""
        if not Config.EMAIL_ADDRESS:
            raise ValueError("EMAIL_ADDRESS not set in .env")
        if not Config.EMAIL_PASSWORD:
            raise ValueError("EMAIL_PASSWORD not set in .env")
        if not Config.SLACK_WEBHOOK_URL:
            raise ValueError("SLACK_WEBHOOK_URL not set in .env")
        if not Config.OLLAMA_HOST:
            raise ValueError("OLLAMA_HOST not set in .env")
        if not Config.SCHEDULE_CRON:
            raise ValueError("SCHEDULE_CRON not set in .env")
        if not Config.LOG_FILE:
            raise ValueError("LOG_FILE not set in .env")

        if not isinstance(Config.EMAIL_IMAP_PORT, int) or Config.EMAIL_IMAP_PORT <= 0:
            raise ValueError("EMAIL_IMAP_PORT must be a valid port number")

        return True
