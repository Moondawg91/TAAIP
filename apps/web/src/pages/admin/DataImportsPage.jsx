import React, { useEffect, useState } from 'react'
import { getMe } from '../../api/client'
import { isMaster } from '../../auth/effectiveAccess'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../../api/client'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'

export default function DataImportsPage(){
  const navigate = useNavigate()
  const [uploads, setUploads] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [total, setTotal] = useState(0)
  const [datasetFilter, setDatasetFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [validatedFilter, setValidatedFilter] = useState('')

  async function load(){
    // guard: only allow admins to access this page
    try{
      const me = await getMe()
      const admin = isMaster(me) || (me && Array.isArray(me.roles) && me.roles.map(r=>String(r).toLowerCase()).some(r=>['system_admin','usarec_admin','420t_admin','admin'].includes(r)))
      if(!admin){
        // redirect to home if not authorized
        try{ navigate('/') }catch(e){}
        return
      }
    }catch(e){ try{ navigate('/') }catch(e){}; return }
    setLoading(true)
    try{
      const qs = new URLSearchParams()
      if (datasetFilter) qs.set('dataset_key', datasetFilter)
      if (sourceFilter) qs.set('source_name', sourceFilter)
      if (validatedFilter !== '') qs.set('validated', validatedFilter)
      qs.set('limit', rowsPerPage)
      qs.set('offset', page * rowsPerPage)
      const path = '/uploads/list?' + qs.toString()
      const resp = await apiFetch(path)
      if (resp && resp.uploads) {
        setUploads(resp.uploads)
        setTotal(resp.total || 0)
      } else {
        setUploads([])
        setTotal(0)
      }
    }catch(e){
      console.error(e)
      setUploads([])
      setTotal(0)
      // eslint-disable-next-line no-alert
      alert('Failed to load uploads')
    }finally{ setLoading(false) }
  }

  useEffect(()=>{ load() }, [page, rowsPerPage])

  async function handleValidate(id){
    if(!window.confirm('Validate staging upload #' + id + '?')) return
    try{
      await apiFetch('/uploads/validate', { method: 'POST', body: JSON.stringify({ staging_id: id }), headers: {'Content-Type':'application/json'} })
      load()
    }catch(e){ console.error(e); alert('Validate failed: ' + (e.message || e)) }
  }

  async function handleCommit(id){
    if(!window.confirm('Commit staging upload #' + id + ' into warehouse? This is idempotent.')) return
    try{
      await apiFetch('/uploads/commit', { method: 'POST', body: JSON.stringify({ staging_id: id }), headers: {'Content-Type':'application/json'} })
      load()
    }catch(e){ console.error(e); alert('Commit failed: ' + (e.message || e)) }
  }

  function handleChangePage(event, newPage){ setPage(newPage) }
  function handleChangeRowsPerPage(e){ setRowsPerPage(parseInt(e.target.value, 10)); setPage(0) }

  return (
    <Box sx={{p:3}}>
      <Paper sx={{p:2, mb:2}}>
        <Box sx={{display:'flex', gap:2, alignItems:'center'}}>
          <TextField label="Dataset" size="small" value={datasetFilter} onChange={e=>setDatasetFilter(e.target.value)} />
          <TextField label="Source" size="small" value={sourceFilter} onChange={e=>setSourceFilter(e.target.value)} />
          <Select size="small" value={validatedFilter} onChange={e=>setValidatedFilter(e.target.value)} displayEmpty>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="1">Validated</MenuItem>
            <MenuItem value="0">Not validated</MenuItem>
          </Select>
          <Button variant="contained" onClick={()=>{ setPage(0); load() }}>Apply</Button>
          <Button onClick={()=>{ setDatasetFilter(''); setSourceFilter(''); setValidatedFilter(''); setPage(0); load() }}>Clear</Button>
          <Box sx={{flex:1}} />
          <Button onClick={load} startIcon={loading ? <CircularProgress size={16} /> : null}>Refresh</Button>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Dataset</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Uploaded At</TableCell>
              <TableCell>Validated</TableCell>
              <TableCell>Rows</TableCell>
              <TableCell>Preview</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {uploads.map(u => (
              <TableRow key={u.id} hover>
                <TableCell>{u.id}</TableCell>
                <TableCell>{u.dataset_key}</TableCell>
                <TableCell>{u.source_name}</TableCell>
                <TableCell>{u.uploaded_at}</TableCell>
                <TableCell>{u.validated ? 'yes' : 'no'}</TableCell>
                <TableCell>{u.row_count}</TableCell>
                <TableCell title={u.preview} sx={{maxWidth:300, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{u.preview}</TableCell>
                <TableCell>
                  <Button size="small" onClick={()=>handleValidate(u.id)} sx={{mr:1}}>Validate</Button>
                  <Button size="small" variant="contained" onClick={()=>handleCommit(u.id)}>Commit</Button>
                </TableCell>
              </TableRow>
            ))}
            {uploads.length===0 && (
              <TableRow><TableCell colSpan={8} sx={{p:2}}>No uploads found.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination component="div" count={total} page={page} onPageChange={handleChangePage} rowsPerPage={rowsPerPage} onRowsPerPageChange={handleChangeRowsPerPage} />
      </TableContainer>
    </Box>
  )
}
