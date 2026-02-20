import React from 'react'
import { Box, Typography, Chip, Grid, Paper, Button, TextField, MenuItem, Select, FormControl, InputLabel, Pagination } from '@mui/material'
import api from '../../api/client'
import EmptyState from '../../components/common/EmptyState'
import { Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'

export default function BudgetTrackerPage(){
  const [data, setData] = React.useState(null)
  const [loading, setLoading] = React.useState(true)
  const [filters, setFilters] = React.useState({})
  const [projSort, setProjSort] = React.useState<'planned'|'actual'|'variance'>('planned')
  const [projSortDir, setProjSortDir] = React.useState<'asc'|'desc'>('desc')
  const [projPage, setProjPage] = React.useState(1)
  const [projPageSize, setProjPageSize] = React.useState(10)
  const [evtSort, setEvtSort] = React.useState<'planned'|'actual'|'variance'>('planned')
  const [evtSortDir, setEvtSortDir] = React.useState<'asc'|'desc'>('desc')
  const [evtPage, setEvtPage] = React.useState(1)
  const [evtPageSize, setEvtPageSize] = React.useState(10)

  React.useEffect(()=>{
    let mounted = true
    setLoading(true)
    api.getBudgetDashboard(filters).then(d=>{ if(!mounted) return; setData(d) }).catch(()=>{ if(mounted) setData(null) }).finally(()=> mounted && setLoading(false))
    return ()=>{ mounted = false }
  }, [JSON.stringify(filters)])

  const refresh = async () => {
    setLoading(true)
    try{
      const d = await api.getBudgetDashboard(filters)
      setData(d)
    }catch(e){
      setData(null)
    }finally{ setLoading(false) }
  }

  // normalize payload shape: some callers return { data: { ... } } while API returns top-level
  const payload = data && data.data ? data.data : data
  const kpis = payload ? {
    allocated: payload.totals && payload.totals.allocated ? payload.totals.allocated : (payload.allocated || 0),
    planned: payload.totals && payload.totals.planned ? payload.totals.planned : (payload.total_planned || 0),
    actual: payload.totals && payload.totals.actual ? payload.totals.actual : (payload.total_spent || 0),
    remaining: payload.totals && payload.totals.remaining ? payload.totals.remaining : (payload.total_remaining || 0)
  } : { allocated:0, planned:0, actual:0, remaining:0 }

  // support dual-mode view via query param `view` (executive/comptroller)
  const params = new URLSearchParams(window.location.search)
  const view = params.get('view') || 'executive'

  return (
    <Box sx={{ color: '#EAEAF2' }}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <DualModeTabs />
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={data && data.data && data.data.breakdown_by_project ? data.data.breakdown_by_project : []} filename="budget_tracker" />
        </Box>
      </Box>
      <DashboardFilterBar />
      <DashboardToolbar title="Budget Tracker" subtitle="Budget rollups & breakdowns" filters={filters} onFiltersChange={(f)=>setFilters(f)} onExport={async (t:string)=>{
        try{
          if(t==='csv' || t==='json'){
            const qs = new URLSearchParams()
            Object.entries(filters || {}).forEach(([k,v])=>{ if(v!==undefined && v!=='') qs.set(k, String(v)) })
            const ext = t==='csv' ? 'csv' : 'json'
            const url = `/api/budget/dashboard/export.${ext}${qs.toString() ? ('?'+qs.toString()) : ''}`
            const res = await fetch(url)
            if(!res.ok) throw new Error('export failed')
            const blob = await res.blob()
            const dlUrl = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = dlUrl
            a.download = `budget_dashboard.${ext}`
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(dlUrl)
          }else{
            alert(`Export ${t} coming soon`)
          }
        }catch(e){ console.error('export error', e); alert('Export failed') }
      }} />
      {view === 'comptroller' ? (
        <Box sx={{ mt:2 }}>
          <Typography variant="h6">Comptroller Ledger</Typography>
          <ComptrollerPanel filters={filters} />
        </Box>
      ) : (
        <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p:2, bgcolor: '#12121A' }} elevation={0}>
            <Typography variant="caption">Allocated</Typography>
            <Typography variant="h6">${kpis.allocated.toFixed(2)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p:2, bgcolor: '#12121A' }} elevation={0}>
            <Typography variant="caption">Planned</Typography>
            <Typography variant="h6">${kpis.planned.toFixed(2)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p:2, bgcolor: '#12121A' }} elevation={0}>
            <Typography variant="caption">Actual</Typography>
            <Typography variant="h6">${kpis.actual.toFixed(2)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p:2, bgcolor: '#12121A' }} elevation={0}>
            <Typography variant="caption">Remaining</Typography>
            <Typography variant="h6">${kpis.remaining.toFixed(2)}</Typography>
          </Paper>
        </Grid>

        

        <Grid item xs={12}>
          <Typography variant="subtitle1" sx={{ mt:2 }}>Breakdowns</Typography>
          {loading ? <Typography>Loading...</Typography> : (
            data ? (
              <Box>
                {payload && payload.missing_data && payload.missing_data.length>0 && (
                  <Box sx={{ mt:1 }}>
                    {payload.missing_data.map((m,i)=> <Chip key={i} label={m} sx={{ mr:1, bgcolor: '#2A2A3A', color: '#FFB703' }} />)}
                  </Box>
                )}
                <Typography sx={{ mt:1 }}>By Category</Typography>
                <Box>
                  {payload && payload.breakdown_by_category && payload.breakdown_by_category.length ? payload.breakdown_by_category.map((c:any,i:any)=> (
                      <Box key={i} sx={{ display:'flex', justifyContent:'space-between', p:1, bgcolor: '#0B0B10' }}>
                          <Typography>{c.category || c.key || 'category'}</Typography>
                          <Typography>${(c.allocated||c.value||0).toFixed(0)}</Typography>
                      </Box>
                    )) : <Typography>No category data</Typography>}
                </Box>
                <Typography sx={{ mt:2 }}>By Project</Typography>
                <Box sx={{ display:'flex', gap:1, alignItems:'center', mb:1 }}>
                  <FormControl size="small">
                    <InputLabel>Sort</InputLabel>
                    <Select value={projSort} label="Sort" onChange={(e:any)=>{ setProjSort(e.target.value); setProjPage(1) }}>
                      <MenuItem value="planned">Planned</MenuItem>
                      <MenuItem value="actual">Actual</MenuItem>
                      <MenuItem value="variance">Variance</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small">
                    <InputLabel>Dir</InputLabel>
                    <Select value={projSortDir} label="Dir" onChange={(e:any)=>{ setProjSortDir(e.target.value); setProjPage(1) }}>
                      <MenuItem value="desc">Desc</MenuItem>
                      <MenuItem value="asc">Asc</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small">
                    <InputLabel>Page Size</InputLabel>
                    <Select value={projPageSize} label="Page Size" onChange={(e:any)=>{ setProjPageSize(Number(e.target.value)); setProjPage(1) }}>
                      <MenuItem value={5}>5</MenuItem>
                      <MenuItem value={10}>10</MenuItem>
                      <MenuItem value={25}>25</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                <Table size="small" sx={{ bgcolor: '#0B0B10', mt:1 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Project</TableCell>
                      <TableCell>Planned</TableCell>
                      <TableCell>Actual</TableCell>
                      <TableCell>Variance</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(() => {
                      const rows = (payload && payload.breakdown_by_project ? payload.breakdown_by_project : []).slice();
                      rows.sort((a:any,b:any)=>{
                        const key = projSort
                        const va = Number(a[key]||0); const vb = Number(b[key]||0)
                        return projSortDir==='asc' ? va-vb : vb-va
                      })
                      const start = (projPage-1)*projPageSize; const paged = rows.slice(start, start+projPageSize)
                      return paged.length ? paged.map((p:any,i:number)=> (
                        <TableRow key={String(p.project_id||p.key||i)}><TableCell>{p.name || p.project_id || p.key}</TableCell><TableCell>{p.planned || ''}</TableCell><TableCell>{p.value || p.actual || 0}</TableCell><TableCell>{p.variance || ''}</TableCell></TableRow>
                      )) : <TableRow><TableCell colSpan={4}>No project data</TableCell></TableRow>
                    })()}
                  </TableBody>
                </Table>
                <Box sx={{ display:'flex', justifyContent:'center', mt:1 }}>
                  <Pagination size="small" count={Math.max(1, Math.ceil(((data.breakdown_by_project||[]).length || 0)/projPageSize))} page={projPage} onChange={(_,v)=>setProjPage(v)} />
                </Box>

                <Typography sx={{ mt:2 }}>By Event</Typography>
                <Box sx={{ display:'flex', gap:1, alignItems:'center', mb:1 }}>
                  <FormControl size="small">
                    <InputLabel>Sort</InputLabel>
                    <Select value={evtSort} label="Sort" onChange={(e:any)=>{ setEvtSort(e.target.value); setEvtPage(1) }}>
                      <MenuItem value="planned">Planned</MenuItem>
                      <MenuItem value="actual">Actual</MenuItem>
                      <MenuItem value="variance">Variance</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small">
                    <InputLabel>Dir</InputLabel>
                    <Select value={evtSortDir} label="Dir" onChange={(e:any)=>{ setEvtSortDir(e.target.value); setEvtPage(1) }}>
                      <MenuItem value="desc">Desc</MenuItem>
                      <MenuItem value="asc">Asc</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small">
                    <InputLabel>Page Size</InputLabel>
                    <Select value={evtPageSize} label="Page Size" onChange={(e:any)=>{ setEvtPageSize(Number(e.target.value)); setEvtPage(1) }}>
                      <MenuItem value={5}>5</MenuItem>
                      <MenuItem value={10}>10</MenuItem>
                      <MenuItem value={25}>25</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                <Table size="small" sx={{ bgcolor: '#0B0B10', mt:1 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Event</TableCell>
                      <TableCell>Planned</TableCell>
                      <TableCell>Actual</TableCell>
                      <TableCell>Variance</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(() => {
                      const rows = (payload && payload.breakdown_by_event ? payload.breakdown_by_event : []).slice();
                      rows.sort((a:any,b:any)=>{
                        const key = evtSort
                        const va = Number(a[key]||0); const vb = Number(b[key]||0)
                        return evtSortDir==='asc' ? va-vb : vb-va
                      })
                      const start = (evtPage-1)*evtPageSize; const paged = rows.slice(start, start+evtPageSize)
                      return paged.length ? paged.map((e:any,i:number)=> (
                        <TableRow key={String(e.event_id||e.key||i)}><TableCell>{e.name || e.event_id || e.key}</TableCell><TableCell>{e.planned || ''}</TableCell><TableCell>{e.value || e.actual || 0}</TableCell><TableCell>{e.variance || ''}</TableCell></TableRow>
                      )) : <TableRow><TableCell colSpan={4}>No event data</TableCell></TableRow>
                    })()}
                  </TableBody>
                </Table>
                <Box sx={{ display:'flex', justifyContent:'center', mt:1 }}>
                  <Pagination size="small" count={Math.max(1, Math.ceil(((data.breakdown_by_event||[]).length || 0)/evtPageSize))} page={evtPage} onChange={(_,v)=>setEvtPage(v)} />
                </Box>
              </Box>
            ) : <React.Fragment>
              <Box sx={{ mt:2 }}>
                <EmptyState title="No data yet" subtitle="No budget data available for the selected filters." actionLabel="Go to Import Center" onAction={() => { window.location.href = '/import-center' }} />
              </Box>
            </React.Fragment>
          )}
        </Grid>
        </Grid>
      )}
    </Box>
  )
}


