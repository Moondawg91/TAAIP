# TWG Dashboard Q&A - Your Questions Answered

## Question 1: How are the Targeting Working Group dashboards updated?

### Current Update Mechanism
The TWG dashboard currently uses **hardcoded mock data** loaded in the `loadTWGData()` function (lines 100-300 of TargetingWorkingGroup.tsx). This means:

- Data is **not persistent** across browser refreshes
- Updates made in the UI are stored in **frontend state only**
- No database integration yet for TWG-specific data

### Available Backend Endpoints (Already Working)
While TWG events/agenda are hardcoded, these endpoints exist and work:
```
GET /api/v2/twg/boards        - Review boards with filters
GET /api/v2/twg/analysis      - Analysis items by priority
GET /api/v2/twg/decisions     - Decisions with dates
GET /api/v2/twg/actions       - Action items with assignments
```

### Future Update Path
To make updates persistent, you need:
1. Database tables for events, agenda, AARs (currently don't exist)
2. POST endpoints to save data (need to be added to taaip_service.py)
3. Frontend API calls to fetch/save data (replace hardcoded loadTWGData())

---

## Question 2: Where does the information feed from?

### Current Data Sources

**Dashboard Statistics:**
- AAR Overdue count: Calculated from hardcoded `aarReports` array
- Budget: Loaded from hardcoded `marketingBudget` object
- Active Events: Hardcoded number (24)
- Must Win Targets: Hardcoded number (8)

**Tables and Lists:**
- **AAR Reports:** Hardcoded array with 4 sample reports
- **Event Data:** Hardcoded in `targetingPhases` array across Q-1 to Q+4
- **Agenda Items:** Hardcoded array of 7 agenda items
- **Phase Information:** Hardcoded phase descriptions

### Database Tables (For Other TWG Data)
These tables **do exist** in the SQLite database:
- `twg_review_boards` - TWG meeting boards
- `twg_analysis_items` - Analyst findings
- `twg_decisions` - Leadership decisions
- `twg_action_items` - Task assignments

### Missing Database Tables
These tables **need to be created** for full functionality:
- `twg_events` - Marketing events
- `twg_agenda_items` - Meeting agenda
- `twg_aar_reports` - After action reports
- `twg_budget` - Budget allocations

---

## Question 3: How do we update the TWG dashboard?

### Currently Available Methods

#### Method 1: UI Forms (Partially Working)
**What Works:**
- "Add Event" button opens modal to create new events
- "Add Recommendation" button opens modal
- Events added through UI are stored in frontend state

**Limitations:**
- Data lost on page refresh (not saved to database)
- No API backend to persist data

**How to Use:**
1. Click "Add Event" button in Intel Brief view
2. Fill out event form (name, date, location, type, budget)
3. Click "Save Event" - adds to frontend state
4. **Data disappears on refresh** ⚠️

#### Method 2: Direct Database Updates (For Existing Tables)
You can update TWG review boards, analysis, decisions, and actions directly:

```sql
-- Connect to database
ssh root@129.212.185.3
docker exec -it taaip_backend_1 sqlite3 /app/recruiting.db

-- Update a TWG review board
UPDATE twg_review_boards 
SET status = 'completed', 
    scheduled_date = '2025-02-15'
WHERE board_id = 'TWG001';

-- Add analysis item
INSERT INTO twg_analysis_items (analysis_id, board_id, analyst_name, findings, priority)
VALUES ('ANAL001', 'TWG001', 'SSG Johnson', 'Market analysis shows...', 'high');
```

#### Method 3: API Calls (For Existing Endpoints)
Use curl or Postman to query existing data:

```bash
# Get all TWG boards
curl http://129.212.185.3:3000/api/v2/twg/boards

# Get high priority analysis
curl http://129.212.185.3:3000/api/v2/twg/analysis?status=active

# Get decisions
curl http://129.212.185.3:3000/api/v2/twg/decisions

# Get action items
curl http://129.212.185.3:3000/api/v2/twg/actions
```

### What's Missing (Needs Development)

**To Make Events Persistent:**
1. Create database table:
```sql
CREATE TABLE twg_events (
  event_id TEXT PRIMARY KEY,
  name TEXT,
  date TEXT,
  location TEXT,
  type TEXT,
  target_audience TEXT,
  expected_leads INTEGER,
  budget INTEGER,
  status TEXT,
  priority TEXT
);
```

2. Add backend endpoint in `taaip_service.py`:
```python
@app.post("/api/v2/twg/events")
async def create_twg_event(event: dict):
    # Insert into twg_events table
    # Return success/failure
```

3. Update frontend to call API instead of using hardcoded data

---

## Question 4: Why don't cards and charts open details when clicked?

### ✅ **NOW FIXED!**

**What Was Wrong:**
- Stat cards had no onClick handlers
- Table rows had no click events
- Event cards were display-only
- No detail modals existed

**What I Fixed (Just Now):**
1. ✅ Added onClick handlers to all 4 stat cards (AAR, Budget, Events, Targets)
2. ✅ Made AAR table rows clickable
3. ✅ Made event table rows clickable in Sync Matrix
4. ✅ Made Intel Brief event cards clickable
5. ✅ Created 4 comprehensive detail modals:
   - AAR Detail Modal - Shows overdue reports with submit buttons
   - Budget Detail Modal - Complete quarterly breakdown
   - Events Detail Modal - Full event list with edit capability
   - Targets Detail Modal - Must Win/Must Keep strategy overview

**How to Test:**
1. Visit http://129.212.185.3
2. Navigate to Targeting Working Group dashboard
3. Click any of the 4 stat cards at top - modal opens
4. Click any row in AAR Status table - modal opens
5. Go to Sync Matrix → click event rows - opens event editor
6. Go to Intel Brief → click event cards - opens event editor

**Visual Changes:**
- Cards now show cursor-pointer on hover
- Cards have shadow lift effect on hover
- Table rows highlight on hover
- All interactive elements have visual feedback

---

## Question 5: How does the agenda get updated?

### Current Agenda System

**Where It Lives:**
The agenda is **hardcoded** in `loadTWGData()` function:

```typescript
const agendaItems: AgendaItem[] = [
  { id: '1', section: 'Call to Order', presenter: 'BDE CDR', status: 'scheduled', notes: '' },
  { id: '2', section: 'Previous Action Items Review', presenter: 'XO', status: 'scheduled', notes: '' },
  { id: '3', section: 'Market Intelligence Briefing', presenter: 'G2', status: 'scheduled', notes: '' },
  { id: '4', section: 'Resource Status & Budget', presenter: 'G8', status: 'scheduled', notes: '' },
  { id: '5', section: 'Dynamic Event Requests', presenter: 'Operations', status: 'scheduled', notes: '' },
  { id: '6', section: 'AAR Review & Lessons Learned', presenter: 'Operations', status: 'scheduled', notes: '' },
  { id: '7', section: 'Next Steps & Taskers', presenter: 'BDE CDR', status: 'scheduled', notes: '' }
];
```

### Agenda Update Process (Current)

**There is no update mechanism yet!** The agenda is fixed in code.

To change the agenda currently, you would need to:
1. Edit the TargetingWorkingGroup.tsx file
2. Modify the hardcoded array
3. Rebuild the frontend (`npm run build`)
4. Deploy to production server

**This is obviously not ideal for regular users!**

### Recommended Agenda System (Future Enhancement)

**Step 1: Create Database Table**
```sql
CREATE TABLE twg_agenda_items (
  id TEXT PRIMARY KEY,
  meeting_id TEXT,
  section TEXT,
  presenter TEXT,
  status TEXT,
  notes TEXT,
  order_index INTEGER,
  FOREIGN KEY (meeting_id) REFERENCES twg_meetings(meeting_id)
);
```

**Step 2: Add Backend Endpoints**
```python
# Get agenda for specific meeting
@app.get("/api/v2/twg/agenda")
async def get_twg_agenda(meeting_id: str = None):
    # Query twg_agenda_items table
    
# Create/Update agenda item
@app.post("/api/v2/twg/agenda")
async def save_agenda_item(item: dict):
    # Insert or update agenda item
    
# Reorder agenda
@app.put("/api/v2/twg/agenda/reorder")
async def reorder_agenda(items: list):
    # Update order_index for all items
```

**Step 3: Add UI Controls**
Add "Edit Agenda" button in Agenda view that:
- Opens modal with draggable agenda items
- Add/remove items
- Change presenters
- Reorder sections
- Save changes to database via API

**Step 4: Fetch on Load**
Replace hardcoded array in `loadTWGData()`:
```typescript
const response = await fetch(`${API_BASE}/api/v2/twg/agenda?meeting_id=${currentMeeting.id}`);
const agendaItems = await response.json();
setCurrentMeeting({...currentMeeting, agenda: agendaItems});
```

---

## Summary Table

| Feature | Current State | Update Mechanism | Data Source |
|---------|--------------|------------------|-------------|
| **Dashboard Stats** | ✅ Clickable | ❌ Hardcoded frontend | React state |
| **AAR Reports** | ✅ Clickable table | ❌ Hardcoded array | React state |
| **Events** | ✅ Clickable rows/cards | ❌ Hardcoded array | React state |
| **Budget** | ✅ Clickable card | ❌ Hardcoded object | React state |
| **Targets** | ✅ Clickable card | ❌ Hardcoded data | React state |
| **Agenda** | ❌ Not clickable | ❌ Hardcoded array | React state |
| **Review Boards** | ✅ Backend exists | ✅ API + Database | SQLite twg_review_boards |
| **Analysis Items** | ✅ Backend exists | ✅ API + Database | SQLite twg_analysis_items |
| **Decisions** | ✅ Backend exists | ✅ API + Database | SQLite twg_decisions |
| **Action Items** | ✅ Backend exists | ✅ API + Database | SQLite twg_action_items |

---

## Quick Action Guide

### To View Details (Working Now ✅)
1. **View AAR Details:** Click "AAR Overdue" card or any AAR table row
2. **View Budget Details:** Click "Budget Remaining" card
3. **View All Events:** Click "Active Events" card
4. **View Targets Strategy:** Click "Must Win Targets" card
5. **Edit Specific Event:** Click any event row in Sync Matrix or event card in Intel Brief

### To Add New Events (Frontend Only ⚠️)
1. Click "Add Event" button (Intel Brief or Events modal)
2. Fill out form
3. Click "Save Event"
4. **Note:** Data not saved to database, will disappear on refresh

### To Make Updates Persistent (Requires Development 🛠️)
1. Create missing database tables (twg_events, twg_agenda_items, twg_aar_reports)
2. Add POST endpoints to taaip_service.py
3. Update frontend to call APIs instead of using hardcoded data
4. Test full create/read/update/delete cycle

---

## Files Modified

- ✅ `TargetingWorkingGroup.tsx` - Added interactivity and modals
- ✅ `TWG_DASHBOARD_DOCUMENTATION.md` - Complete system guide
- ✅ `TWG_INTERACTIVE_FEATURES.md` - Implementation summary
- ✅ `TWG_Q&A.md` - This file

## Deployment Status

- ✅ Built: November 27, 2024
- ✅ Deployed: http://129.212.185.3
- ✅ Tested: All cards and modals working
- ✅ Committed: Git commit 28cdfe1

---

## Need Help?

**For Interactive Features:** All cards and modals are now working! Just click around.

**For Data Persistence:** You'll need to implement the database tables and backend endpoints described above.

**For Troubleshooting:** See `TWG_DASHBOARD_DOCUMENTATION.md` Support & Troubleshooting section.
