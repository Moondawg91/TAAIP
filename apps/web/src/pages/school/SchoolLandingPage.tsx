import React from 'react'
import { Box, Typography } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import DualModeTabs from '../../components/DualModeTabs'
// TopFilterBar rendered centrally by shell
import ExportMenu from '../../components/ExportMenu'

export default function SchoolLandingPage(){
  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center'}}>
        <Typography variant="h4">School Recruiting Program</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[]} filename="school_recruiting" />
        </Box>
      </Box>
      <DualModeTabs />
      <ZeroState title="Data not loaded" message="No program dashboards available — import datasets or check API connectivity." />
    </Box>
  )
}
