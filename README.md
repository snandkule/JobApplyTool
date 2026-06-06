# Job Apply Tool

AI-powered job application automation tool that can auto-apply to hundreds of jobs with intelligent Q&A learning and Claude Code integration.

## Features

- 🤖 **Bulk Auto-Apply** - Apply to 200-500 jobs/week automatically
- 🧠 **Interactive Q&A Learning** - Learns from your answers and builds a knowledge base
- 🔗 **Claude Code Integration** - Uses your current Claude session (no API tokens needed!)
- 📊 **Smart Job Matching** - AI-powered filtering and scoring
- 🌐 **Multi-Platform** - LinkedIn, Indeed, and custom career pages
- 📈 **Analytics Dashboard** - Track applications, response rates, and success metrics

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Claude Code CLI (for AI features)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/JobApplyTool.git
cd JobApplyTool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or with development dependencies:
```bash
pip install -e ".[dev]"
```

3. Install Playwright browsers (for web automation):
```bash
playwright install
```

4. Initialize the application:
```bash
python -m cli.main init
```

This will:
- Create necessary directories
- Initialize the database
- Set up configuration

## Quick Start

### 1. Create Your Profile

```bash
# Create profile interactively
python -m cli.main profile create

# Add your resume
python -m cli.main profile add-resume ~/Documents/resume.pdf --default

# Add skills
python -m cli.main profile add-skill "Python" --category technical --proficiency expert
python -m cli.main profile add-skill "React" --category technical --proficiency advanced
```

### 2. View Your Profile

```bash
python -m cli.main profile show
```

### 3. List Your Skills

```bash
python -m cli.main profile list-skills
```

## Project Structure

```
JobApplyTool/
├── backend/
│   └── app/
│       ├── api/              # API endpoints (Phase 4+)
│       ├── automation/       # Browser automation (Phase 2+)
│       ├── ai/               # Claude Code integration (Phase 3+)
│       ├── models/           # Database models ✅
│       ├── services/         # Business logic (Phase 2+)
│       ├── database/         # Database session ✅
│       └── config.py         # Configuration ✅
├── cli/
│   ├── commands/             # CLI commands ✅
│   │   ├── init.py          # Initialize command ✅
│   │   ├── profile.py       # Profile management ✅
│   │   └── auth.py          # Authentication (stub)
│   └── main.py              # CLI entry point ✅
├── data/                    # User data directory ✅
│   ├── resumes/             # Uploaded resumes
│   ├── cover_letters/       # Generated cover letters
│   └── screenshots/         # Debug screenshots
├── docs/                    # Documentation ✅
│   └── DESIGN.md           # Complete design document ✅
├── tests/                   # Test suite (Phase 6+)
├── .env.example            # Environment variables template ✅
├── requirements.txt        # Python dependencies ✅
└── README.md               # This file ✅
```

## Development Status

### ✅ Phase 1 Complete: Foundation
- [x] Project structure
- [x] Database models (User, Job, Application, Queue, Q&A)
- [x] Basic CLI commands
- [x] Profile management
- [x] Configuration system

### 🚧 Coming in Phase 2: Core Automation
- [ ] Playwright browser automation
- [ ] LinkedIn Easy Apply automation
- [ ] Indeed Quick Apply automation
- [ ] Basic batch processor

### 🔮 Future Phases
- **Phase 3**: Bulk Auto-Apply Engine (daemon, queue, rate limiting)
- **Phase 4**: Interactive Q&A System (pending questions, knowledge base)
- **Phase 5**: AI Integration (Claude Code CLI for cover letters)
- **Phase 6**: Web Dashboard (React frontend)
- **Phase 7**: Polish (analytics, notifications, email integration)

See [docs/DESIGN.md](docs/DESIGN.md) for the complete roadmap.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:
- `DATABASE_URL` - Database connection string
- `LINKEDIN_MAX_PER_DAY` - Daily application limit for LinkedIn
- `INDEED_MAX_PER_DAY` - Daily application limit for Indeed
- `CLAUDE_CLI_PATH` - Path to Claude Code CLI executable
- `BROWSER_HEADLESS` - Run browser in headless mode

## Database Schema

The tool uses SQLAlchemy with SQLite (default) or PostgreSQL for data storage:

- **UserProfile** - Personal information, contact details, preferences
- **Resume** - Uploaded resumes with tags and metadata
- **WorkHistory** - Employment history
- **Skill** - Skills database with proficiency levels
- **Education** - Educational background
- **Job** - Job listings from various platforms
- **Application** - Application tracking with status
- **ApplicationQueue** - Queue for batch processing
- **PendingQuestion** - Questions needing user answers
- **KnowledgeBase** - Learned answers for reuse
- **DailyStats** - Daily application statistics

## Testing

Run tests (once implemented in Phase 6):

```bash
pytest
```

## Contributing

This is a personal project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- See [docs/DESIGN.md](docs/DESIGN.md) for detailed documentation

## Roadmap

See the complete 14-week implementation plan in [docs/DESIGN.md](docs/DESIGN.md).

Current focus: **Phase 1 - Foundation** ✅

---

**Built with** ❤️ **and Claude Code**
