# 🚀 START TODAY - Your First 24 Hours

**Goal**: By end of today, you'll have the project fully bootstrapped and ready for Week 1 Day 2.

---

## 📋 MORNING CHECKLIST (30 min)

Run these in order:

### 1. Clone Your GitHub Repo (5 min)
```bash
cd ~/projects  # or wherever you keep code
git clone https://github.com/[YOUR_USERNAME]/credit-risk-monitor.git
cd credit-risk-monitor

# Verify git is working
git status
```

### 2. Set Up Virtual Environment (5 min)
```bash
# Create venv
python3.11 -m venv venv

# Activate it
source venv/bin/activate
# (On Windows: venv\Scripts\activate)

# Verify prompt shows (venv)
# You should see: (venv) user@machine credit-risk-monitor $
```

### 3. Start Docker PostgreSQL (5 min)
```bash
# Create docker-compose.yml if you don't have it
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: credit_risk
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# Start it
docker-compose up -d

# Verify it's running
docker-compose ps
# Should show: postgres | Up | 5432
```

### 4. Check This Document Exists (5 min)
```bash
# These files should be in your project root
ls -la | grep -E "(STARTUP_PLAN|DAILY_STANDUP|CLAUDE_CODE)"

# Should show:
# STARTUP_PLAN_WEEK1-8.md
# DAILY_STANDUP_LOG.md
# CLAUDE_CODE_WORKFLOW.md
```

If they don't exist, Claude can create them. But you should have them already in your GitHub repo setup.

---

## 🎬 MAIN WORK SESSION (2-3 hours)

### Task 1: Claude Code - Bootstrap Project Structure (30 min)

**What you'll do:**
- Open your IDE (VSCode, PyCharm, etc.)
- Have Claude Code extension ready
- Run the first Claude Code command

**Run this:**
```bash
# In your terminal (with venv activated)
# Copy-paste this command to Claude Code:

claude-code "Set up complete project directory structure for Credit Risk Monitor:
- Create src/ subdirectories: collectors, processors, models, rag, alerts, api, db, utils
- Create tests/ subdirectories: unit/, integration/
- Create infra/, dashboard/, scripts/, docs/, notebooks/
- Create all __init__.py files in src/ and tests/
- Initialize git repo (if not already)
- List the final directory tree when done using: tree -L 2"
```

**What to expect:**
- Claude Code will create all directories
- Shows tree structure at end
- You'll see files appear in your IDE

**Verify:**
```bash
# After Claude Code is done, run:
find . -type d -name "__init__" | head
# Should show multiple __init__.py files
```

---

### Task 2: Claude Code - Create requirements.txt (15 min)

```bash
claude-code "Create requirements.txt with these base Python packages (Week 1 only, minimal):
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
pandas==2.1.3
requests==2.31.0
beautifulsoup4==4.12.2
pytest==7.4.3
pytest-cov==4.1.0
loguru==0.7.2

Add a comment at top explaining this is Week 1 base dependencies.
Show me the file when done."
```

**Verify:**
```bash
# Install dependencies
pip install -r requirements.txt

# Should complete without errors
# If error on psycopg2, that's OK for now (PostgreSQL driver can be tricky)
# We'll fix that when we test database connection
```

---

### Task 3: Claude Code - Create .env Template (10 min)

```bash
claude-code "Create .env.template file with:
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk

# News APIs
NEWSAPI_KEY=your_newsapi_key_here
GDELT_API=http://gdelt.io

# LLM
ANTHROPIC_API_KEY=your_claude_api_key_here

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=true
BATCH_SIZE=50
MAX_WORKERS=4

Add comments explaining each section.
Show the file when done."
```

**After this:**
```bash
# Create actual .env from template
cp .env.template .env

# Add your real API keys to .env
# Edit .env and fill in:
# - NEWSAPI_KEY=sk-... (from newsapi.org)
# - ANTHROPIC_API_KEY=sk-ant-... (from Anthropic console)
```

---

### Task 4: Cowork - Verify Environment (10 min)

```
Cowork Action:
1. In terminal, with venv activated:
   python -c "import fastapi; print('✅ fastapi working')"
   python -c "import sqlalchemy; print('✅ sqlalchemy working')"

2. Check Docker:
   docker-compose ps
   (should show postgres UP)

3. Check psql connection:
   psql -U postgres -d credit_risk -c "SELECT 1;"
   (if this works, database connection is good)

4. Check .env loading:
   python -c "from dotenv import load_dotenv; load_dotenv(); print('✅ .env loaded')"

Report results.
```

---

### Task 5: Claude Code - Create SQLAlchemy Models (45 min)

