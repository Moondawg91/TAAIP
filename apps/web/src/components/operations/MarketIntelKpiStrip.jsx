import React from 'react'
import { Box, Grid, Paper, Typography } from '@mui/material'

export default function MarketIntelKpiStrip({summary}){
  const k = summary && summary.kpis ? summary.kpis : {}
  return (
    <Paper sx={{p:1, bgcolor:'background.paper', borderRadius:'4px'}}>
      <Grid container spacing={1}>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">Market Potential</Typography><Typography variant="body2">{k.market_potential_total ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">Contracts</Typography><Typography variant="body2">{k.contracts_total ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">Potential Remaining</Typography><Typography variant="body2">{k.potential_remaining ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">Army Share %</Typography><Typography variant="body2">{k.army_share_pct_weighted ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">P2P Avg</Typography><Typography variant="body2">{k.p2p_avg ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">ZIP Count</Typography><Typography variant="body2">{k.zip_count ?? '—'}</Typography></Grid>
        <Grid item xs={6} sm={3} md={1}><Typography variant="caption">CBSA Count</Typography><Typography variant="body2">{k.cbsa_count ?? '—'}</Typography></Grid>
        <Grid item xs={12} sm={12} md={4}><Typography variant="caption">Category Counts</Typography><Typography variant="body2">{k.category_counts ? JSON.stringify(k.category_counts) : '—'}</Typography></Grid>
      </Grid>
    </Paper>
  )
}
