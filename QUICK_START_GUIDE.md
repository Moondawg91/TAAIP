# 🎯 TAAIP Market Intelligence Quick Start Guide

## Access the System

### 1. Open the Dashboard
Navigate to: **http://localhost:5173/**

### 2. Navigate to Market Intelligence Features
You'll see 8 tabs in the navigation bar. The three new tabs are:

#### 🌍 **Market Potential** (Globe Icon)
- View Army vs all DOD branches market share analysis
- Track contacted vs remaining potential by geography
- See competitive positioning across major metro areas

#### 🎯 **Mission Analysis** (Target Icon)
- Drill down through USAREC organizational hierarchy
- Track mission goals vs actual performance
- Monitor efficiency metrics (L2E rate, appointment show, test pass)

#### 🏆 **DOD Comparison** (Award Icon)
- Compare all 6 DOD branches side-by-side
- View Army's competitive ranking
- Identify strengths and improvement opportunities

---

## Using the Visualization Switcher

Each dashboard has 4-5 visualization modes accessible via buttons in the top-right:

### 📇 **Cards View** (Default)
- Grid layout with color-coded cards
- Best for quick overview and comparison
- Interactive hover effects
- Click brigade/battalion cards to drill down (Mission Analysis)

### 📊 **Bar Chart**
- Side-by-side comparisons
- Great for comparing metrics across units/branches
- Hover for detailed tooltips

### 🥧 **Pie Chart** (Market Potential only)
- Market share distribution visualization
- Shows proportional representation
- Color-coded by branch

### 🕸️ **Radar Chart** (DOD Comparison only)
- Multi-metric comparison
- Shows relative performance across dimensions
- Overlays multiple branches

### 📋 **Table View**
- Detailed data with all metrics
- Sortable columns (click headers)
- Best for data export and detailed analysis
- Army row highlighted in green

---

## Using Geographic Filters

### Filter Options:

#### **Geographic Level** (Dropdown 1)
- **CBSA** (Metro Areas) - Major markets like San Francisco, Dallas, NYC
- **ZIP Code** - Granular neighborhood-level analysis
- **RSID** - Recruiting station territories
- **State** - State-level aggregation (DOD Comparison)
- **National** - National totals (DOD Comparison)

#### **Fiscal Year** (Dropdown 2)
- FY2024
- FY2025
- FY2026

#### **Quarter** (Dropdown 3)
- Q1 (Oct-Dec)
- Q2 (Jan-Mar)
- Q3 (Apr-Jun)
- Q4 (Jul-Sep)

**Pro Tip**: Change any filter and the dashboard automatically refreshes with new data!

---

## Understanding the Metrics

### Market Potential Dashboard

**Army Market Share**: Percentage of total DOD contacts that belong to Army
- 🏆 **>35%** = Leading (Green)
- 📈 **25-35%** = Strong (Yellow)
- ⚠️ **<25%** = Opportunity (Red)

**Contacted**: Number of qualified individuals Army has engaged
**Remaining Potential**: Qualified individuals not yet contacted by Army
**Penetration Rate**: Contacted ÷ (Contacted + Remaining) × 100

### Mission Analysis Dashboard

**Goal Attainment**: Actual contracts ÷ Mission goal × 100
- ✅ **≥100%** = Exceeding Goal (Green)
- 📊 **90-99%** = On Track (Yellow)
- ⚠️ **<90%** = Below Goal (Red)

**Variance**: Actual contracts - Mission goal
- Positive = Exceeding
- Negative = Shortfall

**L2E Rate**: Lead-to-Enlistment Rate (efficiency metric)
**Appointment Show Rate**: Percentage of scheduled appointments conducted
**Test Pass Rate**: Percentage of test-takers who pass ASVAB

### DOD Comparison Dashboard

**Contracts Per Recruiter**: Productivity metric (higher is better)
**Lead→Contract Rate**: Conversion efficiency
**Contract→Ship Rate**: Retention metric
**Efficiency Score**: Overall performance composite (0-100%)

**Army Competitive Position**: Shows where Army ranks #1-6 across all metrics

---

## Navigation Tips

### Market Potential Dashboard
1. Start with **Cards View** to see all 6 branches at a glance
2. Switch to **Pie Chart** to visualize market share distribution
3. Use **Table View** for detailed numbers and sorting
4. Change geographic level to CBSA → see metro area breakdowns
5. Compare different quarters to see seasonal trends

### Mission Analysis Dashboard
1. Start at **Brigade Level** to see top-level performance
2. **Click a brigade card** to drill down into battalions
3. **Click a battalion card** to see company-level detail
4. Use breadcrumb navigation ("← Back to Brigades") to go back up
5. Switch to **Bar Chart** to compare multiple units side-by-side
6. Switch to **Table View** to see all metrics in sortable columns

