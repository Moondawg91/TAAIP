import React, {useEffect, useState} from 'react'
import { Box, Typography, Grid, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip } from '@mui/material'
import api from '../../api/client'

export default function MarketIntelligencePage(){
  const [summary, setSummary] = useState<any>(null)
  const [zips, setZips] = useState<any[]>([])

  useEffect(()=>{
    let mounted = true
    api.getMarketSummary().then(r=>{ if(mounted) setSummary(r) }).catch(()=>{})
    api.listMarketZips().then(r=>{ if(mounted) setZips((r && r.rows) ? r.rows : []) }).catch(()=>{})
    return ()=>{ mounted = false }
  }, [])

  return (
    <Box sx={{p:3, bgcolor:'background.default', color:'text.primary', minHeight:'100vh'}}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <Typography variant="h4">Market Intelligence</Typography>
        {summary && summary.data_as_of ? <Chip label={`Data as of ${summary.data_as_of}`} /> : null}
      </Box>

      <Grid container spacing={2} sx={{mt:2}}>
        <Grid item xs={12} md={4}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="subtitle2">Army Potential</Typography>
            <Typography variant="h6">{summary?.kpis?.total_army_potential ?? 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="subtitle2">DoD Potential</Typography>
            <Typography variant="h6">{summary?.kpis?.total_dod_potential ?? 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="subtitle2">Potential Remaining</Typography>
            <Typography variant="h6">{summary?.kpis?.total_potential_remaining ?? 0}</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{mt:3}}>
        <Typography variant="h6">ZIP-level Metrics</Typography>
        {(!zips || zips.length===0) ? (
          <Typography sx={{mt:1, color:'text.secondary'}}>Dataset Missing: Market ZIP Metrics not loaded</Typography>
        ) : (
          <Table size="small" sx={{mt:1, bgcolor:'transparent', borderRadius:1}}>
            <TableHead>
              <TableRow>
                <TableCell>Station</TableCell>
                <TableCell>ZIP</TableCell>
                <TableCell>Category</TableCell>
                <TableCell align="right">Army Pot</TableCell>
                <TableCell align="right">DoD Pot</TableCell>
                <TableCell align="right">Army Share</TableCell>
                <TableCell align="right">GA</TableCell>
                <TableCell align="right">SA</TableCell>
                <TableCell align="right">VOL</TableCell>
                <TableCell align="right">Potential Rem</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {zips.map(z => (
                <TableRow key={z.id}>
                  <TableCell>{z.station_rsid}</TableCell>
                  <TableCell>{z.zip}</TableCell>
                  <TableCell>{z.zip_category}</TableCell>
                  <TableCell align="right">{z.army_potential ?? 0}</TableCell>
                  <TableCell align="right">{z.dod_potential ?? 0}</TableCell>
                  <TableCell align="right">{z.army_share_of_potential ?? ''}</TableCell>
                  <TableCell align="right">{z.contracts_ga ?? 0}</TableCell>
                  <TableCell align="right">{z.contracts_sa ?? 0}</TableCell>
                  <TableCell align="right">{z.contracts_vol ?? 0}</TableCell>
                  <TableCell align="right">{z.potential_remaining ?? 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Box>
    </Box>
  )
}
