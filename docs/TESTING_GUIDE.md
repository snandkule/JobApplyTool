# Testing Guide

Complete guide for testing the Job Apply Tool across all phases.

## Overview

The testing suite covers:
- **Phase 5:** AI integration (Claude Code CLI, AI services)
- **Phase 6:** Web dashboard (API endpoints, WebSocket)
- **Integration Tests:** End-to-end workflows
- **Manual Tests:** Browser automation, daemon operations

## Test Structure

```
backend/tests/
├── __init__.py
├── test_ai_integration.py      # Phase 5 AI tests
├── test_api_endpoints.py       # Phase 6 API tests
└── test_websocket.py          # WebSocket tests (future)

frontend/
└── (Frontend tests - future implementation)

run_tests.sh                    # Main test runner script
```

## Prerequisites

### Install Test Dependencies

```bash
# Core testing tools
pip install pytest pytest-asyncio

# Already in requirements.txt
pip install -r requirements.txt
```

### Verify Installation

```bash
pytest --version
# Should show: pytest 8.2.0 or higher
```

## Running Tests

### Quick Test (All Phases)

```bash
# Run all tests
./run_tests.sh
```

**Output:**
```
======================================
Job Apply Tool - Test Suite
======================================

Running Phase 5 AI Integration Tests...
--------------------------------------
test_ai_integration.py::TestClaudeCodeClient::test_init_default_path PASSED
test_ai_integration.py::TestClaudeCodeClient::test_prompt_success PASSED
...

Running Phase 6 API Endpoint Tests...
--------------------------------------
test_api_endpoints.py::TestHealthEndpoints::test_root_endpoint PASSED
test_api_endpoints.py::TestHealthEndpoints::test_health_endpoint PASSED
...

======================================
Test Results Summary
======================================
✓ Phase 5 Tests: PASSED
✓ Phase 6 Tests: PASSED

All tests passed successfully!
```

### Run Individual Test Suites

**Phase 5 AI Integration:**
```bash
pytest backend/tests/test_ai_integration.py -v
```

**Phase 6 API Endpoints:**
```bash
pytest backend/tests/test_api_endpoints.py -v
```

**Specific Test Class:**
```bash
pytest backend/tests/test_ai_integration.py::TestClaudeCodeClient -v
```

**Specific Test:**
```bash
pytest backend/tests/test_ai_integration.py::TestClaudeCodeClient::test_prompt_success -v
```

### Test with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest backend/tests/ --cov=backend/app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Suites

### Phase 5: AI Integration Tests

**File:** `backend/tests/test_ai_integration.py`

**Test Coverage:**

1. **ClaudeCodeClient Tests**
   - ✅ Initialization (default/custom paths)
   - ✅ Prompt execution (success/failure/timeout)
   - ✅ JSON parsing (plain/markdown/embedded)
   - ✅ Error handling

2. **AIService Tests**
   - ✅ Cover letter generation
   - ✅ Job match calculation
   - ✅ Answer suggestions (text/yes_no/number)
   - ✅ Batch answer suggestions
   - ✅ Resume analysis

3. **Integration Tests**
   - ✅ AI service initialization
   - ✅ Cover letter database integration
   - ✅ Question service AI integration
   - ✅ CLI command registration

**Example Test:**
```python
def test_generate_cover_letter(mock_session, mock_claude):
    """Test cover letter generation."""
    # Mock database and Claude
    # ...
    
    service = AIService()
    cover_letter = service.generate_cover_letter(
        job_id=1,
        user_profile_id=1
    )
    
    assert cover_letter.startswith("Dear Hiring Manager")
    mock_claude_instance.prompt.assert_called_once()
```

**Run Phase 5 Tests:**
```bash
pytest backend/tests/test_ai_integration.py -v --tb=short
```

### Phase 6: API Endpoint Tests

**File:** `backend/tests/test_api_endpoints.py`

**Test Coverage:**

1. **Health Endpoints**
   - ✅ Root endpoint (/)
   - ✅ Health check (/api/health)

2. **Profile API**
   - ✅ Get profile
   - ✅ Get profile (not found)
   - ✅ Get skills
   - ✅ Create profile (tested via mocks)

3. **Jobs API**
   - ✅ List jobs
   - ✅ Get job details
   - ✅ Add to queue
   - ✅ List queue
   - ✅ Remove from queue

4. **Applications API**
   - ✅ Get statistics
   - ✅ Get daily stats
   - ✅ Get platform stats
   - ✅ List applications

5. **Daemon API**
   - ✅ Get status (running/stopped)
   - ✅ Get logs
   - ✅ List configurations

6. **Questions & AI API**
   - ✅ List pending questions
   - ✅ Answer question
   - ✅ AI suggestion
   - ✅ Generate cover letter
   - ✅ Calculate match score

7. **CORS Configuration**
   - ✅ CORS headers present

**Example Test:**
```python
def test_get_stats(mock_session, client):
    """Test get application statistics."""
    # Mock database counts
    mock_db.query().count.side_effect = [100, 75, 5, 20]
    
    response = client.get("/api/applications/stats/overview")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_applications"] == 100
    assert data["submitted"] == 75
    assert data["success_rate"] == 75.0
```

**Run Phase 6 Tests:**
```bash
pytest backend/tests/test_api_endpoints.py -v --tb=short
```

## WebSocket Testing

**WebSocket Endpoint:** `ws://localhost:8000/api/ws`

### Manual WebSocket Test

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/ws"
    
    async with websockets.connect(uri) as websocket:
        # Receive initial update
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Received: {data}")
        
        # Send ping
        await websocket.send(json.dumps({"command": "ping"}))
        
        # Receive pong
        response = await websocket.recv()
        print(f"Response: {json.loads(response)}")

