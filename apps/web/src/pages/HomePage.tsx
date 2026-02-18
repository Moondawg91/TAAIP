import React from 'react'
import { Box, Typography, Grid, Chip, List, ListItem, ListItemText, Button, Stack, Divider, MenuItem, Select, FormControl } from '@mui/material'
import EmptyState from '../components/common/EmptyState'
import { Link as RouterLink } from 'react-router-dom'
import HomePanel from '../components/home/HomePanel'
import api from '../api/client'
import { useScope } from '../contexts/ScopeContext'
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
  const { scope } = useScope()
  const [news, setNews] = React.useState([])
  const [updates, setUpdates] = React.useState([])
  const [links, setLinks] = React.useState([])
  const [loading, setLoading] = React.useState(true)

  React.useEffect(()=>{
    let mounted = true
    setLoading(true)
    Promise.all([api.getHomeNews(), api.getHomeUpdates(), api.getHomeQuickLinks()]).then(([n,u,l])=>{
      if(!mounted) return
      setNews(n || [])
      setUpdates(u || [])
      setLinks(l || [])
    }).catch(()=>{
      // ignore errors; keep empty
    }).finally(()=> mounted && setLoading(false))
    return ()=>{ mounted = false }
  }, [scope])

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
                )) : <ListItem><EmptyState title="No news" subtitle="No news items for your scope." /></ListItem>)}
              </List>
            </HomePanel>
          </Grid>

          <Grid item xs={12} md={4}>
            <HomePanel title="System Status" icon={<ApiIcon sx={{ color: COLORS.primary }} />} actionLabel="View Imports" onActionClick={() => { /* navigation intentionally omitted */ }}>
              <Stack spacing={1}>
                <Box sx={{ display:'flex', justifyContent:'space-between' }}>
                  <Typography variant="body2">API</Typography>
                  <Typography variant="body2" sx={{ color: '#22C55E' }}>Online</Typography>
                </Box>
                <Box sx={{ display:'flex', justifyContent:'space-between' }}>
                  <Typography variant="body2">DB</Typography>
                  <Typography variant="body2" sx={{ color: COLORS.text }}>Connected</Typography>
                </Box>
                <Box sx={{ display:'flex', justifyContent:'space-between' }}>
                  <Typography variant="body2">Last Import</Typography>
                  <Typography variant="body2" sx={{ color: COLORS.muted }}>None</Typography>
                </Box>
                <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                  <Typography variant="body2">Alerts</Typography>
                  <Chip label={0} size="small" sx={{ bgcolor: '#2A2A3A', color: COLORS.accent }} />
                </Box>
              </Stack>
            </HomePanel>
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
            <HomePanel title="Your Scope Snapshot" icon={<StorageIcon sx={{ color: COLORS.primary }} />}>
              <Typography variant="body2" sx={{ color: COLORS.muted }}>Role</Typography>
              <Typography variant="body1" sx={{ color: COLORS.text, fontWeight:700, mb:1 }}>420T</Typography>
              <Typography variant="body2" sx={{ color: COLORS.muted }}>Scope</Typography>
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
              <Typography variant="caption" sx={{ color: COLORS.muted }}>© 2026 TAAIP — Talent Acquisition Intelligence & Analytics Platform</Typography>
            </HomePanel>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
