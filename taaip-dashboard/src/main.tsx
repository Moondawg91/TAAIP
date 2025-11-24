import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary fallbackTitle="We hit a snag" fallbackMessage="A dashboard failed to render. Try reloading.">
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
