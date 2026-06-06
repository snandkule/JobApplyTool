# Web Dashboard Guide

Complete guide for setting up and using the Job Apply Tool web dashboard.

## Architecture

```
┌─────────────────────────────────────────────────┐
│          React Frontend (Port 5173)             │
│  - Dashboard with charts                        │
│  - Application queue viewer                     │
│  - Pending questions interface                  │
│  - Daemon control panel                         │
└───────────────────┬─────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend (Port 8000)             │
│  - REST API endpoints                           │
│  - Real-time WebSocket updates                  │
│  - AI service integration                       │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│              SQLite Database                     │
│  - Applications, jobs, questions                │
│  - Stats, logs, knowledge base                  │
└─────────────────────────────────────────────────┘
```

## Prerequisites

**Backend:**
- Python 3.11+
- All dependencies from `requirements.txt`

**Frontend:**
- Node.js 18+
- npm or yarn

## Installation

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or with poetry
poetry install

# Initialize database (if not done already)
python -m cli.main init
```

### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Create environment file
cp .env.example .env

# (Optional) Edit .env if backend is not on localhost:8000
# VITE_API_URL=http://your-backend-url:8000
```

## Running the Dashboard

### Option 1: Manual Start (Development)

**Terminal 1 - Start Backend:**
```bash
# From project root
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

Access the dashboard at: **http://localhost:5173**

### Option 2: Using Docker Compose (Coming Soon)

```bash
docker-compose up
```

## API Documentation

Once the backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative API docs**: http://localhost:8000/redoc

## Features

### 1. Dashboard

**What it shows:**
- Total applications statistics
- Success rate
- Daily application charts (30 days)
- Status distribution pie chart
- Platform-specific stats
- Today's and this week's activity

**Real-time updates:**
- Auto-refreshes every 5 seconds
- No manual refresh needed

**Example:**
```
┌───────────────────────────────────────────────┐
│ Total Applications: 127                       │
│ Submitted: 98  |  Pending: 5  |  Failed: 24   │
│ Success Rate: 77.2%                           │
└───────────────────────────────────────────────┘

[Chart showing applications over last 30 days]
[Pie chart showing status distribution]
[Platform breakdown: LinkedIn, Indeed, etc.]
```

### 2. Application Queue

**What it shows:**
- All jobs queued for automated application
- Job details (company, title, location)
- Match score (AI-calculated)
- Priority level
- Date added
- Platform badge

**Actions:**
- Remove jobs from queue
- View job details
- Sort by priority

**Real-time updates:**
- Auto-refreshes every 5 seconds
- See new jobs added by daemon

**Example:**
```
┌───────────────────────────────────────────────┐
│ Application Queue                             │
│ 23 jobs in queue                              │
├───────────────────────────────────────────────┤
│ Senior Software Engineer                      │
│ Google • Mountain View, CA • 92% match        │
│ Priority: 8 • Added: Jun 7, 2:30 PM          │
│                                        [Remove]│
├───────────────────────────────────────────────┤
│ ...more jobs...                               │
└───────────────────────────────────────────────┘
```

### 3. Pending Questions

**What it shows:**
- Questions that paused applications
- Job context (company, title)
- Question type (text, yes/no, number)
- When question was asked

**Actions:**
- Answer questions manually
- Get AI suggestions
- Use AI suggestion
- Submit answers

**AI Integration:**
- Click "AI" button for suggestion
- AI analyzes job + profile context
- Suggestion appears in blue box
- One-click to use suggestion

**Real-time updates:**
- Auto-refreshes every 5 seconds
- See new questions as they come in

**Example:**
```
┌───────────────────────────────────────────────┐
│ Pending Questions                             │
├───────────────────────────────────────────────┤
│ Are you willing to relocate?                  │
│ Amazon - Principal Engineer                   │
│ Type: yes_no                                  │
│                                               │
│ 💡 AI Suggestion:                             │
│ "No, I prefer remote work"                    │
│ [Use this suggestion]                         │
│                                               │
│ [Yes] [No]  [AI] [Submit]                     │
└───────────────────────────────────────────────┘
```

### 4. Daemon Control

**What it shows:**
- Daemon running status (live indicator)
- Search criteria
- Queue size
- Applications today vs. daily limit
- Last cycle timestamp
- Recent logs (50 most recent)

**Actions:**
- Start/Stop daemon (via CLI for now)
- View logs in real-time
- Monitor daemon activity

**Real-time updates:**
- Status refreshes every 3 seconds
- Logs refresh every 5 seconds

**Example:**
```
┌───────────────────────────────────────────────┐
│ Daemon Status              ● Running          │
├───────────────────────────────────────────────┤
│ Search: "Senior Engineer"                     │
│ Queue: 23 jobs                                │
│ Today: 15 / 50 applications                   │
│ Last cycle: Jun 7, 3:45:23 PM                 │
├───────────────────────────────────────────────┤
│ Recent Logs:                                  │
│ Jun 7, 3:45:23 PM  INFO    Cycle complete     │
│ Jun 7, 3:45:20 PM  INFO    Applied to Google  │
│ Jun 7, 3:45:15 PM  WARNING Rate limit hit     │
└───────────────────────────────────────────────┘
```

## API Endpoints Reference

### Profile Endpoints

```
GET    /api/profile              Get user profile
POST   /api/profile              Create profile
PUT    /api/profile              Update profile
GET    /api/profile/skills       Get skills
POST   /api/profile/skills       Add skill
GET    /api/profile/resumes      Get resumes
GET    /api/profile/work-history Get work history
GET    /api/profile/education    Get education
```

### Jobs Endpoints

```
GET    /api/jobs                 List jobs
GET    /api/jobs/{id}            Get job details
POST   /api/jobs/queue/add       Add to queue
GET    /api/jobs/queue/list      List queue
DELETE /api/jobs/queue/{id}      Remove from queue
```

### Applications Endpoints

```
GET    /api/applications             List applications
GET    /api/applications/{id}        Get application details
GET    /api/applications/stats/overview        Overview stats
GET    /api/applications/stats/daily           Daily stats
GET    /api/applications/stats/by-platform     Platform stats
```

### Daemon Endpoints

```
GET    /api/daemon/status        Get status
POST   /api/daemon/start         Start daemon
POST   /api/daemon/stop          Stop daemon
GET    /api/daemon/logs          Get logs
GET    /api/daemon/configs       List configs
```

### Questions & AI Endpoints

```
GET    /api/questions/pending              List pending questions
POST   /api/questions/answer               Answer question
POST   /api/questions/batch-answer         Batch answer
POST   /api/questions/suggest              Get AI suggestion
GET    /api/questions/knowledge-base       List knowledge base
GET    /api/questions/stats                Question stats
POST   /api/questions/ai/cover-letter      Generate cover letter
POST   /api/questions/ai/match-score       Calculate match score
POST   /api/questions/ai/analyze-resume    Analyze resume
```

## Workflow Examples

### Example 1: Monitor Running Daemon

1. Start daemon via CLI:
   ```bash
   job-apply daemon start --criteria "Software Engineer" --max-daily 50
   ```

2. Open dashboard: http://localhost:5173

3. Navigate to **Dashboard** to see:
   - Real-time application count
   - Success rate
   - Daily trends

4. Navigate to **Daemon Control** to see:
   - Live status (green dot)
   - Current progress
   - Logs scrolling

### Example 2: Answer Pending Questions

1. Daemon encounters unknown question
2. Application pauses in `PENDING_QUESTIONS` state
3. Dashboard shows notification badge
4. Navigate to **Pending Questions**
5. Click "AI" button for suggestion
6. Review AI suggestion
7. Click "Use this suggestion" or type your own
8. Click "Submit"
9. Application resumes automatically

### Example 3: Review Application Queue

1. Navigate to **Application Queue**
2. See all queued jobs with match scores
3. Review job details
4. Remove low-priority jobs if desired
5. Jobs process automatically when daemon cycles

### Example 4: Analyze Performance

1. Navigate to **Dashboard**
2. Review 30-day application trend chart
3. Check platform-specific success rates
4. Identify best-performing platforms
5. Adjust daemon criteria based on insights

## Customization

### Change API URL

Edit `frontend/.env`:
```env
VITE_API_URL=http://your-backend:8000
```

### Adjust Refresh Intervals

Edit component files:
- Dashboard: `refetchInterval: 5000` (5 seconds)
- Queue: `refetchInterval: 5000`
- Questions: `refetchInterval: 5000`
- Daemon: `refetchInterval: 3000` (3 seconds)

### Customize Theme

Edit `frontend/tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      primary: '#your-color',
      // Add custom colors
    },
  },
}
```

## Troubleshooting

### Backend Won't Start

**Error: Port 8000 already in use**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn backend.app.main:app --port 8001
```

