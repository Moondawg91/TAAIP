import React, {useEffect, useState} from 'react'
import { Box, Button, Snackbar, Alert, Typography, Grid, Paper, Chip, Card, CardContent, Divider, Stack } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { getMe } from '../api/client'

export default function TargetingBoard() {
  const [summary, setSummary] = useState(null)
  const [pending, setPending] = useState(null)
  const [changes, setChanges] = useState(null)
  const [msg, setMsg] = useState({ open: false, severity: 'info', text: '' })
  const auth = useAuth()
  const [schoolTargets, setSchoolTargets] = useState([])

  function fetchAll(){
    fetch('/api/v2/targeting/dashboard/summary').then(r=>r.json()).then(setSummary).catch(()=>setSummary(null))
    fetch('/api/v2/targeting/dashboard/pending').then(r=>r.json()).then(setPending).catch(()=>setPending(null))
    fetch('/api/v2/targeting/dashboard/recent-changes').then(r=>r.json()).then(setChanges).catch(()=>setChanges(null))
    fetch('/api/v2/targeting/schools').then(r=>r.json()).then(js=>setSchoolTargets(js.schools || [])).catch(()=>setSchoolTargets([]))
  }

  function getStageColor(stage){
    if(!stage) return {bg:'#e0e0e0', color:'#000'}
    const s = String(stage).toLowerCase()
    if(s.includes('fusion')) return {bg:'#1976d2', color:'#fff'}
    if(s.includes('twg')) return {bg:'#9c27b0', color:'#fff'}
    if(s.includes('board')) return {bg:'#00695c', color:'#fff'}
    if(s.includes('execution')) return {bg:'#2e7d32', color:'#fff'}
    if(s.includes('assessment')) return {bg:'#ef6c00', color:'#fff'}
    return {bg:'#616161', color:'#fff'}
  }

  useEffect(() => { fetchAll() }, [])

  const [actorName, setActorName] = useState(null)
  const [actorType, setActorType] = useState('human')

  useEffect(()=>{
    let mounted = true
    // prefer explicit user display from /api/me
    getMe().then(me => {
      if (!mounted) return
      if (me && me.user && me.user.display_name) setActorName(me.user.display_name)
      else if (me && me.display_name) setActorName(me.display_name)
      else if (auth && auth.roles && auth.roles.length>0) setActorName(auth.roles[0])
      else setActorName('web_user')

      // derive actor type from roles: treat service/bot-like roles as non-human
      try{
        const roles = (auth && auth.roles) ? auth.roles : []
        const isAi = roles.some(r => /ai|bot|service|system|automation/i.test(String(r)))
        setActorType(isAi ? 'system' : 'human')
      }catch(e){ setActorType('human') }
    }).catch(()=>{
      if (!mounted) return
      setActorName((auth && auth.roles && auth.roles.length>0) ? auth.roles[0] : 'web_user')
      setActorType('human')
    })
    return ()=>{ mounted = false }
  }, [auth])

  async function doAdvance(targeting_cycle){
    const reason = window.prompt('Reason for advancing the cycle:', 'Advancing from UI')
    if (reason === null) return
    try{
      const res = await fetch('/api/v2/targeting/advance', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({targeting_cycle, actor: actorName, actor_type: actorType, reason})})
      const js = await res.json()
      if (js.status === 'ok') setMsg({open:true, severity:'success', text:'Advanced successfully'})
      else if (js.status === 'pending') setMsg({open:true, severity:'warning', text:'Advance pending approval'})
      else setMsg({open:true, severity:'error', text: 'Advance failed'})
    }catch(e){ setMsg({open:true, severity:'error', text: String(e)}) }
    fetchAll()
  }

  async function doApprove(targeting_cycle){
    // enforce human-only approval
    if (actorType !== 'human') { setMsg({open:true, severity:'error', text: 'Only human users may approve transitions'}); return }
    const confirmed = window.confirm('Approve the pending transition as a human?')
    if (!confirmed) return
    const reason = window.prompt('Optional approval note:', 'Approved via UI')
    try{
      const res = await fetch('/api/v2/targeting/approve', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({targeting_cycle, actor: actorName, reason})})
      const js = await res.json()
      if (js.status === 'ok') setMsg({open:true, severity:'success', text:'Approved'})
      else setMsg({open:true, severity:'error', text: js.result || 'Approve failed'})
    }catch(e){ setMsg({open:true, severity:'error', text: String(e)}) }
    fetchAll()
  }

  async function doReject(targeting_cycle, from_stage, to_stage, unit_rsid){
    const reason = window.prompt('Reason for sending back the cycle:', 'Rejecting via UI')
    if (reason === null) return
    const payload = { from_stage, to_stage, note: reason }
    try{
      const res = await fetch('/api/v2/targeting/actions', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ action_type: 'send_back', payload_json: payload, unit_rsid: unit_rsid || '', targeting_cycle, created_by: actorName })})
      const js = await res.json()
      if (js && js.status === 'ok') setMsg({open:true, severity:'success', text:'Send-back action created'})
      else setMsg({open:true, severity:'error', text: 'Send-back failed'})
    }catch(e){ setMsg({open:true, severity:'error', text: String(e)}) }
    fetchAll()
  }

  const current = (summary && summary.cycles && summary.cycles.length>0) ? summary.cycles[0] : null

  // derive simple counts
  const pendingCount = (pending && pending.pending_logs) ? pending.pending_logs.length : 0
  const recentCount = (changes && changes.rows) ? changes.rows.length : 0

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Targeting Board</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Command decision board — concise briefing and controls.</Typography>

      {/* Top row metrics */}
      <Grid container spacing={2} sx={{ mb:2 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">Current Phase</Typography>
              <Typography variant="h6">{current ? current.current_stage.toUpperCase() : 'N/A'}</Typography>
              <Chip label={current ? current.current_stage : 'none'} color="primary" size="small" sx={{ mt:1 }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">Unit / Cycle</Typography>
              <Typography variant="h6">{current ? `${current.unit_rsid || ''} • ${current.targeting_cycle || ''}` : '—'}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p:2 }}>
            <Typography variant="caption" color="text.secondary">Pending Approvals</Typography>
            <Typography variant="h6">{pendingCount}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p:2 }}>
            <Typography variant="caption" color="text.secondary">Recent Changes</Typography>
            <Typography variant="h6">{recentCount}</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {/* Main board */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Paper sx={{ p:2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
                    <Typography variant="h6">Commander Guidance</Typography>
                    <Chip label={current ? current.current_stage : 'none'} size="small" sx={{ ...(getStageColor(current && current.current_stage)), ml:1 }} />
                    <Box sx={{ ml:'auto' }}>
                      <Button variant="contained" color="primary" disabled={!current} onClick={() => current && doAdvance(current.targeting_cycle)} sx={{ mr:1 }}>Advance</Button>
                      <Button variant="outlined" color="success" disabled={!current || actorType !== 'human'} onClick={() => current && doApprove(current.targeting_cycle)} sx={{ mr:1 }}>Approve</Button>
                      <Button variant="outlined" color="error" disabled={!current} onClick={() => current && doReject(current.targeting_cycle, current && current.current_stage, current && current.current_stage, current && current.unit_rsid)}>Send Back</Button>
                    </Box>
                  </Box>
                </Stack>
                <Divider sx={{ my:1 }} />
                <Typography variant="body2" color="text.secondary">High-level instructions and mission-critical notes for the current cycle go here.</Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p:2 }}>
                <Typography variant="subtitle2">School Targeting</Typography>
                <Divider sx={{ my:1 }} />
                {schoolTargets && schoolTargets.length>0 ? (
                  <Box>
                    {['High Priority','Monitor','Low Priority'].map(cat => (
                      <Box key={cat} sx={{ mb:2 }}>
                        <Typography variant="subtitle2">{cat}</Typography>
                        <ul>
                          {schoolTargets.filter(s=>s.category===cat).slice(0,10).map(s => (
                            <li key={s.school_id}>
                              <strong>{s.school_name || s.school_id}</strong> — priority: {s.priority_score} • conf: {s.confidence_score}
                              {s.drivers && s.drivers.length>0 ? (<div style={{ fontSize:12, color:'#666' }}>Drivers: {s.drivers.map(d=>`${d.name} (${d.value})`).join(', ')}</div>) : null}
                              {s.limiting_factors && s.limiting_factors.length>0 ? (<div style={{ fontSize:12, color:'#a00' }}>Limiters: {s.limiting_factors.join('; ')}</div>) : null}
                              <div style={{ fontSize:11, color:'#888' }}>Last computed: {s.last_computed || '—'}</div>
                            </li>
                          ))}
                        </ul>
                      </Box>
                    ))}
                  </Box>
                ) : <Typography variant="caption" color="text.secondary">No school targeting results yet</Typography>}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p:2, minHeight:160 }}>
                <Typography variant="subtitle2">Fusion Cell Recommendations</Typography>
                <Divider sx={{ my:1 }} />
                {(summary && summary.latest && summary.latest.fusion && summary.latest.fusion.length>0) ? (
                  <ul>{summary.latest.fusion.map(f => <li key={f.id}>{f.id} — {f.created_at}</li>)}</ul>
                ) : <Typography variant="caption" color="text.secondary">No recommendations</Typography>}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p:2, minHeight:160 }}>
                <Typography variant="subtitle2">TWG Nominations</Typography>
                <Divider sx={{ my:1 }} />
                {(summary && summary.latest && summary.latest.twg && summary.latest.twg.length>0) ? (
                  <ul>{summary.latest.twg.map(t => <li key={t.id}>{t.id} — {t.approval_status}</li>)}</ul>
                ) : <Typography variant="caption" color="text.secondary">No nominations</Typography>}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p:2, minHeight:120 }}>
                <Typography variant="subtitle2">Decision Board</Typography>
                <Divider sx={{ my:1 }} />
                {(summary && summary.latest && summary.latest.board && summary.latest.board.length>0) ? (
                  <ul>{summary.latest.board.map(b => <li key={b.id}>{b.id} — {b.decision_status}</li>)}</ul>
                ) : <Typography variant="caption" color="text.secondary">No decisions</Typography>}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p:2, minHeight:120 }}>
                <Typography variant="subtitle2">Execution / Sync Actions</Typography>
                <Divider sx={{ my:1 }} />
                <Typography variant="caption" color="text.secondary">Scheduled actions and syncs will appear here.</Typography>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p:2 }}>
                <Typography variant="subtitle2">Assessment Feedback</Typography>
                <Divider sx={{ my:1 }} />
                <Typography variant="caption" color="text.secondary">Assessment outcomes and scores.</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Grid>

        {/* Side panel */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="subtitle2">Recent Changes</Typography>
            <Divider sx={{ my:1 }} />
            { changes && changes.rows && changes.rows.length>0 ? (
              <ul style={{ maxHeight:240, overflow:'auto' }}>{changes.rows.map(r => <li key={r.id}>{r.created_at}: {r.targeting_cycle} {r.from_stage}→{r.to_stage} by {r.actor}</li>)}</ul>
            ) : <Typography variant="caption" color="text.secondary">No recent changes</Typography> }
          </Paper>

          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="subtitle2">Pending Approvals</Typography>
            <Divider sx={{ my:1 }} />
            { pending && pending.pending_logs && pending.pending_logs.length>0 ? (
              <Stack spacing={1}>
                {pending.pending_logs.map(l => (
                  <Box key={l.id} sx={{ p:1, border: '1px solid rgba(0,0,0,0.06)', borderRadius:1 }}>
                    <Typography variant="body2"><strong>{l.targeting_cycle}</strong></Typography>
                    <Typography variant="caption">{l.from_stage} → {l.to_stage}</Typography>
                    <Box sx={{ mt:1 }}>
                      <Button size="small" variant="contained" color="success" onClick={() => doApprove(l.targeting_cycle)} sx={{ mr:1 }}>Approve</Button>
                      <Button size="small" variant="outlined" color="error" onClick={() => doReject(l.targeting_cycle, l.from_stage, l.to_stage, l.unit_rsid || '')}>Send Back</Button>
                    </Box>
                  </Box>
                ))}
              </Stack>
            ) : <Typography variant="caption" color="text.secondary">No pending approvals</Typography> }
          </Paper>

          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="subtitle2">Must Keep / Must Win</Typography>
            <Divider sx={{ my:1 }} />
            <Typography variant="caption" color="text.secondary">Placeholder for commander-priority items.</Typography>
          </Paper>

          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Risk Flags</Typography>
            <Divider sx={{ my:1 }} />
            <Typography variant="caption" color="text.secondary">Risk indicators (R/G/A) and quick notes.</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Snackbar open={msg.open} autoHideDuration={4000} onClose={() => setMsg(m=>({ ...m, open:false }))}>
        <Alert onClose={() => setMsg(m=>({ ...m, open:false }))} severity={msg.severity}>{msg.text}</Alert>
      </Snackbar>
    </Box>
  )
}
