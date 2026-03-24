# Troubleshooting Guide - Credit Risk Monitor

## 🔧 Common Problems and Solutions

This guide helps you fix the most common issues you'll encounter.

---

## Problem 1: "Command not found" Error

### Symptoms
```bash
$ python app.py
bash: python: command not found
```

### Diagnosis Flowchart
```
Is Python installed?
├─ No → Install Python 3.11+ from python.org
└─ Yes → Try these:
    ├─ Use 'python3' instead of 'python'
    ├─ Check PATH: echo $PATH
    └─ Reinstall Python with "Add to PATH" checked
```

### Solutions

**Solution 1: Use python3**
```bash
python3 --version
python3 your_script.py
```

**Solution 2: Check if Python is installed**
```bash
# Mac/Linux
which python
which python3

# Windows
where python
```

**Solution 3: Reinstall Python**
1. Download from https://python.org
2. During installation, CHECK "Add Python to PATH"
3. Restart terminal

---

## Problem 2: Virtual Environment Won't Activate

### Symptoms
```bash
$ source venv/bin/activate
# Nothing happens, no (venv) appears
```

### Diagnosis Flowchart
```
Does venv/ folder exist?
├─ No → Create it: python -m venv venv
└─ Yes → Check your OS:
    ├─ Mac/Linux → Use: source venv/bin/activate
    ├─ Windows CMD → Use: venv\Scripts\activate
    └─ Windows PowerShell → 
        ├─ Try: venv\Scripts\Activate.ps1
        └─ If error → Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Solutions

**For Mac/Linux:**
```bash
# Make sure you're in project directory
cd ~/projects/credit-risk-monitor

# Activate
source venv/bin/activate

# Verify (should see (venv) at start of line)
which python
```

**For Windows PowerShell:**
```powershell
# First time: Allow scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1

# Verify
Get-Command python
```

**For Windows Command Prompt:**
```cmd
venv\Scripts\activate
```

**If nothing works - recreate venv:**
```bash
# Delete old one
rm -rf venv/          # Mac/Linux
rmdir /s /q venv\     # Windows

# Create new one
python -m venv venv

# Try activating again
```

---

## Problem 3: Package Installation Fails

### Symptoms
```bash
$ pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement...
```

### Diagnosis Flowchart
```
Check these in order:
1. Is virtual environment activated?
   └─ See (venv) at start of line?
2. Is pip up to date?
   └─ Run: pip install --upgrade pip
3. Do you have internet connection?
   └─ Test: ping google.com
4. Are there typos in requirements.txt?
   └─ Check file carefully
```

### Solutions

**Solution 1: Activate venv and upgrade pip**
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Solution 2: Install packages one by one**
```bash
# Find which package is failing
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
# ... continue with each package
```

**Solution 3: Check Python version**
```bash
python --version
# Should be 3.11 or higher

# If not, some packages won't work
```

**Solution 4: Clear pip cache**
```bash
pip cache purge
pip install -r requirements.txt
```

---

## Problem 4: Database Connection Failed

### Symptoms
```bash
$ python src/db/connection.py
sqlalchemy.exc.OperationalError: could not connect to server
```

### Diagnosis Flowchart
```
Is Docker running?
├─ No → Start Docker Desktop
└─ Yes → Is database container running?
    ├─ No → docker-compose up -d
    └─ Yes → Check connection details:
        ├─ Is .env file correct?
        ├─ Is port 5432 available?
        └─ Can you connect manually?
```

### Solutions

**Solution 1: Start Docker and Database**
```bash
# 1. Open Docker Desktop app
# 2. Wait for it to fully start (1-2 minutes)

# 3. Start database
docker-compose up -d

# 4. Check status
docker-compose ps
# Should show: credit-risk-db is Up
```

**Solution 2: Check Database is Healthy**
```bash
# Check logs
docker-compose logs postgres

# Test connection
docker exec credit-risk-db pg_isready -U postgres

# Should output: accepting connections
```

**Solution 3: Verify .env File**
```bash
# Check your .env file has:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk

# No spaces around =
# Make sure it matches docker-compose.yml settings
```

**Solution 4: Restart Database**
```bash
# Stop database
docker-compose down

# Start fresh
docker-compose up -d

# Wait 10 seconds
sleep 10

# Test again
python src/db/connection.py
```

**Solution 5: Port 5432 Already in Use**
```bash
# Check what's using port 5432
lsof -i :5432              # Mac/Linux
netstat -ano | findstr :5432   # Windows

