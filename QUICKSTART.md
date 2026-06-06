# Quick Start Guide

Get started with Job Apply Tool in 5 minutes!

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize the application
./job-apply.sh init-command
```

## Create Your Profile

```bash
# Create profile (interactive)
./job-apply.sh profile create
```

You'll be prompted to enter:
- Full Name
- Email
- Phone
- Location
- LinkedIn URL
- GitHub URL
- Work Authorization
- Visa Sponsorship status
- Available start date

## Add Your Resume

```bash
# Add your resume and set it as default
./job-apply.sh profile add-resume ~/path/to/resume.pdf --default

# Add multiple resumes with titles
./job-apply.sh profile add-resume ~/senior-resume.pdf --title "Senior Engineer"
./job-apply.sh profile add-resume ~/lead-resume.pdf --title "Tech Lead"
```

## Add Your Skills

```bash
# Add technical skills
./job-apply.sh profile add-skill "Python" --category technical --proficiency expert
./job-apply.sh profile add-skill "JavaScript" --category technical --proficiency advanced
./job-apply.sh profile add-skill "React" --category technical --proficiency advanced
./job-apply.sh profile add-skill "SQL" --category technical --proficiency expert

# Add soft skills
./job-apply.sh profile add-skill "Leadership" --category soft
./job-apply.sh profile add-skill "Communication" --category soft

# Add certifications
./job-apply.sh profile add-skill "AWS Certified" --category certification

# View all your skills
./job-apply.sh profile list-skills
```

## View Your Profile

```bash
# See your complete profile
./job-apply.sh profile show
```

## Available Commands

```bash
# Initialize
./job-apply.sh init-command         # Set up database and directories
./job-apply.sh version              # Show version

# Profile Management
./job-apply.sh profile create       # Create/update profile
./job-apply.sh profile show         # View profile
./job-apply.sh profile add-resume   # Add resume
./job-apply.sh profile add-skill    # Add skill
./job-apply.sh profile list-skills  # List all skills

# Authentication (Coming in Phase 2)
./job-apply.sh auth linkedin        # Login to LinkedIn
./job-apply.sh auth indeed          # Login to Indeed
./job-apply.sh auth status          # Check auth status

# Help
./job-apply.sh --help              # Show all commands
./job-apply.sh profile --help      # Show profile commands
```

## What's Next?

Phase 1 is complete! Here's what you can do:

### Now Available:
- ✅ Create and manage your profile
- ✅ Upload multiple resumes
- ✅ Add and organize skills
- ✅ Store work history
- ✅ Track education

### Coming Soon (Phase 2-7):
- 🔜 **Phase 2:** Browser automation for LinkedIn and Indeed
- 🔜 **Phase 3:** Bulk auto-apply engine (100+ jobs/day)
- 🔜 **Phase 4:** Interactive Q&A learning system
- 🔜 **Phase 5:** AI-powered cover letter generation via Claude Code
- 🔜 **Phase 6:** Web dashboard with real-time stats
- 🔜 **Phase 7:** Email integration and analytics

## Configuration

Edit `.env` file (copy from `.env.example`) to customize:

```bash
# Database
DATABASE_URL=sqlite:///./data/job_apply.db

# Rate Limits
LINKEDIN_MAX_PER_DAY=50
INDEED_MAX_PER_DAY=100

# Browser
BROWSER_HEADLESS=True

# AI (Claude Code CLI path)
CLAUDE_CLI_PATH=claude
```

## Troubleshooting

### "No module named 'cli'"
```bash
# Make sure you're in the project directory
cd JobApplyTool
./job-apply.sh --help
```

### "Database not found"
```bash
# Run initialization first
./job-apply.sh init-command
```

### "No profile found"
```bash
# Create a profile first
./job-apply.sh profile create
```

## Data Location

All your data is stored in the `data/` directory:
- `data/job_apply.db` - SQLite database
- `data/resumes/` - Your uploaded resumes
- `data/cover_letters/` - Generated cover letters
- `data/screenshots/` - Debug screenshots

## Need Help?

- 📖 Full documentation: [docs/DESIGN.md](docs/DESIGN.md)
- ✅ Phase 1 completion: [docs/PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md)
- 📝 README: [README.md](README.md)

---

**Ready to automate your job search!** 🚀
