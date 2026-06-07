# Quick Start Guide - Job Apply Tool

Get started in **5 minutes** and start auto-applying to jobs\!

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (optional, for web dashboard)
- A resume file (PDF/DOCX)

---

## Installation (2 minutes)

### 1. Clone and Install

```bash
# Clone repository
git clone https://github.com/snandkule/JobApplyTool.git
cd JobApplyTool

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Initialize

```bash
python -m cli.main init
```

This creates:
- `data/` directory
- SQLite database
- Configuration files

---

## Setup Profile (1 minute)

### Option 1: Quick Setup (Automated - Recommended)

```bash
# 1. Create minimal profile
python -m cli.main profile create
# Enter just: Name and Email

# 2. Upload your resume
python -m cli.main profile add-resume ~/path/to/resume.pdf --default

# 3. Auto-build profile from resume\!
python -m cli.main profile build-from-resume 1
# Review suggestions and type: all
```

**Done\!** Your profile is now complete with skills, work history, and education extracted from your resume.

### Option 2: Manual Setup

```bash
# Create profile
python -m cli.main profile create

# Add resume
python -m cli.main profile add-resume ~/resume.pdf --default

# Add skills manually
python -m cli.main profile add-skill "Python" --proficiency "Expert"
python -m cli.main profile add-skill "React" --proficiency "Advanced"
```

---

## Start Applying (1 minute)

### Daemon Mode (24/7 Automation)

```bash
# Start automation
python -m cli.main daemon start \
  --criteria "Software Engineer" \
  --location "Remote" \
  --max-daily 50

# Monitor status
python -m cli.main daemon status
```

The daemon will automatically:
- ✅ Search for matching jobs
- ✅ Score them with AI  
- ✅ Generate unique cover letters
- ✅ Apply automatically
- ✅ Ask you questions when uncertain

---

## Answer Questions (As Needed)

```bash
# View pending questions
python -m cli.main questions list

# Answer all questions interactively
python -m cli.main questions batch-answer
```

---

## Complete Example

```bash
# 1. Install
git clone https://github.com/snandkule/JobApplyTool.git
cd JobApplyTool
pip install -r requirements.txt
playwright install chromium

# 2. Initialize
python -m cli.main init

# 3. Quick profile setup
python -m cli.main profile create
python -m cli.main profile add-resume ~/resume.pdf --default
python -m cli.main profile build-from-resume 1

# 4. Authenticate platforms
python -m cli.main auth linkedin
python -m cli.main auth indeed

# 5. Start auto-applying\!
python -m cli.main daemon start \
  --criteria "Software Engineer" \
  --max-daily 50
```

**Done\! The bot is now running 24/7 and applying to jobs automatically.**

---

## Web Dashboard (Optional)

For real-time monitoring:

```bash
# Terminal 1: Backend
uvicorn backend.app.main:app --port 8000

# Terminal 2: Frontend  
cd frontend && npm install && npm run dev

# Open: http://localhost:5173
```

---

## Common Commands

```bash
# Profile
python -m cli.main profile show
python -m cli.main profile list-skills

# Applications
python -m cli.main apply stats
python -m cli.main apply list --status submitted

# Questions
python -m cli.main questions list
python -m cli.main questions batch-answer

# Daemon
python -m cli.main daemon status
python -m cli.main daemon stop
python -m cli.main daemon logs
```

---

## What to Expect

**Day 1-2:**
- 20-30 applications submitted
- 10-15 questions to answer (teaches the bot)

**Day 3+:**
- 40-50 applications submitted
- 1-2 questions (bot learned from your answers)

**Week 2:**
- 200-300 total applications
- High automation (95%+ questions auto-answered)

---

## Full Documentation

- **Complete Guide:** [README.md](README.md)
- **Web Dashboard:** [docs/WEB_DASHBOARD_GUIDE.md](docs/WEB_DASHBOARD_GUIDE.md)
- **Architecture:** [docs/DESIGN.md](docs/DESIGN.md)

---

**You're ready\! Start applying to hundreds of jobs automatically.** 🚀
