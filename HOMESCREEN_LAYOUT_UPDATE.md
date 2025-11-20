# HomeScreen Layout Update - Deployment Guide

## Changes Summary

### 1. HomeScreen Layout Reorganization
**File**: `taaip-dashboard/src/components/HomeScreen.tsx`

**Changes**:
- Replaced horizontal dropdown buttons with vertical sidebar layout
- Created 3-column grid: 1 column sidebar + 3 columns leaderboard
- Added collapsible sidebar panels:
  - **Resources Panel**: Quick access to documentation, manuals, training videos
  - **Dashboards Panel**: Quick navigation to all mission dashboards
  - **Help Desk Panel**: Quick access to support request types
- Implemented mutual exclusion for sidebar dropdowns (only one open at a time)
- Added `handleToggleDropdown` function to manage dropdown states
- Maintained dashboard grid cards below leaderboard for quick access

**Key Features**:
- Sidebar panels are collapsible with chevron indicators
- Clicking one panel closes others automatically
- Compact sidebar design saves horizontal space for leaderboard
- All existing functionality preserved, just reorganized

### 2. Expandable Top 10 Leaderboard
**File**: `taaip-dashboard/src/components/CompanyStandingsLeaderboard.tsx`

**Changes**:
- Added `CompanyStandingsLeaderboardProps` interface:
  ```typescript
  interface CompanyStandingsLeaderboardProps {
    showExpanded?: boolean;
    setShowExpanded?: React.Dispatch<React.SetStateAction<boolean>>;
  }
  ```
- Modified component to accept `showExpanded` and `setShowExpanded` props
- Updated table body rendering to show top 10 by default:
  ```typescript
  {(showExpanded ? filteredStandings : filteredStandings.slice(0, 10)).map(...)}
  ```
- Added "Show More/Less" toggle button below table:
  - Button text: "Show Top 10" (when expanded) or "Show All (X companies)" (when collapsed)
  - Styled with Army theme colors (gray-800 background, yellow-500 text)
  - Only appears when there are more than 10 companies

**User Experience**:
- Leaderboard initially displays top 10 companies
- "Show All" button reveals remaining companies
- "Show Top 10" button collapses back to top performers
- Button includes total company count for transparency

### 3. App.tsx Dropdown Improvements
**File**: `taaip-dashboard/src/App.tsx` (from previous update)

**Features**:
- Dropdown closes when clicking outside (detects `.dropdown-menu` and `.dropdown-button` classes)
- Dropdown closes automatically when switching main navigation tabs
- Enhanced user experience with cleaner tab switching

## Technical Details

### State Management
```typescript
// HomeScreen state
const [showMissionMenu, setShowMissionMenu] = React.useState(false);
const [showResources, setShowResources] = React.useState(false);
const [showHelpDesk, setShowHelpDesk] = React.useState(false);
const [showExpanded, setShowExpanded] = React.useState(false);

// Mutual exclusion handler
const handleToggleDropdown = (dropdown: 'mission' | 'resources' | 'helpdesk') => {
  // Opens selected, closes others
}
```

### Layout Structure
```
HomeScreen
├── Hero Section (TAAIP header)
├── Main Content
│   ├── Grid Layout (1 + 3 columns)
│   │   ├── Sidebar (1 column)
│   │   │   ├── Resources Panel (collapsible)
│   │   │   ├── Dashboards Panel (collapsible)
│   │   │   └── Help Desk Panel (collapsible)
│   │   └── Leaderboard (3 columns)
│   │       ├── CompanyStandingsLeaderboard
│   │       └── Show More/Less Button
│   └── Dashboard Grid Cards (below, 4 columns)
└── Footer
```

### Responsive Design
- **Mobile/Tablet**: Sidebar stacks above leaderboard (1 column layout)
- **Desktop**: Sidebar + leaderboard side-by-side (1 + 3 column grid)
- Grid uses Tailwind's `lg:` breakpoint for responsive behavior

## Deployment Instructions

### On DigitalOcean Droplet (129.212.185.3)

1. **SSH into droplet**:
   ```bash
   ssh root@129.212.185.3
   ```

2. **Navigate to repository**:
   ```bash
   cd /opt/TAAIP
   ```

3. **Pull latest changes**:
   ```bash
   git fetch origin feat/optimize-app
   git checkout feat/optimize-app
   git pull origin feat/optimize-app
   ```

4. **Rebuild frontend container**:
   ```bash
   docker-compose build frontend
   ```

5. **Restart services**:
   ```bash
   docker-compose up -d
   ```

6. **Verify deployment**:
   ```bash
   docker-compose ps
   docker-compose logs -f frontend
   ```

### Alternative: Use Existing Deployment Script

If `deploy-enhanced-upload.sh` exists:
```bash
cd /opt/TAAIP
./deploy-enhanced-upload.sh
```

## Testing Checklist

After deployment, verify on http://129.212.185.3:

- [ ] Home page loads without errors
- [ ] Left sidebar displays Resources, Dashboards, Help Desk panels
- [ ] Clicking Resources panel opens dropdown with 5 links
- [ ] Clicking Dashboards panel opens dropdown with 8 dashboard shortcuts
- [ ] Clicking Help Desk panel opens dropdown with 5 support options
- [ ] Opening one panel closes others (mutual exclusion working)
- [ ] Leaderboard displays top 10 companies by default
- [ ] "Show All" button appears when >10 companies exist
- [ ] Clicking "Show All" expands to display all companies
- [ ] Clicking "Show Top 10" collapses back to top 10
- [ ] Dashboard grid cards appear below leaderboard (8 cards)
- [ ] Main menu dropdown closes when switching tabs
- [ ] Main menu dropdown closes when clicking outside
- [ ] Layout is responsive (sidebar stacks on mobile)
- [ ] Footer displays correctly at bottom

## Rollback Plan

If issues occur:

1. **Revert to previous commit**:
   ```bash
   cd /opt/TAAIP
   git log --oneline -5  # Find previous commit hash
   git checkout <previous-commit-hash>
   docker-compose build frontend
   docker-compose up -d
   ```

2. **Or checkout previous branch**:
   ```bash
   git checkout main
   docker-compose build frontend
   docker-compose up -d
   ```

## Known Issues / Notes

- **None currently** - All TypeScript compilation errors resolved
- **Browser Caching**: Users may need to hard refresh (Ctrl+F5 / Cmd+Shift+R) to see changes
- **Props Compatibility**: CompanyStandingsLeaderboard props are optional, so existing usages without props still work

## Files Modified

1. `taaip-dashboard/src/components/HomeScreen.tsx` - Layout reorganization, sidebar implementation
2. `taaip-dashboard/src/components/CompanyStandingsLeaderboard.tsx` - Expandable top 10 feature
3. `taaip-dashboard/src/App.tsx` - Dropdown close behavior (previous update)

## Git Commit

**Commit Hash**: `c71c478`
**Branch**: `feat/optimize-app`
**Commit Message**: "Fix HomeScreen layout with sidebar and add expandable top 10 leaderboard"

## Support

If deployment issues arise:
- Check Docker logs: `docker-compose logs -f frontend`
- Check backend logs: `docker-compose logs -f backend`
- Verify containers running: `docker-compose ps`
- Check disk space: `df -h`
- Check memory: `free -m`

---

**Deployment Date**: December 2024
**Deployed By**: TAAIP Development Team
**Environment**: DigitalOcean Production (129.212.185.3)
