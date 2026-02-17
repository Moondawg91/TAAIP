# TAAIP v2.0 - User Documentation
## Talent Acquisition Analytics & Intelligence Platform

---

## Table of Contents
1. [Overview](#overview)
2. [Access the System](#access-the-system)
3. [Navigation Guide](#navigation-guide)
4. [Access Tier System](#access-tier-system)
5. [Home Page Features](#home-page-features)
6. [Dashboard Sections](#dashboard-sections)
7. [Company Standings Leaderboard](#company-standings-leaderboard)
8. [Help Desk & Support](#help-desk--support)
9. [Troubleshooting](#troubleshooting)

---

## Overview

TAAIP v2.0 is a comprehensive analytics and intelligence platform designed for talent acquisition operations. The platform provides real-time insights, performance tracking, and decision support tools across 14 specialized dashboards.

### Key Features
- **Real-time Company Standings**: Live leaderboard tracking company performance
- **14 Specialized Dashboards**: Analytics, recruiting, G2Zone, forecasting, and more
- **Tier-Based Access Control**: 4 levels of user permissions
- **Dropdown Navigation**: Clean, organized interface
- **Resource Library**: Training materials, guides, and documentation
- **Integrated Help Desk**: Request support, features, and access upgrades

---

## Access the System

### URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Login
Use your DOD ID credentials to access the system. Your access level will be automatically assigned based on your role.

---

## Navigation Guide

### Top Navigation Bar
The main navigation is accessed via a dropdown menu in the top-right corner:

**Click the menu icon (≡)** to reveal:
- Home
- Analytics Dashboard
- Recruiting Operations
- G2 Zone Performance
- Lead Scoring
- Forecasting & Trends
- Project Management
- Budget & ROI
- Heat Maps
- Mission Funnel
- Campaign Manager
- Calendar & Scheduler
- DOD Branch Comparison
- Market Segments
- Data Input Forms

### Home Page Dropdowns
Three main dropdown buttons provide quick access:

1. **Mission Dashboards** - Access all 14 dashboard sections
2. **Resources** - Training materials, guides, templates
3. **Help Desk** - Submit support requests

---

## Access Tier System

TAAIP uses a 4-tier access control system:

### Tier 1 - View Only
**Typical Users**: Support Staff, Analysts, Interns

**Permissions**:
- ✅ View dashboards and reports
- ✅ View company standings
- ❌ No export capabilities
- ❌ No editing permissions

**Use Cases**:
- Review performance metrics
- Monitor company standings
- Access read-only reports

---

### Tier 2 - Standard User
**Typical Users**: Recruiters, Station Commanders, NCOs

**Permissions**:
- ✅ All Tier 1 permissions
- ✅ Export reports and data
- ✅ Create personal filters
- ✅ Save custom views
- ❌ No data editing

**Use Cases**:
- Generate custom reports
- Export data for presentations
- Track personal performance metrics
- Create saved filter sets

---

### Tier 3 - Editor
**Typical Users**: Company Commanders, Battalion Staff, Senior NCOs

**Permissions**:
- ✅ All Tier 2 permissions
- ✅ Edit data entries
- ✅ Create/modify projects
- ✅ Manage team tasks
- ✅ Input recruiting data

**Use Cases**:
- Update enlistment records
- Manage project timelines
- Edit team assignments
- Input survey data
- Modify campaign details

---

### Tier 4 - Administrator
**Typical Users**: Brigade/Battalion Commanders, G-Staff, System Admins

**Permissions**:
- ✅ All Tier 3 permissions
- ✅ Manage user accounts
- ✅ Configure dashboard settings
- ✅ Access admin panel
- ✅ Database management
- ✅ System configuration

**Use Cases**:
- Grant/revoke user access
- Configure system settings
- Manage organizational structure
- Oversee all operations
- Generate executive reports

---

## Home Page Features

### Company Standings Leaderboard
The centerpiece of the home page displays real-time company performance:

**Metrics Displayed**:
- **Rank**: Current position (with trend indicators)
- **Company Name**: Unit identification
- **Brigade**: Parent organization
- **YTD Mission**: Year-to-date goal
- **YTD Actual**: Year-to-date performance
- **Attainment %**: Performance percentage (color-coded)
- **Net Gain**: Total enlistments minus losses
- **Last Enlistment**: Most recent timestamp

**Visual Indicators**:
- 🥇 **Gold Medal**: Rank 1-3
- 🥈 **Silver Medal**: Rank 4-10
- 🥉 **Bronze Medal**: Rank 11-20
- ↑ **Green Arrow**: Rank improved
- ↓ **Red Arrow**: Rank decreased
- ➡ **Gray Arrow**: Rank stable

**Attainment Color Coding**:
- 🟢 **Green** (120%+): Exceeding mission
- 🟡 **Yellow** (100-119%): On track
- 🟠 **Orange** (80-99%): Below target
- 🔴 **Red** (<80%): Significantly below

**Features**:
- Auto-refreshes every 30 seconds
- Toggle between YTD and Monthly views
- Filter by brigade
- Click company name for detailed view

### Resources Dropdown
Quick access to training and reference materials:

- **420T Quick Start Guide**: New recruiter onboarding
- **Recruiting Operations Manual**: SOPs and best practices
- **Platform Training Videos**: TAAIP tutorials
- **Mission Analysis Guide**: M-IPOE framework
- **Access Control Policy**: User roles documentation
- **Data Entry Templates**: Excel/CSV templates
- **Leadership Guide**: Executive analytics
- **Army Recruiting Portal**: External resources

### Help Desk Dropdown
Submit support requests for:

- **Access Request**: Request tier upgrade
- **Feature Request**: Suggest new capabilities
- **Upgrade Request**: System improvements
- **Bug Report**: Technical issues
- **Training Request**: Schedule training sessions
- **Other Support**: General assistance

---

## Dashboard Sections

### 1. Analytics Dashboard
**Purpose**: High-level performance overview

**Key Metrics**:
- Enlistment trends
- Mission attainment rates
- Brigade comparisons
- Historical performance

**Access Level**: Tier 1+

---

### 2. Recruiting Operations
**Purpose**: Day-to-day recruiting management

**Features**:
- Lead pipeline tracking
- Appointment scheduling
- Contact management
- Activity logging

**Access Level**: Tier 2+

---

### 3. G2 Zone Performance
**Purpose**: Market intelligence and competitive analysis

**Features**:
- Zip code heat maps
- Demographic analysis
- Competition tracking
- Territory performance

**Access Level**: Tier 2+

---

### 4. Lead Scoring
**Purpose**: AI-powered lead prioritization

**Features**:
- ML-based lead scoring
- Conversion probability
- Recommended actions
- Contact history

**Access Level**: Tier 2+

---

### 5. Forecasting & Trends
**Purpose**: Predictive analytics

**Features**:
- Mission forecasting
- Trend analysis
- Seasonal patterns
- Predictive modeling

**Access Level**: Tier 3+

---

### 6. Project Management
**Purpose**: Track initiatives and campaigns

**Features**:
- Project timelines (PRID tracking)
- Budget monitoring
- Task management
- Milestone tracking

**Access Level**: Tier 3+

**Key Fields**:
- **PRID**: Project ID (FS ID, Lead ID, Prospect ID, Applicant ID)
- **Recruiter DODID**: Assigned recruiter
- **Burn Rate**: Budget utilization rate
- **Risk Level**: Project health indicator

---

### 7. Budget & ROI
**Purpose**: Financial tracking

**Features**:
- Budget allocation
- Expenditure tracking
- ROI calculations
- Cost per enlistment

**Access Level**: Tier 3+

---

### 8. Heat Maps
**Purpose**: Geographic visualization

**Features**:
- Interactive maps
- Territory boundaries
- Performance overlays
- Demographic layers

**Access Level**: Tier 2+

---

### 9. Mission Funnel
**Purpose**: Conversion tracking

**Features**:
- Lead → Applicant → Enlistee flow
- Drop-off analysis
- Stage conversion rates
- Funnel optimization

**Access Level**: Tier 2+

---

### 10. Campaign Manager
**Purpose**: Marketing campaign tracking

**Features**:
- Campaign creation
- Event management
- Performance tracking
- Budget allocation

**Access Level**: Tier 3+

---

### 11. Calendar & Scheduler
**Purpose**: Event and appointment management

**Features**:
- Event scheduling
- EMM integration
- Status reports
- Team calendars

**Access Level**: Tier 2+

---

### 12. DOD Branch Comparison
**Purpose**: Cross-service analysis

**Features**:
- Army vs Navy vs Air Force vs Marines
- Recruiting trends
- Market share analysis
- Competitive intelligence

**Access Level**: Tier 2+

---

### 13. Market Segments
**Purpose**: Demographic and psychographic analysis

**Features**:
- Audience segmentation
- Targeting strategies
- Persona development
- Market analysis

**Access Level**: Tier 2+

---

### 14. Data Input Forms
**Purpose**: Manual data entry

**Features**:
- Survey collection
- Lead entry
- Event logging
- Custom forms

**Access Level**: Tier 3+

---

## Company Standings Leaderboard

### Understanding the Metrics

**YTD Mission vs YTD Actual**:
- Mission = Assigned goal for the fiscal year
- Actual = Contracts/enlistments achieved
- Attainment % = (Actual / Mission) × 100

**Monthly Metrics**:
- Current month's mission and performance
- Helps track recent momentum
- Affects overall YTD standing

**Net Gain Calculation**:
```
Total Enlistments - Future Soldier Losses = Net Gain
```

**Example**:
- Total Enlistments: 90
- FS Losses: 8
- Net Gain: 82

### Rank Changes
- Rankings update in real-time
- Based on YTD attainment percentage
- Ties broken by net gain
- Previous rank shown for comparison

### Auto-Refresh Feature
The leaderboard automatically refreshes every 30 seconds to show:
- New enlistments
- Updated attainment percentages
- Rank changes
- Recent activity timestamps

---

## Help Desk & Support

### Requesting Access Upgrades

**Process**:
1. Click "Help Desk" dropdown
2. Select "Access Request"
3. Fill out form with:
   - Current tier level
   - Requested tier level
   - Justification
   - Supervisor approval (if required)
4. Submit request

**Review Time**: 1-3 business days

**Approval Authority**:
- Tier 1 → Tier 2: Company Commander
- Tier 2 → Tier 3: Battalion Commander
- Tier 3 → Tier 4: Brigade Commander/G-Staff

### Feature Requests
Submit ideas for new features:
- Describe the feature
- Explain the use case
- Estimate impact
- Priority level

### Bug Reports
Report technical issues:
- Describe the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)

### Training Requests
Schedule training sessions:
- Individual or group training
- Specific dashboard focus
- Basic or advanced level
- Preferred dates/times

---

## Troubleshooting

### Common Issues

**Q: Dashboard not loading**
- Check internet connection
- Clear browser cache
- Try different browser
- Verify backend is running (port 8000)

**Q: Can't export data**
- Verify you have Tier 2+ access
- Check browser popup blocker
- Try different file format

**Q: Access denied error**
- Confirm your access tier
- Request upgrade via Help Desk
- Contact system administrator

**Q: Leaderboard not updating**
- Wait for auto-refresh (30 seconds)
- Manual refresh: Click brigade filter toggle
- Check backend connection

**Q: Can't submit help desk request**
- Fill all required fields
- Check character limits
- Verify email format
- Try again in a few minutes

### Contact Support

**Technical Support**:
- Email: taaip-support@army.mil
- Phone: DSN 123-4567
- Hours: Mon-Fri, 0800-1700

**System Administrators**:
- COL Sarah Mitchell: sarah.mitchell@army.mil
- MAJ Robert Chen: robert.chen@army.mil

---

## Best Practices

### Daily Workflow
1. Check company standings for overnight changes
2. Review your assigned dashboards
3. Update recruiting activities
4. Export reports as needed
5. Respond to help desk tickets

### Weekly Tasks
1. Analyze trend reports
2. Update project statuses
3. Review team performance
4. Plan upcoming campaigns
5. Submit feature requests

### Monthly Reviews
1. Generate executive reports
2. Review budget vs expenditures
3. Analyze market segment performance
4. Update forecasting models
5. Conduct team training

---

## Security & Classification

**System Classification**: UNCLASSIFIED
**Data Handling**: FOR OFFICIAL USE ONLY (FOUO)

**Security Requirements**:
- Use strong passwords
- Log out when not in use
- Don't share credentials
- Report suspicious activity
- Follow DOD cybersecurity policies

---

## Version Information

**Current Version**: TAAIP v2.0
**Release Date**: November 2025
**Last Updated**: November 18, 2025

**Recent Updates**:
- Removed USAREC branding
- Implemented tier-based access system
- Redesigned home page with dropdown navigation
- Centered company standings leaderboard
- Standardized Army Vantage color theme
- Enhanced project management with PRID tracking
- Added comprehensive tooltips throughout

---

## Training Resources

### New User Training (2 hours)
- System overview
- Navigation basics
- Your access tier capabilities
- Basic reporting

### Advanced User Training (4 hours)
- Deep dive into all dashboards
- Custom report creation
- Data analysis techniques
- Admin functions (Tier 4 only)

### Refresher Training (1 hour)
- New features overview
- Tips and tricks
- Common issues resolution
- Q&A session

**To Schedule Training**: Submit a Training Request via the Help Desk dropdown

---

*For questions or feedback, contact the TAAIP support team.*
