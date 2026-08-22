"""Slack sender module — posts messages to Slack via webhook."""

import logging
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


class SlackSender:
    """Send messages to Slack via Incoming Webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(
        self,
        text: str,
        title: Optional[str] = None,
        blocks: Optional[list] = None,
    ) -> bool:
        """Send a plain-text/Markdown message to Slack."""

        try:
            message = f"*{title}*\n\n{text}" if title else text

            payload = {
                "text": message
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=20,
            )

            if response.status_code != 200:
                logger.error(
                    f"Slack Error {response.status_code}: {response.text}"
                )
                return False

            logger.info("Message sent to Slack successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send message to Slack: {e}")
            return False

    @staticmethod
    def format_email_summary(summary: str, email_count: int) -> list:
        """
        Keep compatibility with scheduler.py.

        The scheduler still calls this method, but the Slack sender
        intentionally ignores blocks and sends a normal text message.
        """

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*🤖 AutoPilot Email Summary*\n"
                        f"*Unread Emails:* {email_count}\n\n"
                        f"{summary}"
                    ),
                },
            }
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sender = SlackSender(Config.SLACK_WEBHOOK_URL)

    sender.send_message(
        text="This is a test message from AutoPilot.",
        title="🤖 AutoPilot Test",
    )