# Enhanced Upload Data System Guide

## Overview

The **Upload Data** system provides a unified interface for bulk importing all types of recruiting pipeline data into TAAIP. This enhanced system supports the complete recruiting lifecycle from initial leads through future soldiers.

## Supported Data Types

### 1. **Leads** 👤
Initial contacts and inquiries from potential recruits.

**Required Fields:**
- `first_name` - First name
- `last_name` - Last name
- `date_of_birth` - Format: YYYY-MM-DD
- `education_code` - HS (High School), SC (Some College), CD (College Degree), etc.
- `phone_number` - Contact phone number
- `lead_source` - Source of lead (social_media, referral, walk_in, event, etc.)
- `prid` - Personnel Record ID

**Optional Fields:**
- `cbsa_code` - Core Based Statistical Area code
- `middle_name` - Middle name or initial
- `address` - Full mailing address
- `asvab_score` - ASVAB test score (1-99)

**Example:**
```csv
first_name,last_name,middle_name,date_of_birth,education_code,phone_number,address,cbsa_code,lead_source,prid,asvab_score
John,Smith,A,2003-05-15,HS,555-1234,123 Main St,41700,social_media,PR123456,75
```

---

### 2. **Prospects** 🎯
Qualified leads that have been contacted and show interest.

**Required Fields:**
- All lead fields PLUS:
- `prospect_status` - contacted, interested, qualified, not_interested, etc.

**Optional Fields:**
- All lead optional fields PLUS:
- `last_contact_date` - Last contact date (YYYY-MM-DD)
- `recruiter_assigned` - Assigned recruiter name/ID
- `notes` - Additional notes about prospect

**Example:**
```csv
first_name,last_name,date_of_birth,education_code,phone_number,lead_source,prid,prospect_status,last_contact_date,recruiter_assigned
Jane,Doe,2002-08-20,SC,555-5678,referral,PR789012,qualified,2025-11-15,SSG Smith
```

---

### 3. **Applicants** 📋
Active applicants in the processing pipeline.

**Required Fields:**
- All lead fields PLUS:
- `application_date` - Application submission date (YYYY-MM-DD)
- `applicant_status` - pending, processing, approved, denied, etc.

**Optional Fields:**
- All lead optional fields PLUS:
- `meps_scheduled_date` - MEPS appointment date
- `recruiter_assigned` - Assigned recruiter
- `mos_preference` - Preferred Military Occupational Specialty

**Example:**
```csv
first_name,last_name,date_of_birth,education_code,phone_number,lead_source,prid,application_date,applicant_status,meps_scheduled_date,mos_preference,asvab_score
Mike,Johnson,2001-12-10,HS,555-9012,walk_in,PR345678,2025-10-01,processing,2025-11-25,11B,82
```

---

### 4. **Future Soldiers** 🎖️
Contracted soldiers awaiting their ship date.

**Required Fields:**
- All lead fields PLUS:
- `contract_date` - Contract signing date (YYYY-MM-DD)
- `ship_date` - Scheduled ship to basic training date (YYYY-MM-DD)
- `mos_assigned` - Assigned MOS
- `future_soldier_status` - active, delayed, discharged, etc.

**Optional Fields:**
- All lead optional fields PLUS:
- `recruiter_assigned` - Assigned recruiter
- `unit_assignment` - Assigned unit information

**Example:**
```csv
first_name,last_name,date_of_birth,education_code,phone_number,lead_source,prid,contract_date,ship_date,mos_assigned,future_soldier_status,unit_assignment,asvab_score
Sarah,Williams,2003-03-22,HS,555-3456,event,PR901234,2025-09-15,2026-01-10,68W,active,A Co 1-50 IN,88
```

---

### 5. **Events** 📅
Recruiting events and activities.

**Required Fields:**
- `name` - Event name
- `location` - Event location
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)

**Optional Fields:**
- `type` - school_visit, career_fair, community_event, etc.
- `budget` - Event budget amount
- `team_size` - Number of team members
- `targeting_principles` - D3AE, F3A, etc.
- `status` - planned, active, completed, cancelled

---

### 6. **Projects** 📊
Project management and tracking.

**Required Fields:**
- `name` - Project name
- `owner_id` - Project owner/manager
- `start_date` - Start date (YYYY-MM-DD)
- `target_date` - Target completion date (YYYY-MM-DD)
- `objectives` - Project objectives description

