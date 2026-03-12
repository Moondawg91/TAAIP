import React, { useEffect, useState } from 'react'
import { Box, Typography, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import { importTemplate } from '../../api/client'
import ExportMenu from '../../components/ExportMenu'

export default function SchoolDataPage(){
  const templates = [ 'SCHOOL_DIM','SCHOOL_ACCOUNTS','SCHOOL_CONTACTS','SCHOOL_ACTIVITIES','SCHOOL_MILESTONES','SCHOOL_PROGRAM_LEADS' ]

  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Typography variant="h4">Data & Imports (School)</Typography>
        <ExportMenu data={templates.map(t=>({ dataset: t, template_url: `/api/import/templates/${t}` }))} filename="school_data_templates" />
      </Box>
      <Typography variant="subtitle2" sx={{ color:'text.secondary', mt:1 }}>Download templates and review last import jobs.</Typography>

      <Box sx={{ mt:1 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Dataset</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templates.map(t=> (
              <TableRow key={t}>
                <TableCell>{t}</TableCell>
                <TableCell>
                  <Button variant="outlined" href={`/api/import/templates/${t}`}>Download template</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      <Box sx={{ mt:1 }}>
        <Typography variant="body2" color="text.secondary">Data not loaded. Load datasets in Data Hub. <a href="/data-hub" style={{ fontSize:13 }}>Go to Data Hub</a></Typography>
      </Box>
    </Box>
  )
}
