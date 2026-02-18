import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { ThemeProvider, CssBaseline } from '@mui/material'
import muiTheme from './theme/muiTheme'

const container = document.getElementById('root')
const root = createRoot(container)
root.render(
	<ThemeProvider theme={muiTheme}>
		<CssBaseline />
		<App />
	</ThemeProvider>
)
