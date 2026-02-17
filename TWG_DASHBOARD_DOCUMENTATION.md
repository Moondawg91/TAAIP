# Targeting Working Group (TWG) Dashboard - Documentation

## Overview
The TWG Dashboard coordinates targeting recommendations, analysis, and decision-making for marketing events and geographical targeting initiatives across Company, Battalion, and Brigade levels.

## Data Sources & Update Mechanisms

### 1. Database Tables (SQLite - `recruiting.db`)

#### `twg_review_boards`
- **Purpose**: Stores TWG meeting/board records
- **Fields**: board_id, name, project_id, event_id, review_type, status, scheduled_date, facilitator, attendees, rsid, brigade, battalion
- **Update Method**: Backend POST endpoints or direct SQL INSERT/UPDATE

#### `twg_analysis_items`
- **Purpose**: Analysis items discussed in TWG meetings
- **Fields**: analysis_id, board_id, analyst_name, analysis_type, findings, recommendations, priority, status
- **Update Method**: Frontend forms → Backend API → Database

#### `twg_decisions`
- **Purpose**: Decisions made during TWG sessions
- **Fields**: decision_id, board_id, decision_text, decision_maker, rationale, status, implementation_date
- **Update Method**: Frontend forms → Backend API → Database

#### `twg_action_items`
- **Purpose**: Action items assigned during TWG meetings
- **Fields**: action_id, board_id, task_description, assigned_to, due_date, status, priority
- **Update Method**: Frontend forms → Backend API → Database

### 2. Backend API Endpoints (`taaip_service.py`)

#### GET Endpoints:
- **`/api/v2/twg/boards`** - Retrieves TWG review boards
  - Filters: status, review_type, rsid
  - Returns: List of TWG boards with attendees and metadata

- **`/api/v2/twg/analysis`** - Gets analysis items
  - Filters: board_id, status
  - Returns: Analysis items sorted by priority

- **`/api/v2/twg/decisions`** - Fetches decisions
  - Filters: board_id, status
  - Returns: Decisions with maker and implementation dates

- **`/api/v2/twg/actions`** - Retrieves action items
  - Filters: board_id, status, assigned_to
  - Returns: Action items with assignments and due dates

#### POST Endpoints (Need to be added):
- **`/api/v2/twg/events`** - Create new events
- **`/api/v2/twg/aar`** - Submit AAR reports
- **`/api/v2/twg/agenda`** - Update agenda items
- **`/api/v2/twg/budget`** - Update budget allocations

### 3. Current Data Flow

```
User Action → Frontend Component → API Call → Backend Endpoint → Database → Response → UI Update
```

#### Example: Adding a New Event
1. User clicks "Add Event" button
2. Modal opens with form fields
3. User fills in: Event name, date, location, type, priority, budget
4. User clicks "Save"
5. Frontend calls `POST /api/v2/twg/events` with data
6. Backend validates and inserts into database
7. Backend returns success response
8. Frontend refreshes event list
9. New event appears in Sync Matrix

## How to Update Information

### A. Through the Dashboard UI

#### 1. Add New Events
- Navigate to: **Intel Brief** or **Sync Matrix** view
- Click: **"Add Event"** button
- Fill in form:
  - Event Name
  - Date
  - Location
  - Type (Event Targeting / Geographic Targeting)
  - Target Audience
  - Expected Leads
  - Budget
  - Priority (Must Keep / Must Win / Standard)
- Click **"Save Event"**

#### 2. Update Agenda Items
- Navigate to: **Agenda** view
- Click on agenda item
- Edit status or add notes
- Changes auto-save

#### 3. Submit AAR Reports
- Navigate to: **Dashboard** view → AAR Status table
- Click on overdue event
- Fill in AAR form
- Submit within 72 hours of event

#### 4. Add Recommendations
- Navigate to: **Recommendations** view
- Click **"Add Recommendation"** button
- Select recommendation type
- Fill in details
- Submit for review

### B. Direct Database Updates

#### Using SQL Commands:
```sql
-- Add a new TWG board
INSERT INTO twg_review_boards (board_id, name, review_type, status, scheduled_date, facilitator, rsid)
VALUES ('TWG_2025_Q1', 'Q1 FY25 Review', 'quarterly', 'scheduled', '2025-01-15', 'MAJ Smith', 'RS001');

-- Add an analysis item
INSERT INTO twg_analysis_items (board_id, analyst_name, analysis_type, findings, recommendations, priority, status)
VALUES ('TWG_2025_Q1', 'SPC Davis', 'market_analysis', 'High potential in downtown area', 'Increase event frequency', 'high', 'pending');

-- Update agenda item status
UPDATE agenda_items SET status = 'completed', notes = 'Reviewed and approved' WHERE id = 'agenda_1';

-- Add budget allocation
INSERT INTO marketing_budget (fy, total_budget, allocated, spent, remaining)
VALUES (2025, 500000, 350000, 125000, 225000);
```

#### Using Backend API (curl examples):
```bash
# Add new TWG board
curl -X POST http://129.212.185.3:3000/api/v2/twg/boards \
  -H "Content-Type: application/json" \
  -d '{"name":"Q2 FY25 Review","review_type":"quarterly","scheduled_date":"2025-04-15","facilitator":"MAJ Smith"}'

# Submit analysis
curl -X POST http://129.212.185.3:3000/api/v2/twg/analysis \
  -H "Content-Type: application/json" \
  -d '{"board_id":"TWG_2025_Q1","analyst_name":"SPC Davis","analysis_type":"market","findings":"High engagement"}'
```

