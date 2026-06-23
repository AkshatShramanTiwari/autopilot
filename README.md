# AutoPilot — Scheduled & Triggered Agent Workflows

Automatically summarize your unread emails and post summaries to Slack on a schedule using Ollama AI running locally on your GPU.

## Features

- ✅ **Local AI Model**: Runs Ollama (`qwen3.5:cloud`) on your GPU — no cloud costs, no API keys
- ✅ **Scheduled Tasks**: Uses APScheduler with cron expressions for flexible scheduling
- ✅ **Email Integration**: Fetches unread emails via IMAP (Gmail, Outlook, etc.)
- ✅ **Slack Notifications**: Posts formatted summaries directly to Slack
- ✅ **Job Persistence**: SQLite-backed job store survives app restarts
- ✅ **FastAPI Server**: Manual trigger endpoints + status monitoring
- ✅ **Comprehensive Logging**: Full execution logs saved to `autopilot.log`

## Prerequisites

- Python 3.10+
- Ollama installed locally (`ollama serve` running)
- Gmail or Outlook account with IMAP enabled
- Slack workspace with webhook access

## Quick Setup

### 1. Clone and install dependencies

```bash
cd /path/to/AutoPilot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up Ollama

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull the model (one-time)
ollama pull qwen3.5:cloud
```

### 3. Configure credentials

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Gmail setup (use App Password, not regular password)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993

# Slack webhook (create from Slack App settings)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Ollama
OLLAMA_MODEL=qwen3.5:cloud
OLLAMA_HOST=http://localhost:11434

# Schedule (cron format: minute hour day month weekday)
SCHEDULE_CRON=0 9 * * 1  # Every Monday at 9 AM
SCHEDULE_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=autopilot.log
```

### 4. Get Gmail App Password

1. Go to [Google Account settings](https://myaccount.google.com/)
2. Enable 2-Factor Authentication
3. Generate an **App Password** for "Mail" on "Windows Computer"
4. Copy that password into `.env`

### 5. Create Slack Webhook

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app (or select existing)
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select target channel
6. Copy the webhook URL to `.env`

## Usage

### Start the server

```bash
source venv/bin/activate
python main.py
```

Server runs on `http://localhost:8000`

### Endpoints

**Health check:**
```bash
curl http://localhost:8000/health
```

**List scheduled jobs:**
```bash
curl http://localhost:8000/jobs
```

**Manually trigger the pipeline (for testing):**
```bash
curl -X POST http://localhost:8000/trigger
```

**View current configuration:**
```bash
curl -X POST http://localhost:8000/config
```

### Check logs

```bash
tail -f autopilot.log
```

## Testing Guide (2-Day Sprint)

### Day 1: Test Individual Components

```bash
# Test email fetcher
python -m email_fetcher

# Test Ollama summarizer
python -c "from summarizer import summarize; print(summarize('Test email about Python'))"

# Test Slack sender
python -m slack_sender

# Test scheduler
python scheduler.py
```

### Day 2: Full Pipeline Test

```bash
# Start Ollama (if not running)
ollama serve &

# Start AutoPilot
python main.py

# In another terminal, trigger manually
curl -X POST http://localhost:8000/trigger
```

## Cron Schedule Examples

```
# Every Monday at 9 AM
0 9 * * 1

# Every weekday at 8:30 AM
30 8 * * 1-5

# Every day at 6 PM
0 18 * * *

# Every 10 minutes (testing)
*/10 * * * *

# First day of month at 9 AM
0 9 1 * *
```

## File Structure

```
AutoPilot/
├── main.py              # FastAPI server & orchestration
├── config.py            # Configuration management
├── scheduler.py         # APScheduler setup & job logic
├── email_fetcher.py     # IMAP email fetching
├── summarizer.py        # Ollama summarization
├── slack_sender.py      # Slack webhook posting
├── requirements.txt     # Python dependencies
├── .env                 # Credentials (never commit)
├── .env.example         # Template
├── autopilot.log        # Execution logs (generated)
└── autopilot_jobs.db    # SQLite job store (generated)
```

## Troubleshooting

### "Could not connect to ollama server"
- Make sure `ollama serve` is running in another terminal
- Check `OLLAMA_HOST` in `.env` (default: `http://localhost:11434`)

### "Failed to connect to IMAP server"
- Verify EMAIL_ADDRESS and EMAIL_PASSWORD are correct
- For Gmail: Make sure you're using an **App Password**, not your regular password
- Check that IMAP is enabled in your email provider

### "Failed to send message to Slack"
- Verify SLACK_WEBHOOK_URL is correct
- Make sure the webhook is still active (Slack webhooks can expire)
- Check that the target channel still exists

### "Job didn't run at scheduled time"
- Check `autopilot.log` for errors
- Verify APScheduler database is not locked: `rm autopilot_jobs.db` and restart
- Check cron expression format (must be: minute hour day month weekday)

## Performance Notes

- **Ollama Memory**: `qwen3.5:cloud` runs on CPU but uses GPU acceleration when available
- **Email Fetch**: Typically 2-5 seconds
- **Summarization**: Typically 5-15 seconds (depends on email volume)
- **Slack Post**: Typically <1 second

**Total pipeline time**: ~10-20 seconds

## Next Steps (Extended Features)

- Add database to store summaries history
- Add web dashboard to view past summaries
- Support multiple channels
- Add filtering (only summarize certain senders)
- Add retry logic with exponential backoff
- Deploy to cloud (AWS Lambda, Google Cloud Run)

## License

This is an internal project. All rights reserved.

---

**Questions or issues?** Check `autopilot.log` first, then reach out.
