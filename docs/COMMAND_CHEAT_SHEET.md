# Command Cheat Sheet - Credit Risk Monitor Project

## 📌 Quick Reference for Daily Development

---

## Starting Your Work Session

```bash
# 1. Navigate to project
cd ~/projects/credit-risk-monitor

# 2. Activate virtual environment
source venv/bin/activate              # Mac/Linux
venv\Scripts\activate                 # Windows CMD
venv\Scripts\Activate.ps1             # Windows PowerShell

# 3. Check database is running
docker-compose ps

# 4. If database is not running, start it
docker-compose up -d
```

**You know you're ready when:**
- Terminal shows `(venv)` at the start
- `docker-compose ps` shows database is "Up"

---

## Essential Git Commands

### Saving Your Work
```bash
# Check what changed
git status

# See specific changes
git diff

# Add all changes
git add .

# Commit with message
git commit -m "Description of what you did"

# View commit history
git log --oneline
```

### Undoing Mistakes
```bash
# Undo changes to a file (before adding)
git checkout -- filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

---

## Docker Commands

### Basic Operations
```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# View running containers
docker-compose ps

# View logs
docker-compose logs -f postgres

# Restart database
docker-compose restart

# Complete reset (DELETES ALL DATA!)
docker-compose down -v
```

### Troubleshooting
```bash
# Database won't start? Check Docker is running
docker ps

# View detailed logs
docker-compose logs --tail=50 postgres

# Force rebuild
docker-compose up -d --force-recreate
```

---

## Python Virtual Environment

### Activation
```bash
# Mac/Linux
source venv/bin/activate

# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell (if you get permission error first time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### Deactivation
```bash
deactivate
```

### Managing Packages
```bash
# Install a new package
pip install package-name

# Install from requirements.txt
pip install -r requirements.txt

# Update requirements.txt
pip freeze > requirements.txt

# List installed packages
pip list

# Uninstall a package
pip uninstall package-name
```

---

## Database Commands

### Using psql (PostgreSQL CLI)
```bash
# Connect to database
docker exec -it credit-risk-db psql -U postgres -d credit_risk

# Once connected, useful commands:
\dt                    # List all tables
\d table_name          # Describe a table
\q                     # Quit
```

### SQL Queries
```sql
-- Count articles
SELECT COUNT(*) FROM articles;

-- View recent articles
SELECT id, title, published_at FROM articles 
ORDER BY published_at DESC LIMIT 10;

-- Count by source
SELECT source, COUNT(*) FROM articles 
GROUP BY source;

-- Clear all data (CAREFUL!)
TRUNCATE articles, obligors, processed_articles CASCADE;
```

### Python Database Operations
```bash
# Create/update database tables
python src/db/connection.py

# Seed obligor data
python scripts/seed_obligors.py

# Collect initial data
python scripts/collect_initial_data.py

# Verify data
python scripts/verify_data.py
```

---

## Running Your Application

### API Server (FastAPI)
```bash
# Start development server
uvicorn src.api.main:app --reload

# Access at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Dashboard (Streamlit)
```bash
# Start dashboard
streamlit run dashboard/app.py

# Access at: http://localhost:8501
```

### Both at Once (Different Terminals)
```bash
# Terminal 1
uvicorn src.api.main:app --reload

# Terminal 2 (new terminal, remember to activate venv!)
streamlit run dashboard/app.py
```

---

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_collectors.py

# Run tests with output
pytest -v

# Run tests and stop at first failure
pytest -x
```

### Quick Manual Tests
```bash
# Test configuration
python src/utils/config.py

# Test database connection
python src/db/connection.py

# Test news collector
python src/collectors/news_api.py
```

---

## File Operations

### Creating Files
```bash
# Create a Python file
touch src/collectors/new_file.py

# Create with content
cat > filename.py << 'EOF'
# Your code here
EOF
```

### Editing Files
```bash
# Open in VS Code
code filename.py

# Open entire project in VS Code
code .

# Using nano (terminal editor)
nano filename.py
# Ctrl+X to exit, Y to save
```

### Viewing Files
```bash
# View entire file
cat filename.py

# View first 10 lines
head filename.py

# View last 10 lines
tail filename.py

# View with line numbers
cat -n filename.py
```

---

## Navigation

### Directory Commands
```bash
# Where am I?
pwd

# List files
ls              # Mac/Linux
dir             # Windows

# List with details
ls -la          # Mac/Linux
dir /a          # Windows

# Go to project root
cd ~/projects/credit-risk-monitor

# Go up one level
cd ..

# Go to previous directory
cd -

# Go to home directory
cd ~
```

### Finding Things
```bash
# Find files by name
find . -name "*.py"

# Search within files
grep -r "search_term" src/

# Count Python files
find src/ -name "*.py" | wc -l
```

---

## Environment Variables

