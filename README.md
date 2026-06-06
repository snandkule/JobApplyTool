# Job Apply Tool

🤖 AI-powered job application automation tool that applies to hundreds of jobs automatically with intelligent Q&A learning and real-time monitoring.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Features

### Core Capabilities
- 🚀 **Bulk Auto-Apply** - Apply to 50+ jobs per day automatically
- 🧠 **AI-Powered** - Claude Code integration for cover letters and job matching
- 📝 **Smart Q&A Learning** - Learns from your answers and reuses them intelligently
- 🎯 **Job Matching** - AI scoring (0-100%) to prioritize best-fit jobs
- 🌐 **Multi-Platform** - LinkedIn Easy Apply, Indeed Quick Apply
- 📊 **Real-time Dashboard** - Web UI with live statistics and charts
- 🔄 **24/7 Operation** - Background daemon for continuous automation
- 💾 **Knowledge Base** - Saves answers with fuzzy matching for reuse

### Platform Support
- ✅ **LinkedIn** (Easy Apply)
- ✅ **Indeed** (Quick Apply)
- 🔜 Custom career pages (coming soon)

### AI Features
- ✅ Tailored cover letter generation
- ✅ Job match scoring with skill analysis
- ✅ Answer suggestions for application questions
- ✅ Resume selection recommendations

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
  - [CLI Commands](#cli-commands)
  - [Web Dashboard](#web-dashboard)
  - [Daemon Mode](#daemon-mode-247-automation)
- [Architecture](#-architecture)
- [Development](#-development)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

---

## ⚡ Quick Start

Get started in 5 minutes:

```bash
# 1. Clone and install
git clone https://github.com/snandkule/JobApplyTool.git
cd JobApplyTool
pip install -r requirements.txt
playwright install chromium

# 2. Initialize
python -m cli.main init

# 3. Create profile
python -m cli.main profile create \
  --name "Your Name" \
  --email "your.email@example.com" \
  --location "San Francisco, CA"

# 4. Add skills
python -m cli.main profile add-skill "Python" --proficiency "Expert"
python -m cli.main profile add-skill "React" --proficiency "Advanced"

# 5. Start daemon (applies to jobs automatically)
python -m cli.main daemon start \
  --criteria "Software Engineer" \
  --location "Remote" \
  --max-daily 50

# 6. Monitor via web dashboard
uvicorn backend.app.main:app --port 8000 &
cd frontend && npm install && npm run dev
# Open http://localhost:5173
```

That's it! The tool will now:
- Search for jobs matching your criteria
- Score them with AI (using Claude Code)
- Generate unique cover letters
- Apply automatically (up to 50/day)
- Ask you questions when uncertain
- Learn from your answers for future applications

---

## 📦 Installation

### Prerequisites

**Required:**
- Python 3.11 or higher
- Node.js 18+ (for web dashboard)
- pip (Python package manager)
- npm (Node package manager)

**Optional:**
- Claude Code CLI (for AI features)
- PostgreSQL (for production)

### Step 1: Clone Repository

```bash
git clone https://github.com/snandkule/JobApplyTool.git
cd JobApplyTool
```

### Step 2: Install Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

**Key dependencies:**
- FastAPI (web API)
- Playwright (browser automation)
- SQLAlchemy (database ORM)
- Typer (CLI framework)
- Rich (beautiful terminal output)

### Step 3: Install Playwright Browsers

```bash
# Install Chromium for browser automation
playwright install chromium

# Or install all browsers (optional)
playwright install
```

### Step 4: Install Frontend Dependencies (Optional)

```bash
cd frontend
npm install
cd ..
```

### Step 5: Initialize Application

```bash
# Creates directories and database
python -m cli.main init
```

This creates:
- `data/` - Database and user data
- `data/resumes/` - Resume storage
- `data/cover_letters/` - Generated cover letters
- `data/screenshots/` - Debug screenshots

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

**Edit `.env`:**

```env
# Database (SQLite by default, PostgreSQL for production)
DATABASE_URL=sqlite:///./data/job_apply.db

# Claude Code CLI path (for AI features)
CLAUDE_CLI_PATH=claude

# Rate Limits
LINKEDIN_MAX_PER_HOUR=10
LINKEDIN_MAX_PER_DAY=50
INDEED_MAX_PER_HOUR=20
INDEED_MAX_PER_DAY=100

# Delays (seconds)
LINKEDIN_DELAY_MIN=120
LINKEDIN_DELAY_MAX=300
INDEED_DELAY_MIN=60
INDEED_DELAY_MAX=180

# Browser settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=60000
```

### Claude Code Setup (AI Features)

The tool uses **Claude Code CLI** for AI features (no API tokens needed!):

1. Install Claude Code CLI: [claude.ai/code](https://claude.ai/code)

2. Verify installation:
```bash
claude --version
```

3. The tool automatically uses your active Claude session

**Note:** AI features work seamlessly if you're already using Claude Code. No additional setup required!

---

## 🚀 Usage

### CLI Commands

The tool provides a comprehensive CLI with 50+ commands:

#### Profile Management

```bash
# Create profile
python -m cli.main profile create \
  --name "John Doe" \
  --email "john@example.com" \
  --phone "+1-555-0100" \
  --location "San Francisco, CA" \
  --linkedin "https://linkedin.com/in/johndoe"

# Show profile
python -m cli.main profile show

# Add resume
python -m cli.main profile add-resume ~/resume.pdf --default --title "General Resume"

# List resumes
python -m cli.main profile list-resumes

# Add skills
python -m cli.main profile add-skill "Python" --proficiency "Expert" --category "Programming"
python -m cli.main profile add-skill "AWS" --proficiency "Advanced" --category "Cloud"

# List skills
python -m cli.main profile list-skills
```

#### Job Search & Management

```bash
# Search for jobs (requires authentication)
python -m cli.main jobs search "Software Engineer" --location "Remote" --platform linkedin

# List discovered jobs
python -m cli.main jobs list --status discovered --limit 20

# Show job details
python -m cli.main jobs show 123

# Add job to application queue
python -m cli.main jobs add-to-queue 123 --priority 8
```

#### Platform Authentication

```bash
# Authenticate with LinkedIn
python -m cli.main auth linkedin

# Authenticate with Indeed
python -m cli.main auth indeed

# Check authentication status
python -m cli.main auth status
```

#### Application Management

```bash
# Apply to a single job
python -m cli.main apply single 123

# Bulk apply to queued jobs
python -m cli.main apply bulk --count 20 --parallel 3

# List applications
python -m cli.main apply list --status submitted --limit 50

# Show application stats
python -m cli.main apply stats
```

#### Question & Answer System

```bash
# List pending questions
python -m cli.main questions list

# Answer questions interactively
python -m cli.main questions batch-answer

# Answer specific question
python -m cli.main questions answer 42 --response "Yes, I am willing to relocate"

# Resume paused applications after answering
python -m cli.main questions resume-paused

# View question statistics
python -m cli.main questions stats

# List knowledge base
python -m cli.main questions kb-list

# Export knowledge base
python -m cli.main questions kb-export answers.json
```

#### AI Features

```bash
# Generate cover letter for a job
python -m cli.main ai generate-cover-letter 123

# Calculate job match score
python -m cli.main ai match-score 123

# Get AI answer suggestion
python -m cli.main ai suggest-answer "Why do you want to work here?" --job-id 123

# Generate suggestions for all pending questions
python -m cli.main ai batch-suggest

# Analyze which resume to use
python -m cli.main ai analyze-resume 123

# Bulk generate cover letters
python -m cli.main ai bulk-cover-letters --status queued --limit 20
```

#### Daemon Mode (24/7 Automation)

```bash
# Create daemon configuration
python -m cli.main daemon create \
  --name "Software Engineer Search" \
  --criteria "Software Engineer" \
  --location "Remote" \
  --max-daily 50 \
  --platforms linkedin,indeed \
  --remote

# Start daemon
python -m cli.main daemon start 1

# Check daemon status
python -m cli.main daemon status

# View daemon logs
python -m cli.main daemon logs --tail 50

# Stop daemon
python -m cli.main daemon stop

# List all daemon configurations
python -m cli.main daemon list

# Delete daemon configuration
python -m cli.main daemon delete 1
```

---

### Web Dashboard

The web dashboard provides real-time monitoring and control:

#### Starting the Dashboard

**Terminal 1 - Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:** Open [http://localhost:5173](http://localhost:5173)

#### Dashboard Features

**1. Overview Dashboard**
- Total applications, submitted, pending, failed
- Success rate percentage
- Applications today and this week
- Line chart: Applications over time (30 days)
- Pie chart: Status distribution
- Platform-specific statistics
- **Auto-refreshes every 5 seconds**

**2. Application Queue**
- View all queued jobs
- Job details (company, title, location)
- AI match scores with color coding
- Priority indicators
- Remove jobs from queue
- **Auto-refreshes every 5 seconds**

**3. Pending Questions**
- Answer application questions via web UI
- AI suggestion button (one-click)
- Field types: text, number, yes/no
- Batch answering
- Knowledge base integration
- **Auto-refreshes every 5 seconds**

**4. Daemon Control**
- Live status indicator (green dot if running)
- Current configuration display
- Applications today / daily limit
- Queue size
- Last cycle timestamp
- Real-time log viewer (50 recent entries)
- **Status refreshes every 3 seconds**

#### API Documentation

Interactive API docs available at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Daemon Mode (24/7 Automation)

The daemon runs continuously in the background, automating the entire application process:

#### How It Works

```
┌─────────────────────────────────────────────────┐
│           Daemon Cycle (Every 15 mins)          │
└─────────────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │  1. Discover New Jobs   │
         │     (LinkedIn, Indeed)  │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  2. AI Filter & Score   │
         │     (Match >60%)        │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  3. Add to Queue        │
         │     (Priority order)    │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  4. Process Applications│
         │     (Rate limited)      │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  5. Generate Content    │
         │     (Cover letters)     │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  6. Submit Applications │
         │     (Browser automation)│
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  7. Handle Questions    │
         │     (Pause if unknown)  │
         └──────────┬──────────────┘
                    │
                    ▼
              [Repeat Cycle]
```

#### Starting Daemon

```bash
# Simple start
python -m cli.main daemon start \
  --criteria "Software Engineer" \
  --max-daily 50

# Advanced configuration
python -m cli.main daemon start \
  --criteria "Senior Python Developer" \
  --location "Remote" \
  --remote \
  --platforms linkedin,indeed \
  --max-daily 50 \
  --min-match-score 0.7
```

#### Monitoring Daemon

**Via CLI:**
```bash
# Status
python -m cli.main daemon status

# Logs (live tail)
python -m cli.main daemon logs --follow

# Statistics
python -m cli.main apply stats
```

**Via Web Dashboard:**
- Open [http://localhost:5173](http://localhost:5173)
- Navigate to "Daemon Control"
- View real-time status, logs, and metrics

#### Stopping Daemon

```bash
python -m cli.main daemon stop
```

The daemon will:
- Finish current application
- Save state
- Gracefully shut down

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interfaces                       │
│  ┌──────────────┐         ┌──────────────────────┐    │
│  │  CLI (Typer) │         │  Web UI (React)      │    │
│  │  - 50+ cmds  │         │  - Real-time charts  │    │
│  └──────────────┘         └──────────────────────┘    │
└────────────┬───────────────────────┬──────────────────┘
             │                       │
             ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                        │
│  - REST endpoints (40+)                                 │
│  - WebSocket real-time updates                         │
│  - CORS middleware                                      │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│           Business Logic & AI Services                  │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ AIService  │  │ Question      │  │ Queue        │  │
│  │ - Claude   │  │ Service       │  │ Manager      │  │
│  │   Code CLI │  │ - KB Learning │  │ - Priority   │  │
│  └────────────┘  └───────────────┘  └──────────────┘  │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│              Automation Engine                          │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Playwright │  │ Batch        │  │ Daemon       │   │
│  │ - Browser  │  │ Processor    │  │ - 24/7       │   │
│  │ - Sessions │  │ - Rate Limit │  │ - Cycles     │   │
│  └────────────┘  └──────────────┘  └──────────────┘   │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│              Data Layer (SQLAlchemy)                    │
│  - SQLite (dev) / PostgreSQL (prod)                     │
│  - 15+ models with relationships                        │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 Development

### Project Structure

```
JobApplyTool/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints (40+)
│   │   ├── automation/       # Browser automation
│   │   ├── ai/              # Claude Code integration
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── database/        # Database session
│   └── tests/               # Test suite (55+ tests)
├── cli/
│   ├── commands/            # CLI commands (50+)
│   └── main.py             # CLI entry point
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api/           # API client
│   │   └── App.tsx        # Main app
│   └── package.json       # Node dependencies
├── data/                  # User data (gitignored)
├── docs/                  # Documentation
└── run_tests.sh          # Test runner
```

### Adding New Features

**1. Add New CLI Command:**

```python
# cli/commands/mycommand.py
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def my_command(arg: str):
    """My new command."""
    console.print(f"[green]Running: {arg}[/green]")
```

**2. Add New API Endpoint:**

```python
# backend/app/api/myapi.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

**3. Add to main app:**

```python
# backend/app/main.py
from backend.app.api import myapi
app.include_router(myapi.router, prefix="/api/my", tags=["My API"])
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test suite
pytest backend/tests/test_ai_integration.py -v
pytest backend/tests/test_api_endpoints.py -v

# Run with coverage
pytest backend/tests/ --cov=backend/app --cov-report=html
open htmlcov/index.html
```

### Test Coverage

- **Phase 5 (AI Integration):** 30+ tests
- **Phase 6 (API Endpoints):** 25+ tests
- **Total:** 55+ tests with 80%+ coverage

### Manual Testing

**Test API:**
```bash
# Start backend
uvicorn backend.app.main:app --port 8000

# Test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/applications/stats/overview
```

**Test WebSocket:**
```python
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/api/ws') as ws:
        print(await ws.recv())

asyncio.run(test())
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue: Database locked**
```bash
# Close all connections
rm data/job_apply.db-wal
rm data/job_apply.db-shm
python -m cli.main init
```

**Issue: Playwright not installed**
```bash
playwright install chromium
```

**Issue: Port already in use**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn backend.app.main:app --port 8001
```

**Issue: Claude Code CLI not found**
```bash
# Install Claude Code: https://claude.ai/code
# Or set custom path
export CLAUDE_CLI_PATH=/path/to/claude
```

**Issue: Import errors**
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

**Issue: Frontend won't start**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📚 Documentation

Comprehensive guides in the `/docs` directory:

- **[DESIGN.md](docs/DESIGN.md)** - Complete architecture and design
- **[PHASE5_SUMMARY.md](docs/PHASE5_SUMMARY.md)** - AI integration details
- **[PHASE6_SUMMARY.md](docs/PHASE6_SUMMARY.md)** - Web dashboard details
- **[WEB_DASHBOARD_GUIDE.md](docs/WEB_DASHBOARD_GUIDE.md)** - Dashboard setup
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing procedures
- **[COMPLETION_SUMMARY.md](docs/COMPLETION_SUMMARY.md)** - Project status

---

## 🎯 Use Cases

### Use Case 1: First-Time Setup
```bash
# Initialize and create profile
python -m cli.main init
python -m cli.main profile create --name "Jane Doe" --email "jane@example.com"
python -m cli.main profile add-resume ~/resume.pdf --default

# Add skills
python -m cli.main profile add-skill "Python" --proficiency "Expert"
python -m cli.main profile add-skill "React" --proficiency "Advanced"

# Authenticate
python -m cli.main auth linkedin
python -m cli.main auth indeed

# Start applying
python -m cli.main daemon start --criteria "Software Engineer" --max-daily 30
```

### Use Case 2: Daily Monitoring
```bash
# Check status
python -m cli.main daemon status
python -m cli.main apply stats

# Answer any pending questions
python -m cli.main questions list
python -m cli.main questions batch-answer

# View applications
python -m cli.main apply list --status submitted --limit 20
```

### Use Case 3: Power User (Web Dashboard)
```bash
# Terminal 1: Backend
uvicorn backend.app.main:app --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Daemon
python -m cli.main daemon start --criteria "Senior Engineer" --max-daily 50

# Monitor everything at: http://localhost:5173
```

---

## 🚀 Production Deployment

### Backend (FastAPI)

```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Frontend (React)

```bash
cd frontend
npm run build

# Serve with nginx or any static server
# Built files are in frontend/dist/
```

### Database

For production, use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/job_apply
```

---

## 📊 Performance

- **Applications per day:** 50+ (rate-limited)
- **Cover letter generation:** 10-20s per letter
- **Job match scoring:** 5-10s per job
- **Web dashboard refresh:** 3-5s intervals
- **Test suite execution:** <10s (55+ tests)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [React](https://react.dev/) - UI library
- [Playwright](https://playwright.dev/) - Browser automation
- [Claude Code](https://claude.ai/code) - AI integration
- [TailwindCSS](https://tailwindcss.com/) - Styling
- [Recharts](https://recharts.org/) - Data visualization

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/snandkule/JobApplyTool/issues)
- **Documentation:** [/docs](docs/)
- **Email:** snandkule@gmail.com

---

## 🎉 Project Status

**✅ ALL PHASES COMPLETE**

- ✅ Phase 1: Foundation
- ✅ Phase 2: Core Automation
- ✅ Phase 3: Bulk Auto-Apply Engine
- ✅ Phase 4: Interactive Q&A System
- ✅ Phase 5: AI Integration
- ✅ Phase 6: Web Dashboard
- ✅ Testing & Documentation

**Production Ready!** 🚀

---

**Built with ❤️ and Claude Code**
