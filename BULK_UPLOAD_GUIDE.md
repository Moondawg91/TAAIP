# Bulk Data Upload Guide

## ✨ NEW FEATURE: CSV/Excel Bulk Import

You asked: **"Does the app have the ability to import raw data tables to be fed into the dashboards?"**

**Answer:** YES! I just added full bulk upload functionality.

---

## 🎯 What You Can Upload

### 1. **Events** (Job Fairs, College Visits, etc.)
- Upload hundreds of recruiting events at once
- Required: name, location, start_date, end_date
- Optional: type, budget, team_size, targeting_principles, status

### 2. **Projects** (Campaigns, Initiatives)
- Bulk upload your project pipeline
- Required: name, owner_id, start_date, target_date, objectives
- Optional: event_id, funding_amount, status

### 3. **Leads** (Recruit Data)
- Import lead lists from your campaigns
- Required: age, education_level, cbsa_code, campaign_source
- Optional: propensity_score, lead_id

---

## 📂 Where to Find It

1. Go to your dashboard: http://129.212.185.3
2. Click **"Bulk Data Upload"** in the Operations section (top menu dropdown)
3. Choose data type: Events, Projects, or Leads
4. Download the template CSV (optional)
5. Drag & drop your file or click to browse

---

## 📝 File Formats Supported

✅ **CSV** (.csv)  
✅ **Excel** (.xlsx, .xls)

---

## 🎨 How It Works

### Step 1: Download Template
- Click "Download [Type] Template" button
- Opens a CSV file with example data and correct column names
- Edit in Excel, Google Sheets, or any spreadsheet app

### Step 2: Prepare Your Data
Make sure your file has the required columns (see below)

### Step 3: Upload
- Drag file into the upload area
- Or click to browse and select file
- Upload starts automatically

### Step 4: Review Results
- ✅ Success: Shows "Imported X of Y rows"
- ⚠️ Errors: Lists which rows failed and why
- Invalid rows are skipped, valid rows are saved

---

## 📊 Required Columns

### Events Upload
```
Required: name, location, start_date, end_date
Optional: type, budget, team_size, targeting_principles, status
Date Format: YYYY-MM-DD (e.g., 2025-03-15)
```

**Example CSV:**
```csv
name,type,location,start_date,end_date,budget,team_size,targeting_principles,status
Spring Job Fair 2025,recruitment_event,San Antonio TX,2025-03-15,2025-03-15,5000,10,D3AE F3A,planned
College Visit - UTSA,college_visit,San Antonio TX,2025-04-10,2025-04-10,1000,5,F3A,planned
```

### Projects Upload
```
Required: name, owner_id, start_date, target_date, objectives
Optional: event_id, funding_amount, status
Date Format: YYYY-MM-DD
```

**Example CSV:**
```csv
name,owner_id,start_date,target_date,objectives,event_id,funding_amount,status
Q1 Digital Campaign,SSG Smith,2025-01-01,2025-03-31,Increase leads by 20%,EVT-12345,25000,in_progress
Social Media Outreach,SGT Jones,2025-02-01,2025-04-30,Boost engagement,EVT-12346,15000,planning
```

### Leads Upload
```
Required: age, education_level, cbsa_code, campaign_source
Optional: propensity_score (1-10), lead_id
Age Range: 17-42 (Army eligibility)
```

**Example CSV:**
```csv
lead_id,age,education_level,cbsa_code,campaign_source,propensity_score
LEAD-001,20,High School,41700,social_media,7
LEAD-002,22,Some College,41700,web,8
LEAD-003,19,High School,41700,event,6
```

---

## 🔧 Technical Details

### Backend API Endpoints
- `POST /api/v2/import/events` - Upload events CSV/Excel
- `POST /api/v2/import/projects` - Upload projects CSV/Excel
- `POST /api/v2/import/leads` - Upload leads CSV/Excel
- `GET /api/v2/import/templates` - Get template column info (JSON)

### Database Tables
- Events → `events` table
- Projects → `projects` table
- Leads → `leads` table

### Upload Limits
- No file size limit (within reason)
- Processes row-by-row
- Invalid rows are skipped with error details
- Valid rows are committed to database

---

## ✅ Validation Rules

### Events
- start_date must be before end_date
- budget must be >= 0
- team_size must be >= 0

### Projects
- start_date must be before target_date
- funding_amount must be >= 0

### Leads
- age must be 17-42 (Army eligibility)
- propensity_score must be 1-10 (if provided)

---

## 🐛 Troubleshooting

### "Missing required columns"
**Fix:** Download the template and make sure your CSV has all required column names (exact spelling, lowercase)

### "Row X: Invalid date format"
**Fix:** Dates must be YYYY-MM-DD format (e.g., 2025-03-15, not 03/15/2025)

### "Row X: Age must be between 17 and 42"
**Fix:** Check the age column for invalid values

### "Only CSV and Excel files are supported"
**Fix:** Save your file as .csv, .xlsx, or .xls

### "Network error. Is backend running?"
**Fix:** Backend must be running on the droplet. Check with:
```bash
/usr/bin/docker-compose ps
```

---

## 🚀 Next Steps

### 1. **Test the Upload Feature**
- Go to http://129.212.185.3
- Click "Bulk Data Upload" in menu
- Download a template
- Add a few rows of test data
- Upload and verify it works

### 2. **Prepare Your Real Data**
- Export existing data from your current system
- Format it to match the template columns
- Upload in batches if you have a lot

### 3. **View Your Uploaded Data**
- Events: Check "Event Performance" dashboard
- Projects: Check "Project Management" dashboard
- Leads: Check "Lead Status" dashboard

---

## 📦 Files Created

**Backend:**
- `backend/routers/data_import.py` - Upload API endpoints

**Frontend:**
- `taaip-dashboard/src/components/BulkDataUpload.tsx` - Upload UI component

**Dependencies Added:**
- `pandas` - CSV/Excel parsing
- `openpyxl` - Excel file support

---

## 🎯 Summary

✅ **Manual Entry:** Data Input Center (form-based, one at a time)  
✅ **Bulk Upload:** Bulk Data Upload (CSV/Excel, hundreds at once) ← NEW!  
✅ **Export:** Already existed (download CSV from backend)

**Your TAAIP platform now has complete data import/export capability!** 🎉

---

## 📞 How to Deploy to Droplet

Run these commands in your **droplet console**:

```bash
# Pull latest code
cd /opt/TAAIP
git pull origin feat/optimize-app

# Install new Python dependencies
pip install pandas openpyxl

# Rebuild containers
/usr/bin/docker-compose down
/usr/bin/docker-compose up -d --build
```

Then test at: http://129.212.185.3 → Bulk Data Upload

---

**Deployed files will be in:**
- `/opt/TAAIP/backend/routers/data_import.py`
- `/opt/TAAIP/taaip-dashboard/src/components/BulkDataUpload.tsx`