### C. Data Import Methods

#### CSV Upload:
1. Navigate to: **Data Upload** page
2. Select category: **"TWG Data"**
3. Upload CSV with required columns:
   - Events: event_name, date, location, type, priority, budget
   - AARs: event_id, event_name, date, submitted_by
4. System validates and imports automatically

#### Excel/SharePoint Integration:
1. Export data from SharePoint
2. Format as CSV or JSON
3. Use Universal Data Upload feature
4. Select appropriate category

## Agenda Update Process

### Current Implementation:
The agenda is **hardcoded** in the component's `loadTWGData()` function with sample data:

```typescript
agenda_items: [
  { id: 'agenda_1', section: 'Previous QTR Overview', presenter: 'S2', status: 'pending' },
  { id: 'agenda_2', section: 'AAR Due Dates Review', presenter: 'XO', status: 'pending' },
  // ... more items
]
```

### To Make Agenda Dynamic:

#### Option 1: Database-Driven
1. Create `twg_agenda_items` table:
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

2. Add backend endpoint:
```python
@app.get("/api/v2/twg/agenda")
async def get_twg_agenda(meeting_id: str):
    # Query twg_agenda_items table
    # Return ordered list of agenda items
```

3. Update frontend to fetch from API instead of hardcoded data

#### Option 2: Editable in UI
1. Add "Edit Agenda" button in Agenda view
2. Allow adding/removing/reordering agenda items
3. POST changes to `/api/v2/twg/agenda`
4. Store in database
5. Fetch on page load

## Clickable Cards & Charts Enhancement

### Cards That Should Open Details:
1. **AAR Overdue** → Modal showing list of overdue AARs with submit buttons
2. **Budget Remaining** → Detailed budget breakdown by quarter
3. **Active Events** → List of all active events with filters
4. **Must Win Targets** → Map view of priority targets
5. **Event Cards** (in Sync Matrix) → Full event details, edit options, related documents

### Charts That Need Interactivity:
1. **Budget visualization** → Click to see spending trends
2. **Event timeline** → Click date to see all events that day
3. **Priority distribution** → Click segment to filter events

## Missing Functionality to Add

### 1. Real-time Data Sync
- WebSocket connection for live updates during meetings
- Collaborative agenda editing
- Live voting on recommendations

### 2. Document Management
- Upload supporting docs (PowerPoint, Excel, PDFs)
- Link documents to agenda items
- Version control for briefings

### 3. Notifications
- Email reminders for AAR deadlines
- Calendar invites for TWG meetings
- Alerts for budget threshold breaches

### 4. Reporting
- Generate meeting minutes automatically
- Export decisions to PDF
- Send action item summaries

### 5. Historical Tracking
- View past TWG meetings
- Compare quarter-over-quarter performance
- Trend analysis dashboards

## Technical Architecture

### Component Structure:
```
TargetingWorkingGroup.tsx (1394 lines)
├── State Management (lines 1-100)
├── Data Loading (lines 100-300)
├── View Rendering
│   ├── Dashboard View (lines 400-650)
│   ├── Agenda View (lines 650-800)
│   ├── Sync Matrix View (lines 800-1000)
│   ├── Intel Brief View (lines 1000-1200)
│   └── Recommendations View (lines 1200-1300)
└── Modals (lines 1300-1394)
```

### State Variables:
- `currentMeeting`: Active TWG meeting details
- `aarReports`: List of AAR submissions and statuses
- `targetingPhases`: Events organized by quarter (Q-1 to Q+4)
- `marketingBudget`: FY budget allocation and spending
- `viewMode`: Controls which view is displayed
- `selectedQuarter`: Currently selected quarter in Sync Matrix

## Quick Reference Commands

### View Current TWG Data:
```bash
ssh root@129.212.185.3 "sqlite3 /root/TAAIP/recruiting.db 'SELECT * FROM twg_review_boards ORDER BY scheduled_date DESC LIMIT 10;'"
```

### Check Recent Analysis:
```bash
ssh root@129.212.185.3 "sqlite3 /root/TAAIP/recruiting.db 'SELECT * FROM twg_analysis_items WHERE status = \"pending\" ORDER BY priority DESC;'"
```

### Get Action Items:
```bash
ssh root@129.212.185.3 "sqlite3 /root/TAAIP/recruiting.db 'SELECT * FROM twg_action_items WHERE status != \"completed\" ORDER BY due_date;'"
```

### Test API Endpoints:
```bash
# Get TWG boards
curl -s http://129.212.185.3:3000/api/v2/twg/boards | jq '.'

# Get analysis items
curl -s http://129.212.185.3:3000/api/v2/twg/analysis | jq '.'

# Get decisions
curl -s http://129.212.185.3:3000/api/v2/twg/decisions | jq '.'
```

## Support & Troubleshooting

### Common Issues:

**Issue**: Cards/charts not clickable
**Solution**: Add `onClick` handlers and modal state management (see enhancement below)

**Issue**: Agenda not updating
**Solution**: Switch from hardcoded data to database-driven agenda (see Agenda Update Process above)

**Issue**: Data not persisting
**Solution**: Ensure POST endpoints exist and are saving to database, check backend logs

**Issue**: AAR deadlines not accurate
**Solution**: Verify event dates in database, check 72-hour calculation logic

---

**Last Updated**: November 26, 2025
**Version**: 2.0
**Maintainer**: System Administrator