**Optional Fields:**
- `event_id` - Related event ID
- `funding_amount` - Project funding
- `status` - planning, in_progress, completed, on_hold

---

### 7. **Marketing Activities** 📢
Marketing campaigns and initiatives.

**Required Fields:**
- `activity_name` - Activity/campaign name
- `campaign_type` - social_media, digital, print, radio, tv, etc.
- `start_date` - Campaign start date (YYYY-MM-DD)
- `end_date` - Campaign end date (YYYY-MM-DD)
- `budget_allocated` - Allocated budget amount

**Optional Fields:**
- `target_audience` - Target demographic description
- `channels` - Marketing channels used
- `leads_generated` - Number of leads generated
- `cost_per_lead` - Cost per lead metric
- `status` - active, completed, paused, cancelled

---

### 8. **Budgets** 💰
Budget allocation and tracking.

**Required Fields:**
- `campaign_name` - Campaign/initiative name
- `allocated_amount` - Total allocated budget
- `start_date` - Budget period start (YYYY-MM-DD)
- `end_date` - Budget period end (YYYY-MM-DD)

**Optional Fields:**
- `event_id` - Related event ID
- `spent_amount` - Amount spent to date
- `remaining_amount` - Remaining budget
- `fiscal_year` - Fiscal year (e.g., "2025")

---

## How to Use

### Step 1: Access Upload Data
1. Navigate to your TAAIP dashboard: `http://129.212.185.3`
2. Click the menu dropdown
3. Select **"Upload Data"** under Operations

### Step 2: Select Data Type
Use the dropdown menu to select which type of data you're uploading:
- Leads
- Prospects
- Applicants
- Future Soldiers
- Events
- Projects
- Marketing Activities
- Budgets

### Step 3: Download Template (Recommended)
1. Click **"Download Template"** button
2. Opens a CSV file with:
   - Correct column headers
   - Example row with sample data
   - All required and optional fields

### Step 4: Prepare Your Data
1. Open the template in Excel, Google Sheets, or CSV editor
2. Replace example row with your actual data
3. Add as many rows as needed
4. Ensure all **required fields** have values
5. Save as CSV or Excel (.xlsx, .xls)

### Step 5: Upload File
1. **Drag and drop** file onto upload area, OR
2. Click **"Browse Files"** to select file
3. File name and size will display
4. Click **"Upload [Data Type]"** button

### Step 6: Review Results
- **Success:** Shows number of imported records
- **Errors:** Lists any rows that failed with specific error messages
- **Partial Success:** Shows both imported count and error details

---

## Data Format Guidelines

### Date Formats
Always use **YYYY-MM-DD** format:
- ✅ Correct: `2003-05-15`, `2025-12-01`
- ❌ Wrong: `05/15/2003`, `12-01-25`, `2003/05/15`

### Phone Numbers
Any format accepted:
- `555-1234`
- `(555) 123-4567`
- `555.123.4567`
- `5551234567`

### Education Codes
Standard codes:
- `HS` - High School Graduate
- `SC` - Some College
- `CD` - College Degree
- `GED` - GED Equivalent
- `AD` - Advanced Degree

### Lead Sources
Common values:
- `social_media` - Social media campaigns
- `referral` - Personal referrals
- `walk_in` - Walk-in to recruiting station
- `event` - Recruiting event
- `phone` - Phone inquiry
- `website` - Website form
- `email` - Email inquiry

### Status Values

**Prospect Status:**
- `contacted` - Initial contact made
- `interested` - Expressed interest
- `qualified` - Meets qualifications
- `not_interested` - Not interested
- `follow_up` - Requires follow-up

**Applicant Status:**
- `pending` - Application pending review
- `processing` - In processing
- `approved` - Approved for enlistment
- `denied` - Application denied
- `withdrawn` - Applicant withdrew

**Future Soldier Status:**
- `active` - Active future soldier
- `delayed` - Delayed entry program
- `discharged` - DEP discharge
- `shipped` - Already shipped to training

---

## Common Issues & Solutions

### Issue: "Missing required columns"
**Problem:** File doesn't contain all required fields
**Solution:** 
1. Download the template for your data type
2. Ensure all required columns are present
3. Column names must match exactly (case-sensitive)

