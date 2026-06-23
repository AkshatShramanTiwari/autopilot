# AutoPilot REST API Reference

All endpoints are available at `http://localhost:8000` when running locally.

---

## Health & Status

### GET /health
Check if the service is running and scheduler is active.

**Response:**
```json
{
  "status": "healthy",
  "scheduler_running": true,
  "schedule_enabled": true,
  "model": "qwen3.5:cloud"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## Jobs & Scheduling

### GET /jobs
List all scheduled jobs.

**Response:**
```json
{
  "jobs": [
    {
      "id": "email_summary_job",
      "trigger": "cron[minute='0', hour='9', day_of_week='0-4']",
      "next_run": "2026-06-23T09:00:00+00:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/jobs
```

### POST /trigger
Manually trigger the email summarization pipeline immediately.

**Response:**
```json
{
  "status": "success",
  "message": "Pipeline triggered"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/trigger
```

---

## Schedule Management

### POST /schedule
Update the cron schedule at runtime without restarting.

**Parameters:**
- `cron` (string, required): New cron expression
  - Format: `minute hour day month day_of_week`
  - Example: `0 9 * * 1-5` = 9 AM Monday-Friday
  - Example: `0 18 * * *` = 6 PM every day

**Response:**
```json
{
  "status": "success",
  "cron": "0 9 * * 1-5",
  "message": "Schedule updated"
}
```

**Example:**
```bash
# Monday-Friday 9 AM
curl -X POST "http://localhost:8000/schedule?cron=0%209%20*%20*%201-5"

# Every day at 6 PM
curl -X POST "http://localhost:8000/schedule?cron=0%2018%20*%20*%20*"

# Every Monday at noon
curl -X POST "http://localhost:8000/schedule?cron=0%2012%20*%20*%201"
```

---

## History & Analytics

### GET /history
Retrieve past email summaries and execution history.

**Parameters:**
- `limit` (integer, optional): Number of records to return (default: 10, max: 100)

**Response:**
```json
{
  "summaries": [
    {
      "timestamp": "2026-06-23T09:15:30.123456",
      "email_count": 5,
      "summary": "Executive summary of emails received...",
      "status": "success",
      "error_message": null
    },
    {
      "timestamp": "2026-06-22T09:12:45.654321",
      "email_count": 3,
      "summary": "Email summary text...",
      "status": "success",
      "error_message": null
    }
  ]
}
```

**Example:**
```bash
# Get last 10 summaries
curl http://localhost:8000/history

# Get last 50 summaries
curl "http://localhost:8000/history?limit=50"

# With jq for pretty printing
curl http://localhost:8000/history | jq .
```

---

## Configuration

### POST /config
Get current configuration (non-sensitive values only).

**Response:**
```json
{
  "email_address": "user@gmail.com",
  "ollama_model": "qwen3.5:cloud",
  "schedule_cron": "0 9 * * 1-5",
  "schedule_enabled": true,
  "log_level": "INFO"
}
```

**Example:**
```bash
curl http://localhost:8000/config
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid parameters (e.g., invalid cron expression)
- **500 Internal Server Error**: Server error (e.g., scheduler not initialized)

Error responses include a `detail` field:

```json
{
  "detail": "Invalid cron expression"
}
```

---

## Common Workflows

### Change Schedule to 6 PM Daily
```bash
curl -X POST "http://localhost:8000/schedule?cron=0%2018%20*%20*%20*"
```

### Run Summary Now
```bash
curl -X POST http://localhost:8000/trigger
```

### Monitor Last 5 Summaries
```bash
curl "http://localhost:8000/history?limit=5" | jq '.summaries[] | {timestamp, email_count, status}'
```

### Check System Status
```bash
curl http://localhost:8000/health | jq '.'
```

---

## Cron Expression Examples

| Expression | Schedule |
|-----------|----------|
| `0 9 * * 1-5` | 9 AM Monday-Friday |
| `0 9 * * *` | 9 AM every day |
| `0 18 * * *` | 6 PM every day |
| `0 12 * * 1` | Noon every Monday |
| `0 9,14 * * *` | 9 AM and 2 PM daily |
| `0 */2 * * *` | Every 2 hours |
| `30 9 * * MON-FRI` | 9:30 AM weekdays |

---

## Monitoring & Alerts

### Health Check (for uptime monitoring)
```bash
# Check every 5 minutes
*/5 * * * * curl -f http://localhost:8000/health || mail -s "AutoPilot Down" you@email.com
```

### Track Recent Activity
```bash
# Check if recent summary succeeded
curl "http://localhost:8000/history?limit=1" | jq '.summaries[0].status'
```

### Verify Schedule Update
```bash
# After updating schedule, verify it took effect
curl http://localhost:8000/jobs | jq '.jobs[0].trigger'
```

---

## Integration Examples

### Python
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Get history
response = requests.get('http://localhost:8000/history?limit=10')
summaries = response.json()['summaries']
for s in summaries:
    print(f"{s['timestamp']}: {s['email_count']} emails")

# Update schedule
response = requests.post('http://localhost:8000/schedule?cron=0%2018%20*%20*%20*')
print(response.json())
```

### JavaScript
```javascript
// Health check
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(d => console.log(d));

// Get history
fetch('http://localhost:8000/history?limit=10')
  .then(r => r.json())
  .then(d => d.summaries.forEach(s => 
    console.log(`${s.timestamp}: ${s.email_count} emails`)
  ));

// Update schedule
fetch('http://localhost:8000/schedule?cron=0%2018%20*%20*%20*', {
  method: 'POST'
})
  .then(r => r.json())
  .then(d => console.log(d));
```

### Bash
```bash
#!/bin/bash

# Monitor AutoPilot health every hour
while true; do
  STATUS=$(curl -s http://localhost:8000/health | jq '.status')
  if [ "$STATUS" != '"healthy"' ]; then
    echo "AutoPilot is down!" | mail -s "Alert" you@email.com
  fi
  sleep 3600
done
```

---

## Deployment: API Endpoints

When deployed to cloud, use the public URL instead of `localhost`:

```bash
# Railway
curl https://autopilot-prod-abc123.railway.app/health

# Google Cloud Run
curl https://autopilot-abc123.a.run.app/health

# AWS Lambda (via API Gateway)
curl https://api-id.execute-api.us-east-1.amazonaws.com/prod/health
```

---

**For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**
