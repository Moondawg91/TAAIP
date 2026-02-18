import React from 'react'

type KPI = {
  id: string
  title: string
  value: string | number
  subtitle?: string
  delta?: string | number | null
}

type Props = {
  kpis: KPI[]
}

const KPIGrid: React.FC<Props> = ({ kpis }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map(k => (
        <div key={k.id} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg p-4 shadow-sm">
          <div className="text-sm text-gray-500 dark:text-gray-300">{k.title}</div>
          <div className="mt-2 text-2xl font-semibold">{k.value}</div>
          {k.delta !== undefined && k.delta !== null && (
            <div className="text-sm text-gray-500 mt-1">Delta: {k.delta}</div>
          )}
          {k.subtitle && <div className="text-xs text-gray-400 mt-1">{k.subtitle}</div>}
        </div>
      ))}
    </div>
  )
}

export default KPIGrid
