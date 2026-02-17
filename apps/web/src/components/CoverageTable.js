import React from 'react'
import {Card, CardContent, Typography, Box} from '@mui/material'
import {DataGrid} from '@mui/x-data-grid'

export default function CoverageTable({rows}){
  const columns = [
    {field:'unit_id', headerName:'Unit ID', width:120},
    {field:'display_name', headerName:'Display Name', width:220},
    {field:'MK', headerName:'MK', width:90},
    {field:'MW', headerName:'MW', width:90},
    {field:'MO', headerName:'MO', width:90},
    {field:'SU', headerName:'SU', width:90},
    {field:'UNK', headerName:'UNK', width:90},
    {field:'total', headerName:'Total', width:100},
    {field:'market_potential', headerName:'Market Potential', width:160},
  ]

  const hasRows = Array.isArray(rows) && rows.length > 0

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle1">Coverage by Unit</Typography>
        {!hasRows ? (
          <Box sx={{p:2}}>
            <Typography variant="body2" color="text.secondary">No sub-unit breakdown available for this scope. TODO: Import sub-unit coverage or implement sub-unit endpoint.</Typography>
          </Box>
        ) : (
          <div style={{height:420, width:'100%'}}>
            <DataGrid rows={rows.map((r,i)=> ({id:i, ...r}))} columns={columns} pageSize={25} rowsPerPageOptions={[25]} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
