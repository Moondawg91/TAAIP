import React from 'react'
import { Paper } from '@mui/material'
import tokens from '../../theme/tokens'

export default function DashboardCard({ children, sx = {}, ...rest }) {
  return (
    <Paper elevation={0} sx={{
      background: tokens.colors.surface,
      border: `1px solid ${tokens.colors.borderSubtle}`,
      borderRadius: tokens.radius,
      padding: tokens.spacing.md,
      boxShadow: '0 10px 30px rgba(6,10,18,0.12)',
      ...sx
    }} {...rest}>
      {children}
    </Paper>
  )
}
