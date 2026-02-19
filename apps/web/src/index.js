import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { ThemeProvider, CssBaseline } from '@mui/material'
import muiTheme from './theme/muiTheme'

// Global error handlers to avoid uncaught promise rejections crashing the app
if (typeof window !== 'undefined') {
	window.addEventListener('unhandledrejection', (ev) => {
		try {
			// ev.reason may be undefined in some browsers; provide a friendly log
			console.error('Unhandled promise rejection:', ev.reason || ev)
		} catch (e) {
			// swallow
		}
		// prevent default to avoid noisy browser console errors
		try { ev.preventDefault && ev.preventDefault() } catch (e) {}
	})

	window.addEventListener('error', (ev) => {
		try {
			console.error('Global error captured:', ev.error || ev.message || ev)
		} catch (e) {}
	})
}

const container = document.getElementById('root')
const root = createRoot(container)
root.render(
	<ThemeProvider theme={muiTheme}>
		<CssBaseline />
		<App />
	</ThemeProvider>
)
