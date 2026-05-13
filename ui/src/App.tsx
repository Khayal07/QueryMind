import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import SchemaViewer from './components/SchemaViewer'
import SqlOutput from './components/SqlOutput'
import PromptBar from './components/PromptBar'
import QueryHistory, { type HistoryEntry } from './components/QueryHistory'
import Toast, { type ToastMessage } from './components/Toast'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

type SchemaType = Record<string, Record<string, string>>
type QueryResult = { columns: string[]; rows: Record<string, unknown>[]; row_count?: number }

let nextToastId = 1
let nextHistoryId = 1

function App() {
  const [schema, setSchema] = useState<SchemaType>({})
  const [prompt, setPrompt] = useState('')
  const [sql, setSql] = useState('')
  const [aiMode, setAiMode] = useState('')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const [historyOpen, setHistoryOpen] = useState(true)

  const addToast = useCallback((type: ToastMessage['type'], text: string) => {
    setToasts((prev) => [...prev, { id: nextToastId++, type, text }])
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // Load schema on mount
  useEffect(() => {
    axios
      .get(`${API_BASE}/schema`)
      .then((res) => setSchema(res.data.schema))
      .catch(() => setError('Unable to load schema. Is the backend running?'))
  }, [])

  // Generate SQL
  const handleGenerate = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await axios.post(`${API_BASE}/generate`, { prompt })
      const newSql = res.data.sql
      const mode = res.data.ai_mode || 'fallback'
      setSql(newSql)
      setAiMode(mode)
      setHistory((prev) => [
        {
          id: nextHistoryId++,
          prompt,
          sql: newSql,
          aiMode: mode,
          timestamp: new Date(),
        },
        ...prev,
      ])
      addToast('success', 'SQL generated successfully')
    } catch {
      setError('Failed to generate SQL. Check backend logs.')
      addToast('error', 'SQL generation failed')
    } finally {
      setLoading(false)
    }
  }

  // Execute SQL
  const handleExecute = async () => {
    if (!sql) return
    setExecuting(true)
    setError('')
    try {
      const res = await axios.post(`${API_BASE}/execute`, { sql })
      setResult(res.data)
      addToast('success', `Query returned ${res.data.row_count ?? res.data.rows?.length ?? 0} rows`)
    } catch {
      setError('Query execution failed. Check SQL syntax.')
      addToast('error', 'Query execution failed')
    } finally {
      setExecuting(false)
    }
  }

  // Copy to clipboard
  const copyToClipboard = () => {
    navigator.clipboard.writeText(sql).then(() => {
      addToast('info', 'SQL copied to clipboard')
    })
  }

  // Restore from history
  const handleHistorySelect = (entry: HistoryEntry) => {
    setPrompt(entry.prompt)
    setSql(entry.sql)
    setAiMode(entry.aiMode)
    setResult(null)
    setError('')
  }

  return (
    <>
      <Toast toasts={toasts} onDismiss={dismissToast} />

      <div className="app-shell">
        {/* ── Header ─────────────────────────────── */}
        <header className="page-header">
          <div className="brand">
            <div className="brand-icon">Q</div>
            <div className="brand-text">
              <h1>QueryMind</h1>
              <p>Natural language → SQL, powered by schema-aware AI</p>
            </div>
          </div>
          <div className="header-actions">
            <div className="ai-badge">
              <span className="dot" />
              AI Ready
            </div>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setHistoryOpen((o) => !o)}
            >
              {historyOpen ? '◀ Hide History' : '▶ History'}
            </button>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => window.location.reload()}
            >
              ↻ Refresh
            </button>
          </div>
        </header>

        {/* ── Workspace ─────────────────────────── */}
        <div className="workspace">
          {/* Left: Schema + History */}
          <aside className="panel" style={{ display: historyOpen ? undefined : 'none' }}>
            <div className="panel-header">
              <div className="panel-title">
                <div className="panel-icon schema">🗄️</div>
                <div>
                  <h2>Database Schema</h2>
                  <p className="panel-subtitle">Tables inferred from Excel data</p>
                </div>
              </div>
            </div>
            <div className="panel-body">
              <SchemaViewer schema={schema} />
            </div>

            {history.length > 0 && (
              <>
                <div className="panel-header" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <div className="panel-title">
                    <div className="panel-icon sql">📜</div>
                    <div>
                      <h2>Query History</h2>
                      <p className="panel-subtitle">{history.length} queries this session</p>
                    </div>
                  </div>
                </div>
                <div className="panel-body" style={{ maxHeight: '280px' }}>
                  <QueryHistory entries={history} onSelect={handleHistorySelect} />
                </div>
              </>
            )}
          </aside>

          {/* Right: SQL Output */}
          <main className="panel sql-panel">
            <div className="panel-header">
              <div className="panel-title">
                <div className="panel-icon sql">⚡</div>
                <div>
                  <h2>Generated SQL</h2>
                  <p className="panel-subtitle">AI-generated query for your analytics workflow</p>
                </div>
              </div>
            </div>
            <div className="panel-body">
              <SqlOutput
                sql={sql}
                aiMode={aiMode}
                onCopy={copyToClipboard}
                onExecute={handleExecute}
                loading={executing}
                result={result}
              />
            </div>
          </main>
        </div>

        {/* ── Prompt Bar (sticky bottom) ─────────── */}
        <PromptBar
          prompt={prompt}
          setPrompt={setPrompt}
          onSend={handleGenerate}
          loading={loading}
          error={error}
        />
      </div>
    </>
  )
}

export default App
