import { useEffect, useRef } from 'react'
import Prism from 'prismjs'
import 'prismjs/components/prism-sql'
import ResultsTabView from './ResultsTabView'

type SqlOutputProps = {
  sql: string
  aiMode: string
  onCopy: () => void
  onExecute: () => void
  loading: boolean
  result: { columns: string[]; rows: Record<string, unknown>[]; row_count?: number } | null
}

function SqlOutput({ sql, aiMode, onCopy, onExecute, loading, result }: SqlOutputProps) {
  const codeRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (codeRef.current && sql) {
      codeRef.current.textContent = sql
      Prism.highlightElement(codeRef.current)
    }
  }, [sql])

  return (
    <div className="sql-content">
      <div className="code-card">
        <div className="code-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="code-lang">SQL</span>
            {aiMode && (
              <span className={`mode-badge mode-${aiMode}`}>
                {aiMode === 'openai' ? '🤖 OpenAI' : '⚡ Fallback'}
              </span>
            )}
          </div>
          <div className="code-actions">
            <button className="btn-icon" onClick={onCopy} disabled={!sql} title="Copy SQL">
              📋
            </button>
          </div>
        </div>
        <div className="code-body">
          {sql ? (
            <pre style={{ margin: 0 }}>
              <code ref={codeRef} className="language-sql">
                {sql}
              </code>
            </pre>
          ) : (
            <div className="code-placeholder">
              ✨ AI-generated SQL will appear here
            </div>
          )}
        </div>
      </div>

      <div className="action-bar">
        <button className="btn btn-primary" onClick={onExecute} disabled={!sql || loading}>
          {loading ? (
            <>
              <span className="loading-spinner">⏳</span>
              Executing Query...
            </>
          ) : (
            <>
              <span>▶</span>
              Execute Query
            </>
          )}
        </button>
        <button className="btn btn-ghost" onClick={onCopy} disabled={!sql}>
          📋 Copy SQL
        </button>
      </div>

      {loading && (
        <div className="execution-status">
          <div className="status-spinner">⏳</div>
          <div className="status-text">
            <p className="status-title">Executing Query...</p>
            <p className="status-subtitle">Retrieving results from database</p>
          </div>
        </div>
      )}

      {result && !loading && (
        <ResultsTabView
          columns={result.columns}
          rows={result.rows}
          rowCount={result.row_count}
        />
      )}
    </div>
  )
}

export default SqlOutput