This is the biggest task. Claude Code will:
- Create `src/db/models.py`
- Define all 6 data models
- Add proper relationships and constraints

```bash
claude-code "Write src/db/models.py with complete SQLAlchemy models:

1. Base = declarative_base()

2. Article model:
   - id (PK), title, content, url (UNIQUE), source, published_at, fetched_at, language, raw_json
   - Timestamps: created_at, updated_at

3. Obligor model:
   - id (PK), name, ticker, lei, sector, country
   - Timestamps

4. ProcessedArticle model:
   - id (PK), article_id (FK to Article), cleaned_text, entities (JSON), 
   - sentiment_score (Float), sentiment_label, is_credit_relevant (Bool), event_types (Array)
   - Timestamps

5. ArticleObliger model (many-to-many):
   - article_id (FK), obligor_id (FK), both are PKs

6. Alert model:
   - id (PK), obligor_id (FK), triggered_at, severity, summary
   - event_types (JSON), article_ids (JSON), metadata (JSON)
   - Timestamps

7. ObligorDailySignals model:
   - id (PK), obligor_id (FK), date, neg_article_count, avg_sentiment, credit_relevant_count
   - Timestamps

Requirements:
- Use proper primary keys, foreign keys, unique constraints
- Add indexes for common queries (url, published_at, obligor_id)
- Include docstrings for each model
- Use proper imports from sqlalchemy
- All datetime fields should default to func.now()
- All models should have created_at, updated_at auto-timestamps

Show me the complete file when done."
```

**Verify after Claude Code completes:**
```bash
# Python should be able to import it
python -c "from src.db.models import Article, Obligor; print('✅ Models import OK')"
```

---

### Task 6: Claude Code - Create DB Connection Module (15 min)

```bash
claude-code "Write src/db/connection.py that:

1. Import create_engine, sessionmaker from sqlalchemy
2. Import Base from src.db.models
3. Load DATABASE_URL from environment (or hardcode for now)

4. Create:
   - engine = create_engine(DATABASE_URL)
   - SessionLocal = sessionmaker(bind=engine)

5. Implement functions:
   - get_db(): yields SessionLocal() session (for FastAPI)
   - init_db(): calls Base.metadata.create_all(bind=engine)
   - test_connection(): connects to DB and prints 'Database connected: [version]'

6. __main__ block:
   - Calls test_connection()
   - Prints 'Database initialized!' if successful

Include proper error handling and logging.
Show the file when done."
```

**Verify:**
```bash
# This is the big test — does it connect to database?
python src/db/connection.py

# Should output: "Database connected: PostgreSQL 15.x..."
# If error about connection, database might not be running
# Check: docker-compose ps
```

---

### Task 7: Cowork - Initialize Alembic (10 min)

```
Cowork Action:
1. Activate venv
2. Run: alembic init infra/migrations
3. This creates alembic/ directory structure
4. Report: "✅ Alembic initialized"
```

---

### Task 8: Claude Code - Create Utility Modules (30 min)

```bash
claude-code "Write three utility modules:

1. src/utils/config.py
   - Use pydantic BaseSettings
   - Load from .env
   - Fields: DATABASE_URL, NEWSAPI_KEY, ANTHROPIC_API_KEY, LOG_LEVEL, ENVIRONMENT, DEBUG, BATCH_SIZE, MAX_WORKERS
   - Create singleton: settings = Settings()
   - Include docstrings and type hints

2. src/utils/logger.py
   - Use loguru
   - setup_logger(name: str) function
   - Console output with formatting
   - File logging optional
   - Return logger instance

3. src/utils/constants.py
   - EVENT_TYPES = list of credit event types
   - SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
   - KEYWORDS = dict mapping event types to keywords

Show all three files when done."
```

**Verify:**
```bash
python -c "from src.utils.config import settings; print(f'✅ Config loaded: {settings.environment}')"
```

---

### Task 9: Claude Code - Create Obligor Seed Script (20 min)

```bash
claude-code "Write scripts/seed_obligors.py that:

1. Import models and SessionLocal from src.db

2. Define OBLIGORS list with 50 companies:
   [
     {'name': 'Apple Inc.', 'ticker': 'AAPL', 'sector': 'Technology', 'country': 'USA'},
     {'name': 'Microsoft Corporation', 'ticker': 'MSFT', ...},
     ...more companies...
   ]

   Include: FAANG (Apple, Microsoft, Google, Amazon, Meta), Major banks (JPMorgan, Goldman Sachs, Bank of America, Citigroup, Wells Fargo), Tech (Tesla, NVIDIA, Intel, AMD, Cisco), Pharma (Pfizer, Moderna, J&J), Energy (Exxon, Chevron, Shell), Aerospace (Boeing, Airbus), Media (Netflix, Disney), Consumer (Coca-Cola, Pepsi), Industrial (3M, Caterpillar), Automotive (Ford, GM)

3. Function seed_obligors():
   - Create SessionLocal
   - For each company:
     * Check if ticker already exists (don't duplicate)
     * Create Obligor instance
     * Add to session
   - Commit
   - Print 'Seeded 50 obligors'

4. __main__ block calls seed_obligors()

Show me the obligors list when done (just the first 5 as example)."
```

