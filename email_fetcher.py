"""Email fetcher module — fetches unread emails from IMAP server."""

import imaplib
import re
import email
from email.header import decode_header
from html import unescape
from typing import List, Dict
import logging
from config import Config

logger = logging.getLogger(__name__)


class EmailFetcher:
    """Fetch unread emails from Gmail or Outlook via IMAP."""

    def __init__(self, email_address: str, password: str, imap_server: str, imap_port: int):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port

    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server."""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.password)
            logger.info(f"Connected to {self.imap_server} as {self.email_address}")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    def fetch_unread_emails(self, max_emails: int = 10) -> List[Dict[str, str]]:
        """Fetch unread emails and return subject + body."""
        try:
            mail = self.connect()
            mail.select("INBOX")

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()

            if not email_ids:
                logger.info("No unread emails found")
                return []

            # Limit to max_emails
            email_ids = email_ids[-max_emails:]

            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                subject = self._decode_header(msg.get("Subject", "No Subject"))
                sender = self._decode_header(msg.get("From", "Unknown"))

                # Extract body
                body = self._extract_body(msg)

                emails.append({
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                })

                logger.info(f"Fetched email: {subject}")

            mail.close()
            mail.logout()
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    @staticmethod
    def _decode_header(value: str) -> str:
        """Decode a MIME-encoded email header to plain text."""
        decoded_parts = decode_header(value)
        decoded_text = []

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_text.append(part.decode(charset or "utf-8", errors="ignore"))
                except Exception:
                    decoded_text.append(part.decode("utf-8", errors="ignore"))
            else:
                decoded_text.append(str(part))

        return "".join(decoded_text).strip()

    @staticmethod
    def _extract_body(msg) -> str:
        """Extract the best available text body from an email message."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = part.get_content_disposition() or ""
                content_type = part.get_content_type()

                if content_disposition == "attachment":
                    continue

                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
                if content_type == "text/html" and not body:
                    html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    body = EmailFetcher._html_to_text(html_body)
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                if content_type == "text/plain":
                    body = payload.decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    body = EmailFetcher._html_to_text(payload.decode("utf-8", errors="ignore"))

        return body.strip()

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert minimal HTML to plain text."""
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"<.*?>", "", text)
        text = unescape(text)
        return text.strip()

    @staticmethod
    def format_for_summary(emails: List[Dict[str, str]]) -> str:
        """Format emails into a string for summarization."""
        if not emails:
            return "No unread emails."

        formatted = "Unread Emails:\n\n"
        for i, email_data in enumerate(emails, 1):
            formatted += f"{i}. From: {email_data['sender']}\n"
            formatted += f"   Subject: {email_data['subject']}\n"
            formatted += f"   Body: {email_data['body'][:200]}...\n\n"

        return formatted


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = EmailFetcher(
        Config.EMAIL_ADDRESS,
        Config.EMAIL_PASSWORD,
        Config.EMAIL_IMAP_SERVER,
        Config.EMAIL_IMAP_PORT,
    )
    emails = fetcher.fetch_unread_emails(max_emails=5)
    print(f"Fetched {len(emails)} emails")
    print(fetcher.format_for_summary(emails))
