# Deploy AutoPilot to Vercel

Deploy your FastAPI app to Vercel with scheduled email summaries.

---

## ⚠️ Important: Vercel Limitations

Vercel is optimized for **serverless functions** and **Next.js apps**, not long-running Python servers. 

**Limitations:**
- Max function execution: 60 seconds (900s for pro)
- No persistent background scheduler
- Functions are stateless (each request is independent)
- Need external scheduler (e.g., cron-job.org, Zapier)

**Better Alternatives for This Project:**
- ✅ **Railway** - Best match (5 min setup)
- ✅ **Render** - Free tier available
- ✅ **Heroku** - Classic choice (but paid now)
- ✅ **Google Cloud Run** - Serverless + scheduler

**Continue with Vercel if:**
- You want manual trigger via webhook
- You'll use external scheduler service
- You want to learn Vercel deployment

---

## Step 1: Prepare Project for Git

### Remove sensitive files from tracking

```bash
cd /Users/akshatshramantiwari/Documents/Developer/AutoPilot

# Verify .gitignore has these entries
cat .gitignore
```

Should include:
```
.env
.env.*
*.db
__pycache__/
venv/
```

### Create `.env.example` (safe template)

```bash
cat > .env.example << 'EOF'
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
OLLAMA_MODEL=qwen3.5:cloud
OLLAMA_HOST=http://localhost:11434
SCHEDULE_CRON=0 9 * * 1
SCHEDULE_ENABLED=true
LOG_LEVEL=INFO
LOG_FILE=/tmp/autopilot.log
EOF
```

### Initialize Git repo

```bash
git init
git add .
git commit -m "Initial AutoPilot commit - FastAPI email summarizer"
```

---

## Step 2: Push to GitHub

### Create GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `autopilot`
3. **Description**: AI-powered email summarization with Slack integration
4. **Visibility**: Public (for Vercel)
5. Click **Create repository**

### Connect local repo to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/autopilot.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## Step 3: Create Vercel Configuration

### Create `vercel.json`

```bash
cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": {
        "maxDuration": 60,
        "memory": 512
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ],
  "env": {
    "SCHEDULE_ENABLED": "false",
    "LOG_FILE": "/tmp/autopilot.log"
  }
}
EOF
```

### Modify main.py for Vercel

Vercel expects a WSGI/ASGI app export. Update the last line of `main.py`:

```python
# At the very end of main.py, after all routes:

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This allows both local testing and Vercel deployment.

---

## Step 4: Add to Vercel

### Link GitHub to Vercel

1. Go to [vercel.com](https://vercel.com)
2. **Sign up** with GitHub
3. Click **Import Project**
4. **Select your repo**: `autopilot`
5. **Framework Preset**: Python
6. **Root Directory**: `./` (default)

### Configure Environment Variables

In Vercel dashboard → Project Settings → Environment Variables, add:

- `EMAIL_ADDRESS` = your-email@gmail.com
- `EMAIL_PASSWORD` = your-app-specific-password
- `EMAIL_IMAP_SERVER` = imap.gmail.com
- `EMAIL_IMAP_PORT` = 993
- `SLACK_WEBHOOK_URL` = https://hooks.slack.com/...
- `OLLAMA_MODEL` = qwen3.5:cloud
- `OLLAMA_HOST` = http://localhost:11434
- `SCHEDULE_ENABLED` = false (set to false for Vercel)
- `SCHEDULE_CRON` = 0 9 * * 1
- `LOG_LEVEL` = INFO
- `LOG_FILE` = /tmp/autopilot.log

### Deploy

Click **Deploy** — Vercel builds and deploys automatically.

Once deployed, your app is live at:
```
https://autopilot-yourname.vercel.app
```

---

## Step 5: Test Vercel Deployment

```bash
# Replace with your actual Vercel URL
VERCEL_URL="https://autopilot-yourname.vercel.app"

# Test root endpoint
curl $VERCEL_URL/

# Test health
curl $VERCEL_URL/health

# Test config
curl -X POST $VERCEL_URL/config

# Test jobs
curl $VERCEL_URL/jobs
```

---

## Step 6: Set Up External Scheduler (Important!)

Since Vercel doesn't support background jobs, you need an external scheduler to trigger your pipeline.

### Option A: cron-job.org (Free)

1. Go to [cron-job.org](https://cron-job.org)
2. **Create Cronjob**
   - **URL**: `https://autopilot-yourname.vercel.app/trigger`
   - **Method**: POST
   - **Schedule**: 9 AM Monday (Cron: `0 9 * * 1`)
   - **Execution timeout**: 60 seconds
