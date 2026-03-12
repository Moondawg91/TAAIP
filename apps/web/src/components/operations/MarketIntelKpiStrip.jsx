import React from 'react'
import { Box, Grid } from '@mui/material'
import DashboardCard from '../../components/ui/DashboardCard'
import KpiTile from '../../components/ui/KpiTile'

export default function MarketIntelKpiStrip({summary}){
  const k = summary && summary.kpis ? summary.kpis : {}
  return (
    <DashboardCard>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="Market Potential" value={k.market_potential_total ?? '—'} sub="total" /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="Contracts" value={k.contracts_total ?? '—'} /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="Potential Remaining" value={k.potential_remaining ?? '—'} /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="Army Share %" value={k.army_share_pct_weighted ?? '—'} /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="P2P Avg" value={k.p2p_avg ?? '—'} /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="ZIP Count" value={k.zip_count ?? '—'} /></Grid>
        <Grid item xs={6} sm={3} md={1}><KpiTile label="CBSA Count" value={k.cbsa_count ?? '—'} /></Grid>
        <Grid item xs={12} sm={12} md={4}><KpiTile label="Category Counts" value={k.category_counts ? JSON.stringify(k.category_counts) : '—'} sub="breakdown" /></Grid>
      </Grid>
    </DashboardCard>
  )
}
