import React from 'react'
import { Box, Typography } from '@mui/material'

export default function PageHeaderStrip({ left, center, right }:{ left?:React.ReactNode, center?:React.ReactNode, right?:React.ReactNode }){
  return (
    <Box sx={{ display:'flex', alignItems:'center', gap:2, height:56, px:1 }}>
      <Box sx={{ display:'flex', flexDirection:'column' }}>
        {left}
      </Box>
      <Box sx={{ flex:1, display:'flex', justifyContent:'center' }}>
        {center}
      </Box>
      <Box>
        {right}
      </Box>
    </Box>
  )
}
