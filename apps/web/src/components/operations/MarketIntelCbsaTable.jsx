import React from 'react'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material'

export default function MarketIntelCbsaTable({data, loading}){
  if (loading) return <Typography variant="body2">Loading CBSA rollup…</Typography>
  if (!data || data.length===0) return <Typography variant="body2">No CBSA rollup available.</Typography>
  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>CBSA</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>FQMA</TableCell>
            <TableCell>Youth</TableCell>
            <TableCell>Market Potential</TableCell>
            <TableCell>Contracts</TableCell>
            <TableCell>P2P</TableCell>
            <TableCell>Potential Remaining</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((r,i)=> (
            <TableRow key={i}>
              <TableCell>{r.cbsa_code}</TableCell>
              <TableCell>{r.cbsa_name || r.cbsa || '—'}</TableCell>
              <TableCell>{r.fqma ?? '—'}</TableCell>
              <TableCell>{r.youth_pop_17_24 ?? r.youth_pop ?? '—'}</TableCell>
              <TableCell>{r.market_potential ?? '—'}</TableCell>
              <TableCell>{r.contracts_total ?? r.contracts ?? '—'}</TableCell>
              <TableCell>{r.p2p ?? '—'}</TableCell>
              <TableCell>{r.potential_remaining ?? '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
