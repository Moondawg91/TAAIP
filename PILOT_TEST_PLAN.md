# TAAIP Pilot Test Plan - New Unit Onboarding

## Phase 1: Initial Setup (Week 1)

### 1. Unit Information Gathering
- [ ] Battalion/Company designation
- [ ] Geographic responsibility (CBSAs, zip codes)
- [ ] Current FY mission numbers
- [ ] Key personnel (XO, 420T, MMA, S3, ESS, APA)
- [ ] Existing event calendar

### 2. Data Migration
- [ ] Import historical event data (last 2 quarters)
- [ ] Upload recruiter station data
- [ ] Configure zip code assignments
- [ ] Set up CBSA market data
- [ ] Import school access list

### 3. User Accounts & Training
- [ ] Create accounts for:
  - Battalion XO (admin access)
  - 420T (full access)
  - Company Commanders (company-level access)
  - Recruiters (read-only)
- [ ] Conduct 1-hour platform walkthrough
- [ ] Share quick reference guides

---

## Phase 2: Targeting Cycle Test (Weeks 2-4)

### Week 2: Q+0 Intelligence Phase
**Test Components:**
- [ ] Market Potential Dashboard - verify CBSA data loads
- [ ] Mission Analysis Dashboard - check FY goals display
- [ ] Analytics Dashboard - test filters and visualizations
- [ ] Upload past event performance data

**Success Metrics:**
- All dashboards load < 3 seconds
- Data filters work correctly
- Export functions generate clean reports

### Week 3: TWG Meeting Preparation
**Test Components:**
- [ ] Targeting Working Group dashboard
- [ ] Review sync matrix (Q-1 through Q+4)
- [ ] Company slide preparation tools
- [ ] D3A methodology walkthrough

**Tasks:**
- Schedule actual TWG meeting
- Have companies prepare Q+1 event nominations
- Test real-time agenda tracking
- Document any workflow issues

### Week 4: TDB Preparation & Execution
**Test Components:**
- [ ] Targeting Decision Board dashboard
- [ ] Event prioritization matrix
- [ ] Budget tracking (Marketing $ allocation)
- [ ] Asset recommendation engine

**Tasks:**
- Review company nominations from TWG
- XO approves/denies events in system
- Track decisions and rationale
- Generate TDB output report

---

## Phase 3: Execution & Assessment (Weeks 5-8)

### Calendar & Event Management
**Test Components:**
- [ ] Calendar Scheduler Dashboard
- [ ] Event Performance tracking
- [ ] Lead Status Report
- [ ] AAR Report submission (72-hour rule)

**Tasks:**
- Execute 2-3 approved events
- Track lead generation in real-time
- Submit AAR within 72 hours
- Assess data accuracy

### Fusion Team Coordination
**Test Components:**
- [ ] Fusion Team Dashboard
- [ ] Team Role Assignments (new separate tab)
- [ ] Task tracking across roles (XO, 420T, MMA, S3, ESS, APA)

**Tasks:**
- Assign tasks to team members
- Track completion rates
- Test communication flow
- Verify role-based access

---

## Phase 4: Full Cycle Assessment (Week 9-10)

### Metrics Collection
**Key Performance Indicators:**
- [ ] System uptime/reliability
- [ ] User adoption rate (% of staff using platform)
- [ ] Data accuracy (compare to manual tracking)
- [ ] Time saved vs. traditional methods
- [ ] Decision-making speed improvement

### User Feedback Sessions
**Schedule 30-min interviews with:**
- [ ] Battalion XO
- [ ] 420T Technician
- [ ] 2-3 Company Commanders
- [ ] 1-2 Station Commanders

**Questions:**
1. What features do you use most?
2. What's confusing or not working?
3. What features are missing?
4. How much time does this save you?
5. Would you recommend to other battalions?

### Bug Fixes & Adjustments
- [ ] Compile all issues/requests
- [ ] Prioritize by impact
- [ ] Deploy fixes
- [ ] Re-test problem areas

---

## Phase 5: Scale & Rollout Decision (Week 11-12)

### Success Criteria for Full Deployment
**Must Meet 4 of 5:**
- [ ] 80%+ user adoption rate
- [ ] Saves 5+ hours/week per staff member
- [ ] Zero critical bugs/data errors
- [ ] Positive feedback from battalion leadership
- [ ] Successfully completed 1 full targeting cycle (TWG → TDB → Execution → AAR)

### Rollout Plan (if successful)
1. **Document lessons learned**
2. **Create standardized training materials**
3. **Identify 2-3 additional pilot battalions**
4. **Establish support structure** (help desk, bug reporting)
5. **Plan quarterly enhancement cycles**

---

## Technical Requirements for Pilot

### Infrastructure
- [ ] Droplet verified at http://129.212.185.3 ✅
- [ ] SSL certificate configured (HTTPS)
- [ ] Domain name (optional): taaip.usarec.army.mil or similar
- [ ] Database backups configured (daily)
- [ ] User authentication/SSO integration

### Data Sources
- [ ] API connection to USAREC data systems
- [ ] Historical event data (CSV imports)
- [ ] School database integration
- [ ] Zip code market data
- [ ] Budget/funding tracker

### Support
- [ ] Designated TAAIP admin (420T or XO)
- [ ] Technical support contact (you/developer)
- [ ] Bug reporting process (email, ticket system)
- [ ] Weekly check-in calls (first 4 weeks)

---

## Quick Start Checklist for First Day

**Pilot Unit Commander (XO):**
1. Log in at http://129.212.185.3 or http://localhost:5174/ (local)
2. Navigate to **Home → Resources → Quick Reference**
3. Review **Targeting Working Group (TWG)** dashboard
4. Check **Fusion Team** → assign roles to your staff
5. Upload 1 past event to **Event Performance Dashboard**
6. Review **Market Potential** for your CBSAs
7. Schedule first TWG meeting in **Calendar**

**420T Technician:**
1. Verify all zip code assignments in **Analytics Dashboard**
2. Check **Mission Analysis** goals for current FY/quarter
3. Upload recruiter station data
4. Test **Lead Status Report** with sample data
5. Prepare sync matrix for next TWG

**Company Commanders:**
1. Review your CBSA assignments
2. Check upcoming events in **Calendar**
3. Prepare Q+1 event nominations
4. Review **Asset Recommendation Engine** for your market

---

## Contact & Support

**Technical Issues:**
- Email: support@taaip.army.mil (set up)
- Report bugs in system or via GitHub issues

**Training & Guidance:**
- Weekly office hours: TBD
- Documentation: http://129.212.185.3/docs
- Video tutorials: Coming soon

**Pilot Test Coordinator:**
- Name: [Your Name/Role]
- Email: [Contact Email]
- Phone: [Contact Number]

---

## Success! 🎉

If pilot completes successfully, TAAIP will:
- Save 15-20 hours/week of manual tracking
- Improve targeting decision accuracy
- Enable real-time market intelligence
- Standardize D3A methodology across USAREC
- Scale to all battalions within 12 months
