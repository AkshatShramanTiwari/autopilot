# AutoPilot Deployment Guide

Deploy AutoPilot to production using local, containerized, or cloud options.

---

## 1. Local Deployment (macOS/Linux)

### For Always-On Home Server

```bash
# 1. Setup
source venv/bin/activate
bash setup.sh

# 2. Configure .env
vim .env

# 3. Start with nohup (runs in background)
nohup python main.py > autopilot.log 2>&1 &

# 4. Verify
curl http://localhost:8000/health

# 5. To stop
pkill -f "python main.py"
```

### For Scheduled Execution (macOS LaunchAgent)

```bash
# Create LaunchAgent plist
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.autopilot.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.autopilot.service</string>
  <key>ProgramArguments</key>
  <array>
    <string>/path/to/AutoPilot/venv/bin/python</string>
    <string>/path/to/AutoPilot/main.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/path/to/AutoPilot</string>
  <key>StandardOutPath</key>
  <string>/path/to/AutoPilot/autopilot.log</string>
  <key>StandardErrorPath</key>
  <string>/path/to/AutoPilot/autopilot.log</string>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.autopilot.plist

# Check status
launchctl list | grep autopilot

# Unload
launchctl unload ~/Library/LaunchAgents/com.autopilot.plist
```

---

## 2. Docker Deployment

### Build Docker Image

```dockerfile
# Create Dockerfile in project root
FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose API port
EXPOSE 8000

# Run app
CMD ["python", "main.py"]
```

### Build and Run

```bash
# Build image
docker build -t autopilot:latest .

# Run locally
docker run -d \
  --name autopilot \
  -p 8000:8000 \
  --env-file .env \
  -v autopilot_data:/app \
  autopilot:latest

# Check logs
docker logs -f autopilot

# Stop
docker stop autopilot
docker rm autopilot
```

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  autopilot:
    build: .
    container_name: autopilot
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./autopilot.log:/app/autopilot.log
      - ./autopilot_jobs.db:/app/autopilot_jobs.db
      - ./autopilot_history.db:/app/autopilot_history.db
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## 3. Cloud Deployment

### Option A: Railway (Recommended - Easiest)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/autopilot.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repo
   - Railway auto-detects Python and runs `requirements.txt`

3. **Set Environment Variables**
   - In Railway dashboard: Project Settings → Variables
   - Add all `.env` variables

4. **Auto-Deploy on Push**
   - Railway automatically redeploys when you push to GitHub

### Option B: AWS Lambda + CloudWatch

1. **Package for Lambda**
   ```bash
   # Create deployment package
   pip install -r requirements.txt -t lambda_package/
   cp -r . lambda_package/
   cd lambda_package && zip -r ../lambda.zip . && cd ..
   ```

2. **Deploy to Lambda**
   - AWS Console → Lambda → Create Function
   - Runtime: Python 3.11
   - Upload `lambda.zip` as code
   - Handler: `main.app`
   - Timeout: 60s
   - Memory: 512 MB

3. **Set Environment Variables**
   - Lambda → Configuration → Environment Variables
   - Add all `.env` variables

4. **Trigger with CloudWatch Events**
   - CloudWatch → Rules → Create Rule
   - Schedule: cron(0 9 ? * MON) = Monday 9 AM
   - Target: Lambda function

### Option C: Google Cloud Run

1. **Set up Google Cloud**
   ```bash
   gcloud auth login
   gcloud projects create autopilot-prod
   gcloud config set project autopilot-prod
   ```

2. **Deploy**
   ```bash
   gcloud run deploy autopilot \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars EMAIL_ADDRESS=your@email.com,... \
     --memory 512Mi \
     --timeout 60s
   ```

3. **Schedule with Cloud Scheduler**
   ```bash
   gcloud scheduler jobs create http autopilot-schedule \
     --schedule "0 9 * * 1" \
     --http-method POST \
     --uri "https://YOUR-CLOUD-RUN-URL/trigger" \
     --location us-central1
   ```

