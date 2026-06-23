"""Scheduler module — APScheduler with SQLite persistence."""

import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Any, Callable, List, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc
from config import Config
from email_fetcher import EmailFetcher
from summarizer import summarize
from slack_sender import SlackSender

logger = logging.getLogger(__name__)


class SummaryHistory:
    """SQLite-backed history of email summaries."""

    DB_PATH = "autopilot_history.db"

    @staticmethod
    def init():
        """Initialize history database."""
        conn = sqlite3.connect(SummaryHistory.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email_count INTEGER,
                summary TEXT,
                status TEXT,
                error_message TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    @staticmethod
    def add(email_count: int, summary: str, status: str = "success", error_message: str = None):
        """Store a summary in history."""
        try:
            conn = sqlite3.connect(SummaryHistory.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO summaries (timestamp, email_count, summary, status, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.utcnow().isoformat(), email_count, summary, status, error_message),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save summary to history: {e}")

    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent summaries."""
        try:
            conn = sqlite3.connect(SummaryHistory.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, email_count, summary, status, error_message
                FROM summaries
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Failed to retrieve summary history: {e}")
            return []


def _run_with_retries(func: Callable[..., Any], name: str, max_attempts: int = 3, delay_seconds: int = 4, *args, **kwargs) -> Any:
    """Run an action with retries and logging."""
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_attempts}: {name}")
            return func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc
            logger.error(f"{name} failed on attempt {attempt}/{max_attempts}: {exc}")
            if attempt < max_attempts:
                logger.info(f"Retrying {name} after {delay_seconds}s...")
                time.sleep(delay_seconds)
    raise last_exception


def pipeline_job(
    email_address: str,
    password: str,
    imap_server: str,
    imap_port: int,
    ollama_model: str,
    slack_webhook_url: str,
) -> None:
    """Main job: Fetch emails → Summarize → Post to Slack → Store history."""
    try:
        logger.info("=" * 60)
        logger.info(f"[{datetime.now()}] AutoPilot pipeline started")

        # Step 1: Fetch emails
        logger.info("Step 1: Fetching unread emails...")
        fetcher = EmailFetcher(
            email_address,
            password,
            imap_server,
            imap_port,
        )
        emails = _run_with_retries(
            lambda: fetcher.fetch_unread_emails(max_emails=10),
            "Fetch unread emails",
        )

        if not emails:
            logger.warning("No unread emails found")
            SummaryHistory.add(0, "", status="skipped")
            return

        logger.info(f"Step 1 complete: {len(emails)} emails fetched")

        # Step 2: Prepare for summarization
        logger.info("Step 2: Preparing emails for summarization...")
        email_text = fetcher.format_for_summary(emails)

        # Step 3: Summarize with Ollama
        logger.info("Step 3: Summarizing with Ollama (model: {})...".format(ollama_model))
        summary = _run_with_retries(
            lambda: summarize(email_text, model=ollama_model),
            "Generate summary",
        )
        logger.info("Step 3 complete: Summary generated")

        # Step 4: Post to Slack
        logger.info("Step 4: Posting summary to Slack...")
        slack = SlackSender(slack_webhook_url)
        blocks = SlackSender.format_email_summary(summary, len(emails))
        success = _run_with_retries(
            lambda: slack.send_message("Email Summary", blocks=blocks),
            "Post Slack message",
        )

        if success:
            logger.info("Step 4 complete: Message posted to Slack")
            logger.info("Summary preview: %s", summary[:300].replace("\n", " "))
            logger.info("=" * 60)
            logger.info(f"[{datetime.now()}] AutoPilot pipeline completed successfully\n")
            SummaryHistory.add(len(emails), summary, status="success")
        else:
            logger.error("Failed to post to Slack")
            SummaryHistory.add(len(emails), summary, status="slack_failed")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        logger.error("=" * 60 + "\n")
        SummaryHistory.add(0, "", status="failed", error_message=str(e))


class AutoPilotScheduler:
    """Manage scheduled tasks for email summarization and Slack posting."""

    JOBSTORE_DB = "autopilot_jobs.db"

    def __init__(self):
        self.job_args = [
            Config.EMAIL_ADDRESS,
            Config.EMAIL_PASSWORD,
            Config.EMAIL_IMAP_SERVER,
            Config.EMAIL_IMAP_PORT,
            Config.OLLAMA_MODEL,
            Config.SLACK_WEBHOOK_URL,
        ]
        SummaryHistory.init()
        self.scheduler = self._create_scheduler()

    def _create_scheduler(self) -> BackgroundScheduler:
        """Create a new BackgroundScheduler with the configured SQLAlchemy job store."""
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{self.JOBSTORE_DB}")
        }
        executors = {
            "default": ThreadPoolExecutor(max_workers=3),
        }
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
        }
        return BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=utc,
        )

    def _reset_job_store(self) -> None:
        """Reset the SQLite job store by removing the database and recreating the scheduler."""
        if os.path.exists(self.JOBSTORE_DB):
            logger.warning("Resetting invalid APScheduler job store: %s", self.JOBSTORE_DB)
            try:
                os.remove(self.JOBSTORE_DB)
            except OSError as exc:
                logger.error("Failed to remove stale job store: %s", exc)
                raise
        self.scheduler = self._create_scheduler()

    def add_scheduled_job(self, cron_expression: str = None):
        """Add the pipeline job to the scheduler."""
        if cron_expression is None:
            cron_expression = Config.SCHEDULE_CRON

        try:
            # Parse cron: "0 9 * * 1" = Monday 9 AM
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must be in format: minute hour day month weekday")

            minute, hour, day, month, weekday = parts

            self.scheduler.add_job(
                pipeline_job,
                "cron",
                args=self.job_args,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=weekday,
                id="email_summary_job",
                replace_existing=True,
            )

            logger.info(f"Job added to scheduler: {cron_expression}")
            return True

        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return False

    def add_test_job(self, seconds: int = 10):
        """Add a test job that runs every N seconds (for testing)."""
        try:
            self.scheduler.add_job(
                pipeline_job,
                "interval",
                args=self.job_args,
                seconds=seconds,
                id="test_job",
                replace_existing=True,
            )
            logger.info(f"Test job added: runs every {seconds} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to add test job: {e}")
            return False

    def start(self):
        """Start the scheduler."""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except TypeError as exc:
            message = str(exc)
            logger.error("Scheduler failed to start: %s", message)
            if "Schedulers cannot be serialized" in message:
                logger.warning("Detected invalid persisted job store. Resetting and retrying...")
                self._reset_job_store()
                self.scheduler.start()
                logger.info("Scheduler started successfully after resetting job store")
            else:
                raise

    def stop(self):
        """Stop the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        if not jobs:
            logger.info("No jobs scheduled")
            return []

        for job in jobs:
            logger.info(f"Job: {job.id} | Trigger: {job.trigger}")
        return jobs

    def trigger_now(self):
        """Manually trigger the pipeline (for testing)."""
        logger.info("Manually triggering pipeline...")
        pipeline_job(*self.job_args)

    def update_schedule(self, cron_expression: str) -> bool:
        """Update the cron schedule at runtime."""
        try:
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must be in format: minute hour day month weekday")

            minute, hour, day, month, weekday = parts

            self.scheduler.reschedule_job(
                "email_summary_job",
                trigger="cron",
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=weekday,
            )

            logger.info(f"Schedule updated to: {cron_expression}")
            return True
        except Exception as e:
            logger.error(f"Failed to update schedule: {e}")
            return False


# Quick test
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    Config.validate()

    scheduler = AutoPilotScheduler()
    scheduler.add_scheduled_job(Config.SCHEDULE_CRON)
    scheduler.list_jobs()

    logger.info("Starting scheduler (press Ctrl+C to stop)...")
    scheduler.start()

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        scheduler.stop()
