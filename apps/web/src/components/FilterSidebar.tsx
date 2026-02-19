import React from 'react'

type Props = {
  filters: Record<string, any[]>
  selected: Record<string, any>
  onChange: (name: string, value: any) => void
}

const FilterSidebar: React.FC<Props> = ({ filters, selected, onChange }) => {
  return (
    <div className="p-4">
      <h2 className="text-lg font-medium mb-4">Filters</h2>
      <div className="space-y-4">
        {Object.keys(filters).map(key => (
          <div key={key}>
            <label className="block text-sm font-semibold mb-2">{key}</label>
            <select
              value={selected[key] ?? ''}
              onChange={e => onChange(key, e.target.value || null)}
              className="w-full rounded border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-2 text-sm"
            >
              <option value="">All</option>
              {filters[key].map((opt: any) => (
                <option key={String(opt)} value={opt}>{String(opt)}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FilterSidebar