### Option D: Self-Hosted VPS (DigitalOcean, Linode)

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Install dependencies
apt update && apt install -y python3.11 python3.11-venv python3-pip git curl

# Clone repo
cd /opt
git clone https://github.com/YOUR_USERNAME/autopilot.git
cd autopilot

# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
nano .env   # Add your credentials

# Run with systemd
sudo tee /etc/systemd/system/autopilot.service > /dev/null << EOF
[Unit]
Description=AutoPilot Email Summarizer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/autopilot
ExecStart=/opt/autopilot/venv/bin/python /opt/autopilot/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable autopilot
sudo systemctl start autopilot
sudo systemctl status autopilot

# View logs
sudo journalctl -u autopilot -f
```

---

## 4. Comparison Table

| Option | Cost | Setup Time | Always-On | Auto-Scale | Notes |
|--------|------|-----------|-----------|-----------|-------|
| Local | $0 | 5 min | ❌ | N/A | Good for testing |
| Docker | $0-20 | 15 min | ✅ | Manual | Most flexible |
| Railway | $5-50 | 5 min | ✅ | ✅ | Easiest to start |
| AWS Lambda | $0-10 | 30 min | ✅ | ✅ | Serverless, pay-per-call |
| Cloud Run | $0-20 | 20 min | ✅ | ✅ | Google's serverless |
| VPS | $5-20 | 20 min | ✅ | Manual | Full control |

---

## 5. New API Endpoints (Production Monitoring)

```bash
# Health check
curl http://YOUR_HOST:8000/health

# View scheduled jobs
curl http://YOUR_HOST:8000/jobs

# Update schedule at runtime
curl -X POST "http://YOUR_HOST:8000/schedule?cron=0%2018%20*%20*%20*"

# View summary history
curl http://YOUR_HOST:8000/history?limit=20

# Get config (non-sensitive)
curl http://YOUR_HOST:8000/config

# Manually trigger
curl -X POST http://YOUR_HOST:8000/trigger
```

---

## 6. Recommended Path

### For Personal Use
→ **Local** (macOS LaunchAgent) or **Docker**

### For Small Team
→ **Railway** or **Google Cloud Run**

### For Enterprise
→ **AWS Lambda** + job history or **VPS** with **Docker**

### For Development
→ Local with `python main.py`

---

## Troubleshooting

### "Failed to connect to Ollama"
- Ensure OLLAMA_HOST points to correct endpoint
- For cloud: may need Ollama running separately

### "Email fetch timeout"
- Increase timeout in email_fetcher.py
- Check IMAP credentials
- Verify firewall allows port 993

### "Schedule not running"
- Check `SCHEDULE_ENABLED=true` in .env
- Verify `SCHEDULE_CRON` format
- Check logs for APScheduler errors

**Ready? Pick an option and deploy!**


Keep this running while AutoPilot runs.

**Time: 1 minute**

### Task 3: Test individual components

```bash
# Test 1: Verify config loads
python -c "from config import Config; print('✓ Config OK')"

# Test 2: Test Ollama connection
python -c "from summarizer import summarize; print(summarize('Test'))"

# Test 3: List Ollama models
python -m ollama list
```

**Time: 5 minutes**

### Task 4: Manual trigger test

```bash
# Start server
python main.py &

# In another terminal, trigger
sleep 3
curl -X POST http://localhost:8000/trigger

# Watch logs
tail -f autopilot.log
```

**Time: 10 minutes**

---

## Day 2: Full Pipeline & Production Ready

### Task 1: Verify scheduled job runs

- [ ] Modify `SCHEDULE_CRON=*/5 * * * *` (every 5 minutes for testing)
- [ ] Restart `python main.py`
- [ ] Wait 5 minutes and check `autopilot.log`

**Expected**: Job runs automatically, fetches emails, summarizes, posts to Slack

**Time: 15 minutes**

### Task 2: Test after restart

- [ ] Stop the server (Ctrl+C)
- [ ] Check if `autopilot_jobs.db` exists
- [ ] Restart the server
- [ ] Verify job still runs at scheduled time

**Expected**: Job persists across restarts

**Time: 10 minutes**

### Task 3: Error scenarios

Test these error conditions:

```bash
# Test 1: No unread emails
# Expected: Pipeline completes, logs "No unread emails"

