import React from 'react'
import { Box, Chip, Typography } from '@mui/material'

export default function MarketIntelCategoriesStrip({ categories }){
  if(!categories || !categories.categories) return <Box sx={{mb:1}} />
  const cats = categories.categories
  return (
    <Box sx={{display:'flex', gap:1, alignItems:'center', mb:1}}>
      <Typography variant="subtitle2">Categories:</Typography>
      {cats.map((c, i)=> (
        <Chip key={i} label={`${c.category || c.key || 'cat'} (${c.count ?? c.total ?? '-'})`} size="small" sx={{borderRadius:'4px'}} />
      ))}
    </Box>
  )
}