**Error: No module named 'fastapi'**
```bash
# Install FastAPI and dependencies
pip install fastapi uvicorn[standard] websockets
```

### Frontend Won't Start

**Error: Cannot find module**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Error: Port 5173 already in use**
```bash
# Use different port
npm run dev -- --port 5174
```

### API Connection Issues

**CORS errors in browser console:**
- Check backend CORS settings in `backend/app/main.py`
- Ensure frontend URL is in `allow_origins`

**API calls failing:**
- Verify backend is running: http://localhost:8000/api/health
- Check `.env` file has correct `VITE_API_URL`
- Check browser network tab for errors

### Dashboard Shows Old Data

- Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Clear browser cache
- Restart backend if database was updated

## Production Deployment

### Backend

```bash
# Use production ASGI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
# Build for production
cd frontend
npm run build

# Serve with nginx or any static file server
# Built files are in frontend/dist/
```

### Environment Variables

**Backend:**
```env
APP_ENV=production
DATABASE_URL=postgresql://...  # Use PostgreSQL in production
CLAUDE_CLI_PATH=/usr/local/bin/claude
```

**Frontend:**
```env
VITE_API_URL=https://your-api-domain.com
```

## Performance Tips

1. **Database**: Switch to PostgreSQL for production (SQLite is for dev only)
2. **Caching**: Enable Redis caching for API responses
3. **WebSocket**: Use WebSocket for real-time updates (coming soon)
4. **CDN**: Serve frontend assets from CDN
5. **Compression**: Enable gzip compression in uvicorn

## Security Considerations

1. **Authentication**: Add auth middleware in production
2. **HTTPS**: Always use HTTPS in production
3. **API Keys**: Store sensitive config in environment variables
4. **CORS**: Restrict CORS to specific domains
5. **Rate Limiting**: Add rate limiting middleware

## Coming Soon

- [ ] WebSocket for real-time updates
- [ ] User authentication
- [ ] Cover letter editor in UI
- [ ] Job search interface
- [ ] Application history timeline
- [ ] Export reports (PDF, CSV)
- [ ] Dark mode toggle
- [ ] Mobile responsive design improvements

## Support

For issues or questions:
- Check GitHub Issues: https://github.com/snandkule/JobApplyTool/issues
- CLI documentation: `job-apply --help`
- API documentation: http://localhost:8000/docs