### DOD Comparison Dashboard
1. Start with **Cards View** to see all branches ranked
2. Check **"Army Competitive Position"** summary at top
3. Review **"Where Army Leads"** (green box) for strengths
4. Review **"Improvement Opportunities"** (red box) for areas to focus
5. Switch to **Radar Chart** for multi-metric visualization
6. Use geographic filters to compare by market
7. Switch to **Table View** to see detailed rankings

---

## Example Workflows

### Workflow 1: Identify Top Markets for Army
1. Go to **Market Potential** tab
2. Select **CBSA** geographic level
3. Select **FY2025** and **Q4**
4. Click **Table View** button
5. Click "Market Share" column header to sort
6. **Result**: Washington DC (39.27%), San Francisco (38.06%), Dallas (34.15%)

### Workflow 2: Analyze Brigade Performance
1. Go to **Mission Analysis** tab
2. Ensure **Brigade** level is selected
3. Select **FY2025 Q4**
4. Review goal attainment percentages
5. **Click 1BDE card** to drill into battalions
6. Compare battalion performance within brigade
7. Identify high and low performers

### Workflow 3: Compare Army to Navy in San Francisco
1. Go to **DOD Comparison** tab
2. Select **CBSA** geographic level
3. Keep default **San Francisco** (41860)
4. Select **FY2025 Q4**
5. Switch to **Table View**
6. Compare Army vs Navy rows:
   - Navy: 601 contracts, 15.0 per recruiter
   - Army: 585 contracts, 9.3 per recruiter
7. **Insight**: Navy has higher productivity per recruiter in this market

### Workflow 4: Track Market Potential Trends
1. Go to **Market Potential** tab
2. Select **Dallas** from CBSA dropdown
3. Select **Q1** → Note Army market share
4. Change to **Q2** → Compare
5. Change to **Q3** → Compare
6. Change to **Q4** → Compare
7. **Result**: Identify if market share is growing or declining quarter-over-quarter

---

## Key Performance Indicators (KPIs) to Monitor

### Strategic KPIs (Executive Dashboard)
1. **Army Market Share** (Target: >30%)
2. **Total DOD Contacted** (Growth indicator)
3. **Remaining Potential** (Opportunity size)
4. **Army Competitive Rank** (Position vs other branches)

### Operational KPIs (Mission Analysis)
1. **Goal Attainment %** (Target: ≥100%)
2. **Variance** (Positive = good, Negative = gap)
3. **L2E Rate** (Target: >5%)
4. **Appointment Show Rate** (Target: >70%)
5. **Test Pass Rate** (Target: >80%)

### Tactical KPIs (Branch Comparison)
1. **Contracts Per Recruiter** (Productivity)
2. **Lead→Contract Rate** (Conversion efficiency)
3. **Contract→Ship Rate** (Retention)
4. **Efficiency Score** (Overall performance)

---

## Troubleshooting

### Dashboard shows "Loading..."
- Wait 2-3 seconds for API response
- Check that backend is running: http://localhost:8000/docs
- Refresh browser (Cmd+R / Ctrl+R)

### No data appears
- Verify filters are set to FY2025 Q4 (most data is here)
- Try different CBSA (San Francisco 41860 is always populated)
- Check browser console (F12) for error messages

### Charts look empty
- Switch to Table View to see if data exists
- Some quarters may have sparse data
- Try different fiscal year or quarter

### Drill-down not working (Mission Analysis)
- Ensure you're in Cards View (drill-down only works there)
- Click directly on card body, not buttons
- Use breadcrumb navigation to go back up levels

---

## Data Refresh

### How often does data update?
- Real-time: Data updates immediately when you change filters
- Database: Sample data is static (for demonstration)
- Production: Would connect to live USAREC systems

### Can I export data?
- **Current**: Copy from Table View, paste into Excel
- **Future Enhancement**: PDF reports, CSV exports, Excel workbooks

---

## Support & Feedback

### System Status
- ✅ Frontend: http://localhost:5173/
- ✅ Backend: http://localhost:8000/
- ✅ API Docs: http://localhost:8000/docs

### Test Endpoints Manually
Run the test script:
```bash
cd /Users/ambermooney/Desktop/TAAIP
./test_all_endpoints.sh
```

### View Detailed Documentation
```bash
cat /Users/ambermooney/Desktop/TAAIP/MARKET_INTELLIGENCE_SYSTEM_SUMMARY.md
```

---

## Quick Reference

### Top 3 Markets by Army Share (FY2025 Q4)
1. 🏆 Washington DC: **39.27%**
2. 🥈 San Francisco: **38.06%**
3. 🥉 Dallas: **34.15%**

### Brigade Performance (FY2025 Q4)
- **1BDE**: 101.1% goal attainment (+27 over goal)
- **2BDE**: 101.2% goal attainment (+33 over goal)

### DOD Branch Rankings (San Francisco)
1. Navy: 601 contracts
2. **Army**: 585 contracts
3. Marines: 480 contracts
4. Air Force: 408 contracts
5. Space Force: 88 contracts
6. Coast Guard: 86 contracts

---

**Last Updated**: November 17, 2025
**Version**: 1.0
**Status**: ✅ Fully Operational
