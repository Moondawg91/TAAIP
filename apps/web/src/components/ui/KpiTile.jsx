import React from 'react'
import { Box, Typography } from '@mui/material'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import tokens from '../../theme/tokens'

export default function KpiTile({ label, value, trend = 0, sub }) {
  const Trend = trend >= 0 ? ArrowUpwardIcon : ArrowDownwardIcon
  const trendColor = trend > 0 ? tokens.colors.accentSuccess : trend < 0 ? tokens.colors.accentDanger : tokens.colors.textSecondary
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: tokens.spacing.xs }}>
      <Typography sx={{ fontSize: 12, fontWeight: 700, color: tokens.colors.textSecondary, letterSpacing: 0.6, textTransform: 'uppercase' }}>{label}</Typography>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: tokens.spacing.sm }}>
        <Typography sx={{ fontSize: 26, fontWeight: 800, color: tokens.colors.textPrimary }}>{value}</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', color: trendColor }}>
          <Trend fontSize="small" />
          <Typography sx={{ fontSize: 12, color: trendColor, ml: 0.5 }}>{Math.abs(trend)}%</Typography>
        </Box>
      </Box>
      {sub ? <Typography sx={{ fontSize: 12, color: tokens.colors.textSecondary }}>{sub}</Typography> : null}
    </Box>
  )
}
