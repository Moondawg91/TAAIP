import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary'
import { ThemeProvider } from './theme/ThemeProvider'
import { RsidProvider } from './state/rsidStore'
import { PeriodProvider } from './state/periodStore'
import { ToastProvider } from './components/shared/ToastProvider'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <RsidProvider>
        <PeriodProvider>
          <ToastProvider>
            <ErrorBoundary fallbackTitle="We hit a snag" fallbackMessage="A dashboard failed to render. Try reloading.">
              <App />
            </ErrorBoundary>
          </ToastProvider>
        </PeriodProvider>
      </RsidProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