### View Current Variables
```bash
# View all
env

# View specific variable
echo $DATABASE_URL          # Mac/Linux
echo %DATABASE_URL%         # Windows CMD
$env:DATABASE_URL           # Windows PowerShell
```

### Load from .env File
```python
# In Python
from dotenv import load_dotenv
load_dotenv()

import os
api_key = os.getenv("NEWSAPI_KEY")
```

---

## Claude Code Commands

### Getting Help
```bash
# General help
claude "How do I implement sentiment analysis?"

# Code generation
claude "Create a function to clean HTML from text"

# Debugging
claude "Why am I getting this error: [paste error]"

# Architecture questions
claude "What's the best way to structure my API routes?"
```

---

## Common Workflows

### Starting a New Feature
```bash
# 1. Make sure you're on main branch
git checkout main

# 2. Update code (if working with others)
git pull

# 3. Create feature branch
git checkout -b feature/my-new-feature

# 4. Do your work...
# 5. Test it
pytest

# 6. Commit
git add .
git commit -m "Add my new feature"

# 7. Merge back to main
git checkout main
git merge feature/my-new-feature
```

### Daily Work Routine
```bash
# Morning
cd ~/projects/credit-risk-monitor
source venv/bin/activate
docker-compose up -d
git status

# Work on code...

# End of day
git add .
git commit -m "Daily progress: [what you did]"
docker-compose down
deactivate
```

### Collecting Fresh News Data
```bash
# Make sure database is running
docker-compose up -d

# Activate environment
source venv/bin/activate

# Run collector
python scripts/collect_initial_data.py

# Verify
python scripts/verify_data.py
```

---

## Troubleshooting Commands

### Python Issues
```bash
# Check Python version
python --version

# Check pip version
pip --version

# Verify package installed
pip show package-name

# Reinstall package
pip uninstall package-name
pip install package-name
```

### Database Issues
```bash
# Check if database is responding
docker exec credit-risk-db pg_isready

# View database logs
docker-compose logs postgres

# Connect and test query
docker exec -it credit-risk-db psql -U postgres -d credit_risk -c "SELECT 1;"

# Restart database
docker-compose restart postgres
```

### Port Conflicts
```bash
# Check what's using port 5432
lsof -i :5432              # Mac/Linux
netstat -ano | findstr :5432   # Windows

# Kill process on port (Mac/Linux)
kill -9 $(lsof -ti:5432)
```

---

## Useful Shortcuts

### Terminal
- `Ctrl + C` - Stop running program
- `Ctrl + D` - Exit/Logout
- `Ctrl + L` - Clear screen (or type `clear`)
- `Ctrl + R` - Search command history
- `↑` / `↓` - Navigate command history
- `Tab` - Auto-complete

### VS Code
- `Ctrl + `` - Toggle terminal
- `Ctrl + P` - Quick file open
- `Ctrl + Shift + P` - Command palette
- `Ctrl + /` - Toggle comment
- `Ctrl + S` - Save
- `Ctrl + F` - Find in file
- `Ctrl + Shift + F` - Find in project

---

## Quick Reference Files

### Check these when stuck:
```bash
# Project structure explained
cat .claude/claude.md

# Week-by-week tasks
cat IMPLEMENTATION_ROADMAP.md

# Setup help
cat QUICK_START.md

# Complete beginner guide
cat COMPLETE_BEGINNER_GUIDE.md
```

---

## Emergency: Reset Everything

**Only use this if you need to start completely fresh!**

```bash
# 1. Deactivate virtual environment
deactivate

# 2. Stop and remove database
docker-compose down -v

# 3. Delete virtual environment
rm -rf venv/               # Mac/Linux
rmdir /s venv\            # Windows

# 4. Recreate virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Start database and recreate tables
docker-compose up -d
python src/db/connection.py

# 6. Seed data
python scripts/seed_obligors.py
```

---

## Helpful Aliases (Optional)

Add these to your shell configuration (`~/.bashrc` or `~/.zshrc`):

```bash
# Credit Risk Monitor shortcuts
alias crm='cd ~/projects/credit-risk-monitor'
alias crmenv='cd ~/projects/credit-risk-monitor && source venv/bin/activate'
alias crmdb='docker-compose up -d'
alias crmtest='pytest -v'
alias crmapi='uvicorn src.api.main:app --reload'
alias crmdash='streamlit run dashboard/app.py'
```

After adding, reload: `source ~/.bashrc`

Then you can just type:
```bash
crmenv          # Go to project and activate venv
crmdb           # Start database
crmapi          # Start API server
```

---

## Remember

✅ **Always activate virtual environment** before running Python code
✅ **Commit frequently** with clear messages
✅ **Test after every change** to catch issues early
✅ **Read error messages** - they usually tell you exactly what's wrong
✅ **Don't panic** - everyone makes mistakes, Git has your back!

---

**Bookmark this file!** You'll reference it constantly. 📌

For detailed explanations, see COMPLETE_BEGINNER_GUIDE.md