3. **Save**

### Option B: AWS CloudWatch Events

1. AWS Console → CloudWatch → Rules
2. **Create Rule**
   - **Schedule**: `cron(0 9 ? * MON *)`
   - **Target**: HTTPS endpoint → Your Vercel URL + `/trigger`
3. **Create**

### Option C: Zapier (Paid)

1. Zapier.com → Make a Zap
2. **Trigger**: Schedule
3. **Action**: Webhook → POST to your Vercel URL
4. **When**: 9 AM Monday

### Option D: GitHub Actions (Free, Built-in)

Create `.github/workflows/trigger.yml`:

```yaml
name: AutoPilot Trigger

on:
  schedule:
    - cron: '0 9 * * 1'  # 9 AM Monday

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger AutoPilot
        run: |
          curl -X POST https://autopilot-yourname.vercel.app/trigger
```

Commit and push:
```bash
git add .github/workflows/trigger.yml
git commit -m "Add GitHub Actions scheduler"
git push origin main
```

---

## Step 7: Monitor & Troubleshoot

### View Logs

Vercel Dashboard → Logs → Function Logs

### Common Issues

**"Module not found"**
- Ensure `requirements.txt` is in root
- Add to `vercel.json` build config

**"Connection refused"**
- Ollama needs to be hosted online or locally accessible
- For Vercel (cloud), use hosted Ollama API

**"Timeout after 60 seconds"**
- Email summarization took too long
- Increase timeout in `vercel.json`: `"maxDuration": 300` (5 minutes, pro only)
- Optimize summarization speed

**"Schedule not running"**
- Vercel doesn't support background jobs
- Use external scheduler (cron-job.org, GitHub Actions, etc.)

---

## Step 8: Monitor History & Endpoints

### Check Recent Summaries

```bash
curl https://autopilot-yourname.vercel.app/history?limit=10 | jq
```

### Update Schedule Dynamically

```bash
curl -X POST "https://autopilot-yourname.vercel.app/schedule?cron=0%2018%20*%20*%20*"
```

### View Jobs

```bash
curl https://autopilot-yourname.vercel.app/jobs | jq
```

---

## Full Workflow Summary

```bash
# 1. Prepare for Git
cd /Users/akshatshramantiwari/Documents/Developer/AutoPilot
git init
git add .
git commit -m "Initial commit"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/autopilot.git
git push -u origin main

# 3. Create vercel.json (done above)

# 4. Deploy via Vercel dashboard
# - Import from GitHub
# - Set environment variables
# - Deploy

# 5. Set up external scheduler
# - Use cron-job.org or GitHub Actions

# 6. Monitor
curl https://autopilot-yourname.vercel.app/health
curl https://autopilot-yourname.vercel.app/history
```

---

## Alternative: Better Platforms for This Project

### Railway (Recommended)

```bash
# Just push and deploy
git push origin main

# That's it! Railway auto-detects Python and deploys.
# Includes built-in scheduler support.
```

Go to [railway.app](https://railway.app), connect GitHub, select repo, add env vars.

### Render

Similar to Railway, supports Python and scheduled jobs.
Go to [render.com](https://render.com), create web service from GitHub.

---

## Quick Deploy Checklist

- [ ] `.env.example` created
- [ ] `vercel.json` created
- [ ] Git repo initialized: `git init`
- [ ] All files committed: `git add . && git commit -m "..."`
- [ ] GitHub repo created
- [ ] Code pushed: `git push -u origin main`
- [ ] Vercel connected to GitHub
- [ ] Environment variables added in Vercel
- [ ] Deployed successfully
- [ ] External scheduler configured (cron-job.org or GitHub Actions)
- [ ] Test endpoints work:
  - `curl https://your-url/health`
  - `curl https://your-url/jobs`
  - `curl -X POST https://your-url/trigger`
  - `curl https://your-url/history`

---

## Next Steps

1. **Test Locally First**
   ```bash
   source venv/bin/activate
   python main.py
   curl http://localhost:8000/health
   ```

2. **Push to GitHub**
   ```bash
   git push origin main
   ```

3. **Deploy to Vercel**
   - Go to vercel.com
   - Import your GitHub repo
   - Set env vars
   - Deploy

4. **Set Up Scheduler**
   - Use cron-job.org or GitHub Actions
   - Test with manual trigger: `curl -X POST https://your-url/trigger`

5. **Monitor**
   - Check `/history` endpoint
   - Review Vercel logs
   - Verify Slack messages

---

**Ready to deploy? Start with `git init` and follow the checklist!** 🚀
