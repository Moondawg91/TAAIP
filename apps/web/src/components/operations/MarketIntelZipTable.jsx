import React from 'react'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material'

export default function MarketIntelZipTable({data, loading}){
  if (loading) return <Typography variant="body2">Loading ZIP rankings…</Typography>
  if (!data || data.length===0) return <Typography variant="body2">No ZIP rankings available.</Typography>
  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>ZIP</TableCell>
            <TableCell>Category</TableCell>
            <TableCell>FQMA</TableCell>
            <TableCell>Youth</TableCell>
            <TableCell>Market Potential</TableCell>
            <TableCell>Contracts</TableCell>
            <TableCell>Potential Remaining</TableCell>
            <TableCell>CBSA</TableCell>
            <TableCell>Opportunity</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((r,i)=> (
            <TableRow key={i}>
              <TableCell>{r.zip5}</TableCell>
              <TableCell>{r.market_category||r.zip_category||'—'}</TableCell>
              <TableCell>{r.fqma ?? '—'}</TableCell>
              <TableCell>{r.youth_pop_17_24 ?? r.youth_pop ?? '—'}</TableCell>
              <TableCell>{r.market_potential ?? '—'}</TableCell>
              <TableCell>{r.contracts_total ?? r.contracts ?? '—'}</TableCell>
              <TableCell>{r.potential_remaining ?? '—'}</TableCell>
              <TableCell>{r.cbsa_code}</TableCell>
              <TableCell>{r.opportunity_score ?? (r.opportunity || '—')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
