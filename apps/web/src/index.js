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
			const reason = ev && ev.reason ? ev.reason : ev
			let message = 'Unknown promise rejection'
			let details = null
			if (reason instanceof Error) {
				message = reason.message || message
				details = reason.stack || String(reason)
			} else {
				try { details = JSON.stringify(reason) } catch (e) { details = String(reason) }
				message = details || message
			}
			console.error('Unhandled promise rejection:', message)
			console.error(details)

			// show a small non-blocking banner in dev for easier visibility
			try{
				let banner = document.getElementById('dev-unhandled-rejection-banner')
				if (!banner){
					banner = document.createElement('div')
					banner.id = 'dev-unhandled-rejection-banner'
					banner.style.position = 'fixed'
					banner.style.right = '12px'
					banner.style.bottom = '12px'
					banner.style.padding = '10px 14px'
					banner.style.background = 'rgba(200,40,40,0.95)'
					banner.style.color = 'white'
					banner.style.zIndex = 999999
					banner.style.fontFamily = 'monospace'
					banner.style.fontSize = '12px'
					document.body.appendChild(banner)
				}
				banner.textContent = `Unhandled rejection: ${String(message).slice(0,120)}`
				setTimeout(()=>{ try{ banner.textContent = '' }catch(e){} }, 8000)
			} catch (e) {}
		} catch (e) {
			console.error('Error while handling unhandledrejection:', e)
		}
		// prevent default to avoid noisy browser console errors
		try { ev.preventDefault && ev.preventDefault() } catch (e) { console.error(e) }
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