# If something else is using it, either:
# 1. Stop that service
# 2. Change port in docker-compose.yml:
#    ports:
#      - "5433:5432"  # Use 5433 on host
#    And update .env:
#    DATABASE_URL=postgresql://postgres:postgres@localhost:5433/credit_risk
```

---

## Problem 5: Import Error - Module Not Found

### Symptoms
```bash
$ python src/db/connection.py
ModuleNotFoundError: No module named 'sqlalchemy'
```

### Diagnosis Flowchart
```
Is virtual environment activated?
├─ No → Activate: source venv/bin/activate
└─ Yes → Is package installed?
    ├─ No → pip install package-name
    └─ Yes → Wrong Python?
        └─ Check: which python (should point to venv)
```

### Solutions

**Solution 1: Activate Virtual Environment**
```bash
# You MUST be in the venv to use installed packages
source venv/bin/activate

# Verify
which python
# Should show: .../credit-risk-monitor/venv/bin/python
```

**Solution 2: Install Missing Package**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific package
pip install sqlalchemy
```

**Solution 3: Check Python Path**
```bash
# In Python
python
>>> import sys
>>> print(sys.executable)
# Should point to: .../venv/bin/python

# If not, recreate venv
```

**Solution 4: Wrong Directory**
```bash
# Make sure you're in project root
cd ~/projects/credit-risk-monitor

# Then run
python src/db/connection.py
```

---

## Problem 6: Git Push/Pull Fails

### Symptoms
```bash
$ git push
fatal: 'origin' does not appear to be a git repository
```

### Solutions

**Solution 1: Add Remote Repository**
```bash
# If this is your first time pushing
git remote add origin https://github.com/yourusername/credit-risk-monitor.git

# Verify
git remote -v
```

**Solution 2: Authentication Issues**
```bash
# GitHub now requires personal access tokens
# Go to: GitHub.com → Settings → Developer Settings → Personal Access Tokens
# Generate token with 'repo' permissions
# Use token as password when prompted
```

**Solution 3: Check Branch Name**
```bash
# See current branch
git branch

# If not on 'main', switch to it
git checkout main

# Push
git push origin main
```

---

## Problem 7: Docker Won't Start

### Symptoms
```bash
$ docker-compose up -d
Cannot connect to the Docker daemon
```

### Solutions

**Solution 1: Start Docker Desktop**
1. Find Docker Desktop application
2. Start it
3. Wait 1-2 minutes for it to fully start
4. Look for Docker icon in system tray
5. Try command again

**Solution 2: Docker Not Installed**
```bash
# Check if Docker is installed
docker --version

# If not found, install from:
# https://www.docker.com/products/docker-desktop
```

**Solution 3: Restart Docker**
1. Quit Docker Desktop completely
2. Restart your computer
3. Open Docker Desktop
4. Wait for it to start
5. Try again

---

## Problem 8: Code Changes Not Taking Effect

### Symptoms
- You edit code but see old behavior
- API still shows old response

### Solutions

**Solution 1: Restart the Server**
```bash
# Stop server: Ctrl+C

# Start again
uvicorn src.api.main:app --reload
# The --reload flag should auto-reload, but sometimes needs manual restart
```

**Solution 2: Check You're Editing Right File**
```bash
# Make sure you're in the right directory
pwd

# Find the file
find . -name "filename.py"
```

**Solution 3: Python Cache Issues**
```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} +

# Or
find . -name "*.pyc" -delete
```

---

## Problem 9: Tests Failing

### Symptoms
```bash
$ pytest
================================ FAILURES ================================
```

### Solutions

**Solution 1: Read the Error Message**
```bash
# Run tests with verbose output
pytest -v

# Show print statements
pytest -s

# Stop at first failure
pytest -x
```

**Solution 2: Test One File at a Time**
```bash
# Test specific file
pytest tests/unit/test_collectors.py

# Test specific function
pytest tests/unit/test_collectors.py::test_fetch_news
```

**Solution 3: Check Test Database**
```bash
# Tests might need a separate test database
# Check if tests are using correct config

# Run with test environment
ENVIRONMENT=test pytest
```

---

## Problem 10: Can't Access API/Dashboard

### Symptoms
- Browser shows "This site can't be reached"
- http://localhost:8000 doesn't load

### Solutions

**Solution 1: Is the Server Running?**
```bash
# Check your terminal - do you see:
# "Uvicorn running on http://127.0.0.1:8000"

# If not, start it:
uvicorn src.api.main:app --reload
```

