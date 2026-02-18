# TAAIP 2.0 - Getting Started with Enterprise Features

## 🚀 Quick Start (What You Just Got)

I've created the **foundation** for your enterprise requirements. Here's what's ready to use:

### ✅ Completed (Phase 1 - Foundation):

1. **Production Database Support**
   - Location: `database/config.py`
   - Supports: PostgreSQL, SQL Server, SQLite (dev)
   - Features: Connection pooling, health checks, automatic migration detection

2. **Data Validation Layer**
   - Location: `validation/data_validator.py`
   - Validates: Leads, Events, Metrics, Projects, Social Media data
   - Features: Army eligibility rules (AR 601-210), PII compliance, data quality scoring

3. **Archival System (No-Delete Policy)**
   - Location: `archival/manager.py`
   - Features: Soft delete, full history tracking, restore capability
   - Compliance: All records preserved indefinitely

4. **Enhanced Database Models**
   - Location: `database/models.py`
   - Features: Archival columns, data quality tracking, sync status

---

## 🎯 What You Need to Do Next

### Option A: Start with SQLite (Quick Start - Development Only)

```bash
# 1. Install dependencies
python3 -m pip install -r requirements.txt

# 2. Run setup script
python3 setup.py

# 3. Start backend
python3 -m uvicorn taaip_service:app --reload --host 0.0.0.0 --port 8000
```

**This will work right now** but is limited to single-user development.

---

### Option B: Set Up PostgreSQL (Recommended for Multi-User)

#### Step 1: Install PostgreSQL

**On macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**On Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Step 2: Create Database

```bash
# Connect to PostgreSQL
psql postgres

# In psql prompt:
CREATE DATABASE taaip_prod;
CREATE USER taaip_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE taaip_prod TO taaip_user;
\q
```

#### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env and set:
# DATABASE_URL=postgresql://taaip_user:secure_password_here@localhost:5432/taaip_prod
```

#### Step 4: Run Setup

```bash
python3 setup.py
```

---

## 📊 What You DON'T Need to Implement (Yet)

### You Asked About These - Here's My Recommendation:

| Feature | Status | When to Implement |
|---------|--------|-------------------|
| **Live EMM Integration** | 🟡 Not yet | Phase 2 (need API credentials) |
| **Sprinklr Integration** | 🟡 Not yet | Phase 2 (need API credentials) |
| **iKrome/Vantage** | 🟡 Not yet | Phase 2-3 |
| **SharePoint** | 🟡 Not yet | Phase 3 (CAC auth required) |
| **Policy Compliance Engine** | 🟡 Not yet | Phase 3 (need policy docs) |
| **Real-time WebSocket** | 🟡 Not yet | Phase 2 (after DB is stable) |

**Why wait?**
- You need API credentials and documentation from USAREC IT
- These integrations build on the foundation we just created
- Get the database working first, then add integrations one at a time

---

## 🔧 Immediate Integration: Update Your Existing Service

Your current `taaip_service.py` uses raw SQLite. Let's migrate it to use the new system:

### Step 1: Update taaip_service.py imports

Add to top of file:
```python
from database.config import get_db
from database.models import Lead, Event, EventMetric, Project
from validation.data_validator import DataValidator, ValidationLogger
from archival.manager import ArchivalManager
from sqlalchemy.orm import Session
from fastapi import Depends
```

### Step 2: Update your endpoints

**Before (raw SQLite):**
```python
@app.post("/api/v2/leads")
async def create_lead(lead: LeadInput):
    conn = get_db_conn()
    conn.execute("INSERT INTO leads ...")
```

**After (with validation & ORM):**
```python
@app.post("/api/v2/leads")
async def create_lead(lead: LeadInput, db: Session = Depends(get_db)):
    # Step 1: Validate
    validation = DataValidator.validate_lead(lead.dict())
    if not validation.passed:
        raise HTTPException(status_code=422, detail={
            "errors": validation.errors,
            "warnings": validation.warnings
        })
    
    # Step 2: Store
    new_lead = Lead(**lead.dict())
    db.add(new_lead)
    db.commit()
    
    # Step 3: Log validation
    await ValidationLogger.log_validation("lead", new_lead.lead_id, validation)
    
    return {"status": "created", "lead_id": new_lead.lead_id}
