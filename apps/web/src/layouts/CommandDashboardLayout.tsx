import React, { useState } from 'react'
import KPIGrid from '../components/KPIGrid'
import FilterSidebar from '../components/FilterSidebar'
import { ThemeProvider } from '../theme/dashboardTheme'

type KPI = {
  id: string
  title: string
  value: string | number
  subtitle?: string
  delta?: string | number | null
}

type Props = {
  kpis: KPI[]
  filters: Record<string, any[]>
  selectedFilters: Record<string, any>
  onFilterChange: (name: string, value: any) => void
  lastRefresh?: string
  onRefresh?: () => void
  children?: React.ReactNode
  dark?: boolean
}

const CommandDashboardLayout: React.FC<Props> = ({
  kpis,
  filters,
  selectedFilters,
  onFilterChange,
  lastRefresh,
  onRefresh,
  children,
  dark = false,
}) => {
  const [open, setOpen] = useState(true)

  return (
    <ThemeProvider dark={dark}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-semibold">Command Dashboard</h1>
            {lastRefresh && <div className="text-sm text-gray-600 dark:text-gray-300">Last refresh: {lastRefresh}</div>}
          </div>
          <div className="flex items-center space-x-3">
            <button onClick={() => onRefresh && onRefresh()} className="px-3 py-1 rounded bg-sky-600 text-white text-sm">Refresh</button>
            <button onClick={() => setOpen(s => !s)} className="px-3 py-1 rounded border border-gray-300 dark:border-gray-700 text-sm">{open ? 'Hide Filters' : 'Show Filters'}</button>
          </div>
        </header>

        <div className="flex">
          <aside className={`${open ? 'w-72' : 'w-0'} transition-all duration-200 overflow-hidden border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800`}> 
            {open && (
              <div className="h-full">
                <FilterSidebar filters={filters} selected={selectedFilters} onChange={onFilterChange} />
              </div>
            )}
          </aside>

          <main className="flex-1 p-6">
            <section className="mb-6">
              <KPIGrid kpis={kpis} />
            </section>

            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {children}
            </section>
          </main>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default CommandDashboardLayout