### Issue: "Row X: Invalid date format"
**Problem:** Date not in YYYY-MM-DD format
**Solution:** 
- Convert dates to YYYY-MM-DD format
- In Excel: Format cells as Custom → `yyyy-mm-dd`
- In Google Sheets: Format → Number → Custom → `yyyy-mm-dd`

### Issue: "Age must be between 17 and 42"
**Problem:** Date of birth calculates to age outside range
**Solution:**
- Verify date_of_birth is correct
- Ensure format is YYYY-MM-DD
- Check for typos (e.g., 2003 vs 2030)

### Issue: Some rows imported, some failed
**Problem:** Data validation errors in specific rows
**Solution:**
1. Review error messages for specific row numbers
2. Fix data in those rows
3. Re-upload only the corrected rows

---

## Best Practices

### Data Preparation
1. **Start with template** - Always download and use provided templates
2. **Validate before upload** - Check data in Excel/Sheets first
3. **Use consistent formats** - Especially for dates and codes
4. **Test with small batch** - Upload 5-10 rows first to verify format

### Field Naming
- **Be consistent** - Use same education codes, lead sources, statuses
- **Avoid special characters** - Stick to letters, numbers, spaces, hyphens
- **Use standard abbreviations** - SSG, MOS codes, state abbreviations

### Large Uploads
- **Batch processing** - Upload in groups of 500-1000 records
- **Check for duplicates** - System may reject duplicate PRIDs
- **Validate results** - Review import summary after each batch

### Data Quality
- **Complete required fields** - All required fields must have values
- **Accurate dates** - Double-check all dates for accuracy
- **Valid codes** - Use standard military/recruiting codes
- **Clean phone numbers** - Remove extra characters if causing issues

---

## Integration with Other Features

### After Upload → Smart Visualizations
1. Navigate to **Smart Visualizations** dashboard
2. Auto-generated charts will include your new data
3. KPIs update automatically
4. Visualizations adapt to data types uploaded

### After Upload → Standard Dashboards
Your uploaded data populates existing dashboards:
- **Lead Status** - Shows leads, prospects, applicants
- **Event Performance** - Displays uploaded events
- **Project Management** - Lists uploaded projects
- **Budget Tracker** - Shows budget allocations

### Pipeline Flow
Track individuals through the recruiting pipeline:
1. Upload as **Lead** → Initial contact
2. Update to **Prospect** → Qualified and interested
3. Convert to **Applicant** → Active processing
4. Transition to **Future Soldier** → Contracted and awaiting ship

---

## API Endpoints

All uploads use the `/api/v2/upload/` endpoint:

```bash
# Upload leads
POST /api/v2/upload/leads
Content-Type: multipart/form-data
Body: file (CSV/Excel)

# Upload prospects
POST /api/v2/upload/prospects

# Upload applicants
POST /api/v2/upload/applicants

# Upload future soldiers
POST /api/v2/upload/future_soldiers

# Upload events
POST /api/v2/upload/events

# Upload projects
POST /api/v2/upload/projects

# Upload marketing activities
POST /api/v2/upload/marketing_activities

# Upload budgets
POST /api/v2/upload/budgets

# Get templates
GET /api/v2/upload/templates
```

---

## Deployment Instructions

### On DigitalOcean Droplet:

```bash
cd /opt/TAAIP
chmod +x deploy-enhanced-upload.sh
./deploy-enhanced-upload.sh
```

Or manually:
```bash
cd /opt/TAAIP
git pull origin feat/optimize-app
python3 migrate_pipeline_tables.py
/usr/bin/docker-compose down
/usr/bin/docker-compose up -d --build
```

---

## Troubleshooting

### Backend Issues
Check logs:
```bash
cd /opt/TAAIP
docker-compose logs backend
```

### Database Issues
Verify tables exist:
```bash
cd /opt/TAAIP
sqlite3 data/recruiting.db ".tables"
```

### Frontend Issues
Check browser console (F12) for JavaScript errors

---

## Support & Documentation

- **This Guide:** Complete upload system documentation
- **BULK_UPLOAD_GUIDE.md:** Original upload feature documentation
- **DYNAMIC_DASHBOARD_GUIDE.md:** Smart visualizations documentation
- **Backend Logs:** `/opt/TAAIP/logs/backend.log`
- **Database:** `/opt/TAAIP/data/recruiting.db`

---

**Upload Data System** - Unified pipeline data management for TAAIP! 🚀
