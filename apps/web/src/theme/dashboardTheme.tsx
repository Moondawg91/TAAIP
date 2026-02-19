import React from 'react'

export const lightTheme = {
  background: 'bg-white',
  surface: 'bg-gray-50',
  text: 'text-gray-900',
  muted: 'text-gray-500',
  primary: '#0ea5a6',
}

export const darkTheme = {
  background: 'bg-gray-900',
  surface: 'bg-gray-800',
  text: 'text-gray-100',
  muted: 'text-gray-400',
  primary: '#06b6d4',
}

export const ThemeProvider: React.FC<{ dark?: boolean; children?: React.ReactNode }> = ({ dark = false, children }) => {
  const theme = dark ? darkTheme : lightTheme
  return (
    <div className={dark ? 'dark' : ''}>
      {children}
    </div>
  )
}

export default ThemeProvider
