import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, Table, TableBody, TableRow, TableCell } from '@mui/material'
import EmptyState from '../../components/common/EmptyState'
import { getFactProduction } from '../../api/client'

export default function ProductionDashboardPage(){
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ load() }, [])

  async function load(){
    setLoading(true)
    try{
      const r = await getFactProduction({ limit: 200 })
      setRows(r || [])
    }catch(e){ console.error('load fact production', e) }
    finally{ setLoading(false) }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Production Dashboard</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Overview of production metrics and KPIs.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Recent Production Rows ({rows.length})</Typography>
          {( !loading && (!rows || rows.length===0) ) ? (
            <EmptyState title="No production data" subtitle="No production rows available for your echelon." actionLabel="Refresh" onAction={load} />
          ) : (
            <Table size="small">
              <TableBody>
                {(rows || []).slice(0,20).map((r:any)=> (
                  <TableRow key={r.id || Math.random()}>
                    <TableCell>{r.date_key}</TableCell>
                    <TableCell>{r.org_unit_id}</TableCell>
                    <TableCell>{r.metric_key}</TableCell>
                    <TableCell>{r.metric_value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
