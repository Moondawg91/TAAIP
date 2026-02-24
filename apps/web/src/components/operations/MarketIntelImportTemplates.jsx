import React from 'react'
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material'

export default function MarketIntelImportTemplates({templates}){
  return (
    <Box>
      <Typography variant="subtitle2" sx={{mb:1}}>Import Templates</Typography>
      <List dense>
        {templates && templates.length>0 ? templates.map((t,i)=> (
          <ListItem key={i}><ListItemText primary={t.name} secondary={t.description} /></ListItem>
        )) : <ListItem><ListItemText primary="No templates available"/></ListItem>}
      </List>
    </Box>
  )
}