# Test 2: Wrong Slack webhook
# Update SLACK_WEBHOOK_URL to invalid value in .env
# Expected: Pipeline logs error, doesn't crash

# Test 3: Wrong email credentials
# Update EMAIL_PASSWORD to wrong value
# Expected: Pipeline logs IMAP error, doesn't crash

# Test 4: Ollama down
# Stop `ollama serve` in other terminal
# Trigger pipeline: curl -X POST http://localhost:8000/trigger
# Expected: Pipeline logs connection error, doesn't crash
```

**Time: 20 minutes**

---

## Production Configuration

Once tested, update cron for production:

```env
# Every Monday at 9 AM
SCHEDULE_CRON=0 9 * * 1

# Every weekday at 8:30 AM
SCHEDULE_CRON=30 8 * * 1-5

# Daily at 6 PM
SCHEDULE_CRON=0 18 * * *
```

---

## File Checklist

```
✓ .env              — Credentials filled in
✓ main.py           — FastAPI server
✓ config.py         — Config management
✓ scheduler.py      — APScheduler setup
✓ email_fetcher.py  — IMAP client
✓ summarizer.py     — Ollama integration
✓ slack_sender.py   — Slack webhook
✓ requirements.txt  — All dependencies
✓ README.md         — Full documentation
✓ setup.sh          — Setup automation
✓ .env.example      — Template
✓ autopilot.log     — Logs (auto-generated)
✓ autopilot_jobs.db — Job store (auto-generated)
```

---

## Endpoints Summary

| Method | Endpoint      | Purpose                          |
|--------|---------------|----------------------------------|
| GET    | `/health`     | Check if server is running       |
| POST   | `/trigger`    | Manually run pipeline            |
| GET    | `/jobs`       | List all scheduled jobs          |
| GET    | `/config`     | View current configuration       |

---

## Common Issues & Fixes

| Issue                           | Solution                                        |
|---------------------------------|-------------------------------------------------|
| Ollama connection failed        | `ollama serve` is not running                   |
| Config validation failed        | Missing required fields in `.env`               |
| IMAP authentication failed      | Wrong credentials or App Password for Gmail     |
| Slack webhook invalid           | Webhook URL is wrong or expired                 |
| Job not running on schedule     | Check cron expression format                    |
| Database locked error           | `rm autopilot_jobs.db` and restart              |

---

## Success Criteria (Acceptance)

- [ ] `ollama serve` runs without errors
- [ ] `python main.py` starts FastAPI server
- [ ] `curl -X POST http://localhost:8000/trigger` fetches emails
- [ ] Summary is generated by Ollama
- [ ] Summary is posted to Slack
- [ ] Job persists after restart
- [ ] All logs appear in `autopilot.log`
- [ ] No hardcoded credentials in code
- [ ] Error handling doesn't crash the app

---

## Next Steps (After 2 Days)

- [ ] Add database for summary history
- [ ] Add web dashboard
- [ ] Deploy to cloud (AWS Lambda, Railway, Heroku)
- [ ] Add analytics & metrics
- [ ] Support multiple schedules
- [ ] Add filtering & rules engine

---

## Support

For issues:
1. Check `autopilot.log` first
2. Review README.md troubleshooting section
3. Verify `.env` is filled correctly
4. Make sure `ollama serve` is running
5. Test individual components in isolation

---

**Status**: Ready for deployment ✅
**Last Updated**: 2026-06-22
**Assigned To**: Intern
