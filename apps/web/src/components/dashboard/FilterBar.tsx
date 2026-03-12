import React from 'react'
import { Box, Typography } from '@mui/material'
import { useFilters } from '../../contexts/FilterContext'

export default function FilterBar(){
  const { filters } = useFilters()
  const displayFy = filters?.fy || '—'
  const displayQtr = filters?.qtr || '—'
  const displayUnit = filters?.unit_rsid || 'USAREC'
  const displayStation = filters?.station || 'All'

  return (
    <Box sx={{ display:'flex', gap:2, alignItems:'center', mx:2 }}>
      <Box>
        <Typography variant="caption" color="text.secondary">FY</Typography>
        <Typography variant="body2">{displayFy}</Typography>
      </Box>

      <Box>
        <Typography variant="caption" color="text.secondary">Quarter</Typography>
        <Typography variant="body2">{displayQtr}</Typography>
      </Box>

      <Box>
        <Typography variant="caption" color="text.secondary">Unit</Typography>
        <Typography variant="body2">{displayUnit}</Typography>
      </Box>

      <Box>
        <Typography variant="caption" color="text.secondary">Station</Typography>
        <Typography variant="body2">{displayStation}</Typography>
      </Box>
    </Box>
  )
}
