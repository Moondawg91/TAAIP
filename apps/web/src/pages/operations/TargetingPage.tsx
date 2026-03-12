import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import { apiFetch } from '../../api/client'

export default function TargetingPage(){
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState<any>(null)
  const [targets, setTargets] = useState<any[]>([])
  const [error, setError] = useState<string|null>(null)
  const [guidance, setGuidance] = useState<any>({})

  useEffect(()=>{
    let mounted = true
    setLoading(true)
    Promise.all([
      apiFetch('/api/ops/targeting/summary').catch(e=>({status:'error', message: e?.message || String(e)})),
      apiFetch('/api/ops/targeting/targets').catch(e=>({status:'error', message: e?.message || String(e)})),
      // fetch guidance for the active unit; fall back to 6L sample if empty
      apiFetch('/api/v2/targeting/guidance').catch(e=>({status:'error', message: e?.message || String(e)}))
    ]).then(([s, t, g])=>{
      if(!mounted) return
      if(s && s.status === 'error') setError(s.message || 'summary fetch failed')
      else setSummary(s)
      if(t && t.status === 'error') setError(prev=>prev || (t.message || 'targets fetch failed'))
      else setTargets((t && Array.isArray(t.rows)) ? t.rows : (t && Array.isArray(t) ? t : []))
      try{
        if(g && g.status !== 'error' && Array.isArray(g.rows)){
          const map:any = {}
          g.rows.forEach((r:any)=>{ map[r.section] = r.payload })
          setGuidance(map)
        }
      }catch(e){ }
    }).catch(e=>{
      if(mounted) setError(e?.message || String(e))
    }).finally(()=>{ if(mounted) setLoading(false) })

    return ()=>{ mounted = false }
  }, [])

  const k = summary?.kpis || {}
  const kpis = {
    targets_identified: k.targets_total ?? k.targets_identified ?? 0,
    priority1: k.priority1 ?? k.priority_1 ?? 0,
    priority2: k.priority2 ?? k.priority_2 ?? 0,
    priority3: k.priority3 ?? k.priority_3 ?? 0,
  }

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:2 }}>Targeting</Typography>
      {loading && <div>Loading...</div>}
      {error && <div style={{color:'red'}}>Error: {error}</div>}

      {!loading && (
        <>
          <Grid container spacing={2} sx={{ mb:2 }}>
            <Grid item xs={12} sm={6} md={3}><Paper sx={{ p:2 }}><Typography variant="subtitle2">Targets Identified</Typography><Typography variant="h5">{kpis.targets_identified}</Typography></Paper></Grid>
            <Grid item xs={12} sm={6} md={3}><Paper sx={{ p:2 }}><Typography variant="subtitle2">Priority 1</Typography><Typography variant="h5">{kpis.priority1}</Typography></Paper></Grid>
            <Grid item xs={12} sm={6} md={3}><Paper sx={{ p:2 }}><Typography variant="subtitle2">Priority 2</Typography><Typography variant="h5">{kpis.priority2}</Typography></Paper></Grid>
            <Grid item xs={12} sm={6} md={3}><Paper sx={{ p:2 }}><Typography variant="subtitle2">Priority 3</Typography><Typography variant="h5">{kpis.priority3}</Typography></Paper></Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mb:2, mt:2 }}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p:2 }}>
                <Typography variant="h6">Commander Guidance</Typography>
                <Typography variant="body2" sx={{ mt:1, whiteSpace:'pre-wrap' }}>{(guidance.commander_guidance && guidance.commander_guidance.command_emphasis) || 'No commander guidance yet'}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p:2 }}>
                <Typography variant="h6">Must Keep</Typography>
                <Typography variant="body2" sx={{ mt:1, whiteSpace:'pre-wrap' }}>{(guidance.must_keep && JSON.stringify(guidance.must_keep, null, 2)) || 'No Must Keep items yet'}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p:2 }}>
                <Typography variant="h6">Must Win</Typography>
                <Typography variant="body2" sx={{ mt:1, whiteSpace:'pre-wrap' }}>{(guidance.must_win && JSON.stringify(guidance.must_win, null, 2)) || 'No Must Win items yet'}</Typography>
              </Paper>
            </Grid>
          </Grid>

          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Target</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Opportunity</TableCell>
                  <TableCell>Performance</TableCell>
                  <TableCell>Gap</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Recommended Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(!targets || targets.length === 0) ? (
                  <TableRow>
                    <TableCell colSpan={7} sx={{ py:4 }}>
                      <Typography variant="h6">No targeting data yet</Typography>
                      <Typography variant="body2" sx={{ color:'text.secondary' }}>The Targeting Engine will populate priority targets when available.</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  targets.map((r:any, idx:number)=>{
                    return (
                      <TableRow key={r.target_id || r.target_name || idx}>
                        <TableCell>{r.target_name || r.target_id || ''}</TableCell>
                        <TableCell>{r.target_type || ''}</TableCell>
                        <TableCell>{r.opportunity_score ?? r.opportunity ?? ''}</TableCell>
                        <TableCell>{r.performance_score ?? ''}</TableCell>
                        <TableCell>{r.gap_score ?? ''}</TableCell>
                        <TableCell>{r.priority_band || r.priority || ''}</TableCell>
                        <TableCell>{r.recommended_action || ''}</TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </Paper>
        </>
      )}
    </Box>
  )
}
