import { useEffect, useState } from 'react'
import ResultsTable from './ResultsTable'
import VisualizationView from './VisualizationView'

type RequestPhase = 'idle' | 'generating' | 'generated' | 'executing' | 'ready'
type TabType = 'table' | 'visualization'

type ResultsTabViewProps = {
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount?: number
  phase: RequestPhase
}

function ResultsTabView({ columns, rows, rowCount, phase }: ResultsTabViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('table')
  const [visualizing, setVisualizing] = useState(false)

  useEffect(() => {
    if (activeTab !== 'visualization' || phase !== 'ready' || rows.length === 0) {
      setVisualizing(false)
      return
    }

    setVisualizing(true)
    const timer = window.setTimeout(() => setVisualizing(false), 180)
    return () => window.clearTimeout(timer)
  }, [activeTab, phase, rows.length, columns.length])

  return (
    <div className="results-tab-view">
      <div className="results-header">
        <div className="tab-buttons">
          <button
            className={`tab-btn ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            <span className="tab-icon">Table</span>
            Table View
          </button>
          <button
            className={`tab-btn ${activeTab === 'visualization' ? 'active' : ''}`}
            onClick={() => setActiveTab('visualization')}
          >
            <span className="tab-icon">Chart</span>
            Visualization View
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
          <ResultsTable columns={columns} rows={rows} rowCount={rowCount} phase={phase} />
        ) : (
          <VisualizationView columns={columns} rows={rows} loading={visualizing || phase === 'executing'} />
        )}
      </div>
    </div>
  )
}

export default ResultsTabView
