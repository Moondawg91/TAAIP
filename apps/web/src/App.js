import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import ShellLayout from './layout/ShellLayout'

import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import DashboardDetailPage from './pages/DashboardDetailPage'
import QBRPage from './pages/QBRPage'
import CommandCenterPage from './pages/CommandCenterPage'
import ProjectsPage from './pages/ProjectsPage'
import MeetingsPage from './pages/MeetingsPage'
import CalendarPage from './pages/CalendarPage'
import ImportCenterPage from './pages/ImportCenterPage'

export default function App() {
  return (
    <Router>
      <ShellLayout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:id" element={<DashboardDetailPage />} />
          <Route path="/qbr" element={<QBRPage />} />
          <Route path="/dashboards/command-center" element={<CommandCenterPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/meetings" element={<MeetingsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/import-center" element={<ImportCenterPage />} />
        </Routes>
      </ShellLayout>
    </Router>
  )
}
