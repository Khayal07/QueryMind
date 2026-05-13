export type HistoryEntry = {
  id: number
  prompt: string
  sql: string
  aiMode: string
  timestamp: Date
}

type QueryHistoryProps = {
  entries: HistoryEntry[]
  onSelect: (entry: HistoryEntry) => void
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function QueryHistory({ entries, onSelect }: QueryHistoryProps) {
  if (entries.length === 0) {
    return (
      <div className="schema-empty">
        <span className="schema-empty-icon">📝</span>
        <p>No queries yet.</p>
        <p style={{ fontSize: '0.78rem' }}>Your query history will appear here.</p>
      </div>
    )
  }

  return (
    <div className="history-list">
      {entries.map((entry) => (
        <div key={entry.id} className="history-item" onClick={() => onSelect(entry)}>
          <div className="history-prompt">{entry.prompt}</div>
          <div className="history-meta">
            <span>{formatTime(entry.timestamp)}</span>
            <span className={`mode-badge mode-${entry.aiMode}`}>
              {entry.aiMode === 'openai' ? '🤖 AI' : '⚡ Fallback'}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default QueryHistory