**Solution 2: Try Different URLs**
```bash
# Try these variations:
http://localhost:8000
http://127.0.0.1:8000
http://0.0.0.0:8000
```

**Solution 3: Port Already in Use**
```bash
# Check if port 8000 is busy
lsof -i :8000              # Mac/Linux
netstat -ano | findstr :8000   # Windows

# Use different port
uvicorn src.api.main:app --reload --port 8001
# Then access: http://localhost:8001
```

**Solution 4: Firewall Blocking**
```bash
# Temporarily disable firewall to test
# (Don't forget to re-enable!)

# Or add exception for Python/uvicorn
```

---

## Emergency Recovery Procedures

### Complete Reset (Nuclear Option)

**⚠️ WARNING: This deletes everything! Only use as last resort.**

```bash
# 1. Backup your code if you have changes
git status
git stash  # Saves changes temporarily

# 2. Stop everything
docker-compose down -v
deactivate

# 3. Delete virtual environment
rm -rf venv/

# 4. Delete database data
docker volume rm credit-risk-monitor_postgres_data

# 5. Start fresh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
python src/db/connection.py

# 6. Restore your code if needed
git stash pop
```

---

## Diagnostic Commands

### System Health Check

Run this script to check everything:

```bash
#!/bin/bash
echo "=== Credit Risk Monitor Health Check ==="

echo "1. Python version:"
python --version || echo "❌ Python not found"

echo "2. Virtual environment:"
[ -d "venv" ] && echo "✅ venv exists" || echo "❌ venv missing"
[[ $VIRTUAL_ENV == *"venv"* ]] && echo "✅ venv active" || echo "⚠️ venv not active"

echo "3. Docker:"
docker --version || echo "❌ Docker not found"
docker ps > /dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

echo "4. Database:"
docker-compose ps | grep -q "Up" && echo "✅ Database running" || echo "❌ Database not running"

echo "5. Key files:"
[ -f ".env" ] && echo "✅ .env exists" || echo "❌ .env missing"
[ -f "requirements.txt" ] && echo "✅ requirements.txt exists" || echo "❌ requirements.txt missing"
[ -f "docker-compose.yml" ] && echo "✅ docker-compose.yml exists" || echo "❌ docker-compose.yml missing"

echo "6. Python packages:"
pip list | grep -q "fastapi" && echo "✅ FastAPI installed" || echo "❌ FastAPI missing"
pip list | grep -q "sqlalchemy" && echo "✅ SQLAlchemy installed" || echo "❌ SQLAlchemy missing"

echo "=== End Health Check ==="
```

Save as `health_check.sh`, make executable (`chmod +x health_check.sh`), and run (`./health_check.sh`)

---

## Getting Help

### Still Stuck?

1. **Check error message carefully**
   - Copy exact error text
   - Google: "python [error message]"

2. **Review documentation**
   - COMPLETE_BEGINNER_GUIDE.md
   - COMMAND_CHEAT_SHEET.md
   - QUICK_START.md

3. **Use Claude Code**
   ```bash
   claude "I'm getting this error: [paste error]. How do I fix it?"
   ```

4. **Check official docs**
   - Python: https://docs.python.org
   - Docker: https://docs.docker.com
   - FastAPI: https://fastapi.tiangolo.com
   - SQLAlchemy: https://docs.sqlalchemy.org

5. **Community resources**
   - Stack Overflow: https://stackoverflow.com
   - Reddit: r/learnpython, r/Python
   - Discord: Python Discord server

---

## Prevention Tips

### Avoid Problems Before They Happen

✅ **Always activate venv** before working
✅ **Commit frequently** - easy to rollback if something breaks
✅ **Test after changes** - catch issues early
✅ **Keep notes** - document what works
✅ **Read error messages** - don't ignore warnings
✅ **Update regularly** - but test in dev first
✅ **Backup important data** - export database before big changes

---

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Command not found | Use `python3` instead of `python` |
| Module not found | Activate venv: `source venv/bin/activate` |
| Database won't connect | `docker-compose restart` |
| Port in use | Use different port or kill process |
| Changes not showing | Restart server (Ctrl+C, then up arrow, Enter) |
| Git issues | Check you're on right branch: `git branch` |
| Docker issues | Restart Docker Desktop app |
| Tests failing | Run with `-v` flag to see details |
| Can't import module | Check you're in project root: `pwd` |
| Permission denied | Use `sudo` (Linux/Mac) or run as Administrator (Windows) |

---

**Remember**: Every error is a learning opportunity! 🎓

The more errors you fix, the better developer you become.
