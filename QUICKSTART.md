# AutoPilot Quick Reference Card

## ONE-COMMAND STARTUP

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start AutoPilot
cd ~/Documents/Developer/AutoPilot
source venv/bin/activate
python main.py

# Terminal 3: Test (optional)
curl -X POST http://localhost:8000/trigger
```

---

## CONFIGURATION

### Gmail App Password Setup
1. Go: https://myaccount.google.com/
2. Security > App passwords
3. Select "Mail" and "Windows Computer"
4. Copy password → paste in `.env`

### Slack Webhook Setup
1. Go: https://api.slack.com/apps
2. Create app (or select existing)
3. Incoming Webhooks > Add webhook
4. Select channel
5. Copy URL → paste in `.env`

### Edit Configuration
```bash
vim .env
```

Key fields:
```
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SCHEDULE_CRON=0 9 * * 1   (Monday 9 AM)
```

---

## MONITORING

### View Logs (Real-time)
```bash
tail -f autopilot.log
```

### List Scheduled Jobs
```bash
curl http://localhost:8000/jobs
```

### Check System Health
```bash
curl http://localhost:8000/health
```

### Manually Trigger Pipeline
```bash
curl -X POST http://localhost:8000/trigger
```

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| "Could not connect to ollama" | Run `ollama serve` in another terminal |
| "IMAP login failed" | Use **App Password**, not regular password |
| "Invalid webhook" | Check Slack webhook URL in `.env` |
| "Job didn't run" | Check cron expression: `minute hour day month weekday` |
| Database locked | `rm autopilot_jobs.db` and restart |
| Nothing in Slack | Check logs with `tail -f autopilot.log` |

---

## CRON SCHEDULE REFERENCE

```
0 9 * * 1      → Every Monday at 9 AM
30 8 * * 1-5   → Weekdays at 8:30 AM
0 18 * * *     → Every day at 6 PM
*/5 * * * *    → Every 5 minutes (testing)
*/10 * * * *   → Every 10 minutes (testing)
```

Format: `minute hour day month weekday`

---

## TESTING WORKFLOW

### Step 1: Component Tests
```bash
python -c "from summarizer import summarize; print(summarize('Test'))"
```

### Step 2: Manual Trigger
```bash
python main.py &
sleep 2
curl -X POST http://localhost:8000/trigger
tail -f autopilot.log
```

### Step 3: Scheduled Run
```bash
# Set cron to run every 5 minutes for testing
SCHEDULE_CRON=*/5 * * * *
# Start server and wait 5 minutes
python main.py
# Monitor logs
tail -f autopilot.log
```

---

## FILE STRUCTURE

```
AutoPilot/
├── main.py           ← Start here
├── config.py         ← Configuration
├── scheduler.py      ← Job scheduling
├── email_fetcher.py  ← Email logic
├── summarizer.py     ← Ollama integration
├── slack_sender.py   ← Slack logic
├── .env              ← Credentials (EDIT THIS)
├── README.md         ← Full docs
├── DEPLOYMENT.md     ← Deployment guide
├── requirements.txt  ← Dependencies
└── setup.sh          ← Setup script
```

---

## ENDPOINTS (FOR TESTING)

```
GET  http://localhost:8000/health
POST http://localhost:8000/trigger
GET  http://localhost:8000/jobs
GET  http://localhost:8000/config
```

---

## 2-DAY SPRINT TASKS

### Day 1
- [ ] Edit `.env` with credentials
- [ ] Run `ollama serve`
- [ ] Run `python main.py`
- [ ] Test manual trigger: `curl -X POST http://localhost:8000/trigger`
- [ ] Verify email fetches and posts to Slack

### Day 2
- [ ] Set cron to test frequency (e.g., `*/5 * * * *`)
- [ ] Let it run for 15 minutes to verify auto-scheduling
- [ ] Stop and restart to test persistence
- [ ] Change cron back to production schedule
- [ ] Document any issues in log

---

## SUCCESS INDICATORS

✅ Ollama summarizes emails  
✅ Summary posts to Slack  
✅ Job runs on schedule  
✅ No errors in logs  
✅ Persists after restart  

---

**Quick Help:**
- Full docs: `README.md`
- Deploy guide: `DEPLOYMENT.md`
- Logs: `autopilot.log`
- Slack help: https://api.slack.com/
- Gmail help: https://support.google.com/accounts/

Last Updated: 2026-06-22