```

### Step 3: Update delete endpoints to archive

**Before:**
```python
@app.delete("/api/v2/leads/{lead_id}")
async def delete_lead(lead_id: str):
    conn.execute("DELETE FROM leads WHERE lead_id = ?", (lead_id,))
```

**After:**
```python
@app.delete("/api/v2/leads/{lead_id}")
async def archive_lead(lead_id: str, reason: str, db: Session = Depends(get_db)):
    # Get lead data
    lead = db.query(Lead).filter_by(lead_id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404)
    
    # Archive instead of delete
    archive_id = await ArchivalManager.archive_record(
        db=db,
        table_name="leads",
        record_id=lead_id,
        record_data={"lead_id": lead.lead_id, "age": lead.age, ...},
        reason=reason,
        archived_by="system",
        soft_delete=True
    )
    
    return {"status": "archived", "archive_id": archive_id}
```

---

## 🎯 Recommended Implementation Plan

### **Phase 1 (This Week): Get Database Running**
- [ ] Choose: PostgreSQL or stick with SQLite for now
- [ ] Run `python3 setup.py`
- [ ] Update 2-3 endpoints in `taaip_service.py` to use new validation
- [ ] Test that archival works

### **Phase 2 (Next 2-4 Weeks): Basic Integration**
- [ ] Get EMM API credentials from USAREC IT
- [ ] Get Sprinklr API credentials from PAO
- [ ] Create first connector (start with simplest API)
- [ ] Add WebSocket real-time updates

### **Phase 3 (1-2 Months): Advanced Features**
- [ ] SharePoint integration
- [ ] Policy compliance engine
- [ ] Remaining API connectors

---

## ❓ Common Questions

### Q: Do I need to implement EVERYTHING you listed?
**A: No!** Start with Phase 1 (database + validation). The rest can wait until you have:
- API access from USAREC systems
- User feedback on what features are most important
- More developers (this is a lot for one person)

### Q: What if I can't get API credentials?
**A: No problem!** You can:
- Use manual CSV imports for now
- Build the dashboard with mock data
- Add integrations later when credentials arrive

### Q: Can I skip PostgreSQL and use SQLite?
**A: For development, yes.** But SQLite won't support:
- Multiple users at the same time
- Large datasets (>100K records)
- Network access (can't connect remotely)

### Q: How do I test the validation?
```python
# Test validation directly
from validation.data_validator import DataValidator

# Good lead
result = DataValidator.validate_lead({"lead_id": "L001", "age": 19, "email": "test@example.com"})
print(result.passed)  # True

# Bad lead (too young)
result = DataValidator.validate_lead({"lead_id": "L002", "age": 16})
print(result.errors)  # ['Age below minimum Army eligibility (17 years)']
```

---

## 🆘 Need Help?

**If you get stuck:**
1. Check `setup.py` output for errors
2. Run database health check: `python3 -c "from database.config import get_db_health; print(get_db_health())"`
3. Look at error logs

**Next conversation, tell me:**
- "I chose PostgreSQL" or "I'm sticking with SQLite"
- "I got API credentials for [system]" (if you have them)
- "I want to start with [specific feature]"

---

## 📁 What Files Were Created

```
TAAIP/
├── database/
│   ├── config.py          # Database connection & setup
│   └── models.py          # SQLAlchemy ORM models
├── validation/
│   └── data_validator.py  # Data validation rules
├── archival/
│   └── manager.py         # Archival & history tracking
├── setup.py               # Automated setup script
├── .env.example           # Environment configuration template
└── requirements.txt       # Updated Python dependencies
```

---

**You now have:** ✅ Database flexibility, ✅ Data validation, ✅ Archival system

**You DON'T need yet:** ⏳ Live APIs, ⏳ SharePoint, ⏳ Real-time updates

**Start here:** Run `python3 setup.py` and let me know if it works!
