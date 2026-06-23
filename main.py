"""Main orchestration for AutoPilot — FastAPI server with scheduled tasks."""

import logging
import signal
import sys
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from config import Config
from scheduler import AutoPilotScheduler

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler_instance: AutoPilotScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage scheduler lifecycle."""
    global scheduler_instance

    # Startup
    logger.info("Starting AutoPilot...")
    try:
        Config.validate()
        logger.info("Configuration validated")

        scheduler_instance = AutoPilotScheduler()

        if Config.SCHEDULE_ENABLED:
            scheduler_instance.add_scheduled_job(Config.SCHEDULE_CRON)
            scheduler_instance.start()
            logger.info("Scheduler started")
        else:
            logger.info("Schedule disabled. Scheduler initialized for manual triggers only.")

    except Exception as e:
        logger.error(f"Failed to start AutoPilot: {e}")
        sys.exit(1)

    yield

    # Shutdown
    logger.info("Shutting down AutoPilot...")
    if scheduler_instance:
        scheduler_instance.stop()
    logger.info("AutoPilot stopped")


# Create FastAPI app
app = FastAPI(
    title="AutoPilot",
    description="Scheduled AI-powered email summarization to Slack",
    version="1.0.0",
    lifespan=lifespan,
)


# Routes
@app.get("/")
async def root():
    """Root endpoint with available endpoints."""
    return {
        "name": "AutoPilot",
        "description": "Scheduled AI-powered email summarization to Slack",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "GET /jobs": "List scheduled jobs",
            "GET /history": "Get summary history (params: ?limit=10)",
            "POST /trigger": "Manually trigger pipeline",
            "POST /schedule": "Update cron schedule (params: ?cron=0 9 * * *)",
            "POST /config": "Get current configuration",
            "GET /docs": "Interactive API documentation (Swagger UI)",
        },
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler_instance.scheduler.running if scheduler_instance else False,
        "schedule_enabled": Config.SCHEDULE_ENABLED,
        "model": Config.OLLAMA_MODEL,
    }


@app.post("/trigger")
async def trigger_pipeline():
    """Manually trigger the email summarization pipeline."""
    if not scheduler_instance:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    try:
        scheduler_instance.trigger_now()
        return {"status": "success", "message": "Pipeline triggered"}
    except Exception as e:
        logger.error(f"Failed to trigger pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs")
async def list_jobs():
    """List all scheduled jobs."""
    if not scheduler_instance:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    jobs = scheduler_instance.scheduler.get_jobs()
    return {
        "jobs": [
            {
                "id": job.id,
                "trigger": str(job.trigger),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in jobs
        ]
    }


@app.post("/schedule")
async def update_schedule(cron: str):
    """Update the cron schedule at runtime."""
    if not scheduler_instance:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    if scheduler_instance.update_schedule(cron):
        return {"status": "success", "cron": cron, "message": "Schedule updated"}
    else:
        raise HTTPException(status_code=400, detail="Invalid cron expression")


@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent email summaries from history."""
    from scheduler import SummaryHistory

    history = SummaryHistory.get_recent(limit)
    return {"summaries": history}


@app.post("/config")
async def get_config():
    """Get current configuration (non-sensitive)."""
    return {
        "email_address": Config.EMAIL_ADDRESS,
        "ollama_model": Config.OLLAMA_MODEL,
        "schedule_cron": Config.SCHEDULE_CRON,
        "schedule_enabled": Config.SCHEDULE_ENABLED,
        "log_level": Config.LOG_LEVEL,
    }


# Graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received shutdown signal")
    if scheduler_instance:
        scheduler_instance.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AutoPilot FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )