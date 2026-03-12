import React from 'react'
import { Box, Typography, Avatar, List, ListItem, ListItemAvatar, ListItemText } from '@mui/material'
import { useTheme } from '@mui/material/styles'

export default function RecognitionPanel(){
  const theme = useTheme()
  const panelBg = theme.palette.mode === 'dark' ? 'background.paper' : '#0f1720'
  // Empty-safe minimal recognition panel (compact)
  const recognitions: any[] = []
  return (
    <Box sx={{ p:2, bgcolor: panelBg, borderRadius: '4px' }}>
      <Typography variant="h6" sx={{ mb:1 }}>Recognition</Typography>
      {recognitions.length === 0 ? (
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>No recognitions available.</Typography>
      ) : (
        <List dense>
          {recognitions.map(r => (
            <ListItem key={r.id} sx={{ py:0.5 }}>
              <ListItemAvatar>
                <Avatar sx={{ width:28, height:28 }}>{r.initials || '?'}</Avatar>
              </ListItemAvatar>
              <ListItemText primary={r.title} secondary={r.subtitle} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  )
}
