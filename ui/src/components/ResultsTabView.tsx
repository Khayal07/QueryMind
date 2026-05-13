import { useState } from 'react'
import ResultsTable from './ResultsTable'
import VisualizationView from './VisualizationView'

type ResultsTabViewProps = {
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount?: number
  visualizing?: boolean
}

type TabType = 'table' | 'visualization'

function ResultsTabView({ columns, rows, rowCount, visualizing = false }: ResultsTabViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('table')

  if (!rows || rows.length === 0) {
    return null
  }

  return (
    <div className="results-tab-view">
      <div className="results-header">
        <div className="tab-buttons">
          <button
            className={`tab-btn ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            <span className="tab-icon">📋</span>
            Table View
          </button>
          <button
            className={`tab-btn ${activeTab === 'visualization' ? 'active' : ''}`}
            onClick={() => setActiveTab('visualization')}
          >
            <span className="tab-icon">📊</span>
            Visualization
            {visualizing && <span className="tab-loading">...</span>}
          </button>
        </div>
        <div className="results-meta">
          <span className="result-count">
            {rowCount ?? rows.length} row{(rowCount ?? rows.length) !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="tab-content">
        {activeTab === 'table' ? (
          <ResultsTable columns={columns} rows={rows} rowCount={rowCount} />
        ) : (
          <VisualizationView columns={columns} rows={rows} />
        )}
      </div>
    </div>
  )
}

export default ResultsTabView