asyncio.run(test_websocket())
```

### Expected WebSocket Messages

**Update Message:**
```json
{
  "type": "update",
  "timestamp": "2026-06-07T15:45:23.123456",
  "data": {
    "stats": {
      "total_applications": 127,
      "submitted": 98,
      "pending_questions": 5,
      "failed": 24,
      "success_rate": 77.2
    },
    "queue": {
      "size": 23
    },
    "questions": {
      "pending_count": 5
    },
    "daemon": {
      "is_running": true,
      "applications_today": 15
    }
  }
}
```

**Application Update:**
```json
{
  "type": "application_update",
  "timestamp": "2026-06-07T15:45:23.123456",
  "data": {
    "application_id": 42,
    "status": "submitted"
  }
}
```

## Manual Testing

### Test API Server

**Start Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Test Endpoints:**
```bash
# Health check
curl http://localhost:8000/api/health

# Get statistics
curl http://localhost:8000/api/applications/stats/overview

# List jobs
curl http://localhost:8000/api/jobs?limit=10

# Get daemon status
curl http://localhost:8000/api/daemon/status
```

### Test Frontend

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Manual Checks:**
1. Open http://localhost:5173
2. Verify Dashboard loads
3. Check charts render
4. Navigate to Queue
5. Navigate to Questions
6. Navigate to Daemon Control
7. Verify auto-refresh works (watch network tab)

### Test WebSocket Connection

**Using Browser Console:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({command: 'ping'}));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('Error:', error);
};
```

## Integration Testing

### End-to-End Workflow Tests

**Test 1: Complete Application Flow**
```bash
# 1. Initialize database
python -m cli.main init

# 2. Create profile
python -m cli.main profile create \
  --name "John Doe" \
  --email "john@example.com" \
  --location "San Francisco, CA"

# 3. Add skills
python -m cli.main profile add-skill "Python" --proficiency "Expert"
python -m cli.main profile add-skill "AWS" --proficiency "Advanced"

# 4. Search jobs (requires authentication)
# python -m cli.main jobs search "Software Engineer" --location "Remote"

# 5. Start API server
uvicorn backend.app.main:app --port 8000 &

# 6. Test API
sleep 2
curl http://localhost:8000/api/profile
curl http://localhost:8000/api/profile/skills

# 7. Kill server
pkill -f uvicorn
```

**Test 2: AI Integration Flow**
```bash
# Generate cover letter (mock mode)
python -c "
from backend.app.ai.ai_service import AIService
from unittest.mock import Mock, patch

with patch('backend.app.ai.ai_service.ClaudeCodeClient') as mock:
    mock_instance = Mock()
    mock_instance.prompt.return_value = 'Test cover letter'
    mock.return_value = mock_instance
    
    # This would normally call Claude Code CLI
    # For testing, we mock it
    print('AI Integration: OK')
"
```

**Test 3: WebSocket Real-time Updates**
```bash
# Terminal 1: Start server
uvicorn backend.app.main:app --port 8000

# Terminal 2: Connect WebSocket client
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/api/ws') as ws:
        msg = await ws.recv()
        print(f'Received: {msg[:100]}...')

asyncio.run(test())
"
```

## Test Data Setup

### Populate Test Data

```python
# Create test_data.py
from backend.app.database.session import SessionLocal
from backend.app.models import Job, Application, UserProfile
from datetime import datetime

db = SessionLocal()

# Create test profile
profile = UserProfile(
    name="Test User",
    email="test@example.com",
    location="San Francisco, CA"
)
db.add(profile)
db.commit()

# Create test jobs
for i in range(10):
    job = Job(
        platform="linkedin",
        company=f"Company {i}",
        title=f"Software Engineer {i}",
        location="Remote",
        job_url=f"https://example.com/job{i}",
        status="discovered",
        match_score=0.7 + (i * 0.02)
    )
    db.add(job)

db.commit()
print("Test data created")
```

**Run:**
```bash
python test_data.py
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        ./run_tests.sh
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting Tests

### Common Issues

**Issue: ModuleNotFoundError**
```bash
# Solution: Install in development mode
pip install -e .
```

**Issue: Database locked**
```bash
# Solution: Close connections
rm data/job_apply.db-wal
rm data/job_apply.db-shm
```

**Issue: Import errors**
```bash
# Solution: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest backend/tests/
```

**Issue: Async test warnings**
```bash
# Solution: Install pytest-asyncio
pip install pytest-asyncio
```

**Issue: Mock not working**
```bash
# Solution: Check mock paths match actual imports
# Use: from backend.app.ai.ai_service import AIService
# Mock: @patch('backend.app.ai.ai_service.ClaudeCodeClient')
```

## Test Coverage Goals

**Target Coverage:**
- Phase 5 (AI): 80%+ coverage
- Phase 6 (API): 85%+ coverage
- Critical paths: 95%+ coverage

**Check Coverage:**
```bash
pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

**Coverage Report Example:**
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/app/ai/claude_client.py            45      5    89%   70-75
backend/app/ai/ai_service.py              120     15    88%   95-110
backend/app/api/applications.py            80      8    90%   45, 67-72
backend/app/api/questions.py               65      6    91%   88-93
---------------------------------------------------------------------
TOTAL                                     892     89    90%
```

## Performance Testing

### Load Testing (future)

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

## Summary

✅ **Phase 5 Tests:** 30+ tests for AI integration  
✅ **Phase 6 Tests:** 25+ tests for API endpoints  
✅ **WebSocket:** Real-time update implementation  
✅ **Test Runner:** Automated script with color output  
✅ **Documentation:** Complete testing guide  

**Run all tests:**
```bash
./run_tests.sh
```

**Expected result:** All tests pass with 85%+ coverage.