**Verify (Cowork will do this on Day 2):**
```bash
# We'll run this tomorrow after Alembic migration
python scripts/seed_obligors.py
```

---

### Task 10: Claude Code - Initial Git Commit (10 min)

```bash
claude-code "Commit everything to git:

1. Create .gitignore with:
   __pycache__/
   *.py[cod]
   .Python
   venv/
   env/
   .env
   .DS_Store
   *.log
   .pytest_cache/
   .coverage

2. Run:
   git add .
   git commit -m 'Initial: project structure, database models, utilities, scripts'

3. Show git log (last 3 commits)

Don't push yet—we'll do that tomorrow when everything is tested."
```

**Verify:**
```bash
git log --oneline -5
# Should show your initial commit
```

---

## ✅ END OF DAY CHECKLIST

By end of today, you should have:

- [ ] venv created + activated (showing `(venv)` in terminal)
- [ ] Docker PostgreSQL running (`docker-compose ps` shows UP)
- [ ] Project structure created (see `tree -L 2` output)
- [ ] requirements.txt installed successfully
- [ ] .env.template created + copied to .env + filled with your keys
- [ ] SQLAlchemy models written (`src/db/models.py`)
- [ ] Database connection working (`python src/db/connection.py` succeeds)
- [ ] Alembic initialized (`alembic/` directory exists)
- [ ] Utility modules created (`src/utils/config.py`, `logger.py`, `constants.py`)
- [ ] Obligor seeding script written (`scripts/seed_obligors.py`)
- [ ] Git initialized + first commit made

---

## 📝 UPDATE LOGS

Add this to `DAILY_STANDUP_LOG.md`:

```markdown
## Week 1, Day 1: [TODAY'S DATE]

✅ COMPLETED:
- Project structure: ✅ All directories created
- venv + dependencies: ✅ Installed
- Docker PostgreSQL: ✅ Running
- Database models: ✅ 6 models defined
- Database connection: ✅ Tested and working
- Utilities: ✅ config, logger, constants
- Obligor seeding script: ✅ Ready (will run tomorrow)
- Git: ✅ Initial commit done

🚧 IN PROGRESS:
- Alembic migration: Created, will apply tomorrow

🚨 BLOCKERS:
- None

📊 METRICS:
- Files created: 15+
- Lines of code: 1200+
- Commits: 1
- Tests written: 0 (starting tomorrow)

🎯 NEXT 24H:
- Apply Alembic migration
- Seed 50 obligors
- Create NewsAPI collector module
```

And update `session-log.md`:

```markdown
## Week 1, Day 1 - Bootstrap

### Completed
- ✅ Full project bootstrapping
- ✅ Database schema designed + models created
- ✅ Environment setup (venv, Docker, .env)
- ✅ Utilities and seeding scripts

### Blockers
- None

### Next Step
- Day 2: Apply Alembic migration, seed obligors, start NewsAPI collector

### Notes
- All dependencies installed successfully
- Database connection confirmed working
- Ready to begin data collection
```

---

## 🎯 IF YOU GET STUCK

### "PostgreSQL connection fails"
```bash
# Check if Docker is running
docker-compose ps

# If not, start it
docker-compose up -d

# If still fails, try resetting
docker-compose down
docker-compose up -d
```

### "ImportError: No module named 'sqlalchemy'"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Claude Code command didn't work"
```bash
# Make sure you:
1. Have Claude Code extension installed in your IDE
2. Are in project root directory
3. Have venv activated in your IDE terminal
4. Paste the exact command
```

---

## 🚀 YOU'RE READY!

Go through the checklist above in order. Each task takes 10-45 minutes.

By tonight, you'll have:
- ✅ Complete project scaffold
- ✅ Database design finalized
- ✅ Ready to collect data tomorrow

**Total time: ~3-4 hours**

---

**Start with Task 1 now. Good luck! 💪**

Questions? Review `CLAUDE_CODE_WORKFLOW.md` for detailed Claude Code instructions.