function ComptrollerPanel({filters}:{filters:any}){
  const [data, setData] = React.useState<any>(null)
  const [loading, setLoading] = React.useState(true)
  React.useEffect(()=>{
    let mounted = true
    setLoading(true)
    const qs = new URLSearchParams()
    Object.entries(filters||{}).forEach(([k,v])=>{ if(v!==undefined && v!=='') qs.set(k, String(v)) })
    fetch(`/api/budget/comptroller/ledger${qs.toString()?('?'+qs.toString()):''}`).then(r=>r.json()).then(d=>{ if(!mounted) return; setData(d) }).catch(()=>{ if(mounted) setData(null) }).finally(()=> mounted && setLoading(false))
    return ()=>{ mounted=false }
  }, [JSON.stringify(filters)])

  if(loading) return <Typography>Loading...</Typography>
  if(!data) return <Typography>No data</Typography>
  return (
    <Box>
      <Typography sx={{ mt:1 }}>Totals: Allocated ${data.totals.allocated} / Obligated ${data.totals.obligated} / Executed ${data.totals.executed} / Remaining ${data.totals.remaining}</Typography>
      <Box sx={{ mt:1 }}>
        <Table size="small" sx={{ bgcolor: '#0B0B10', mt:1 }}>
          <TableHead>
            <TableRow>
              <TableCell>Account</TableCell>
              <TableCell>Allocated</TableCell>
              <TableCell>Obligated</TableCell>
              <TableCell>Executed</TableCell>
              <TableCell>Remaining</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.rows && data.rows.length ? data.rows.map((r:any,i:number)=>(
              <TableRow key={i}><TableCell>{r.account}</TableCell><TableCell>{r.allocated}</TableCell><TableCell>{r.obligated}</TableCell><TableCell>{r.executed}</TableCell><TableCell>{r.remaining}</TableCell></TableRow>
            )) : <TableRow><TableCell colSpan={5}>No ledger rows</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Box>
    </Box>
  )
}
