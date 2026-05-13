import { useState } from 'react'

type SchemaViewerProps = {
  schema: Record<string, Record<string, string>>
}

function getTypeClass(dtype: string): string {
  if (/int/i.test(dtype)) return 'type-Integer'
  if (/float|real|numeric|decimal/i.test(dtype)) return 'type-Float'
  if (/bool/i.test(dtype)) return 'type-Boolean'
  if (/date|time/i.test(dtype)) return 'type-DateTime'
  return 'type-String'
}

function SchemaViewer({ schema }: SchemaViewerProps) {
  const [search, setSearch] = useState('')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  const tables = Object.entries(schema)
  const filtered = search.trim()
    ? tables.filter(
        ([name, cols]) =>
          name.toLowerCase().includes(search.toLowerCase()) ||
          Object.keys(cols).some((c) => c.toLowerCase().includes(search.toLowerCase()))
      )
    : tables

  if (!tables.length) {
    return (
      <div className="schema-empty">
        <span className="schema-empty-icon">🗄️</span>
        <p>No schema loaded.</p>
        <p style={{ fontSize: '0.78rem' }}>
          Add an Excel file to the <code>data/</code> folder and restart the backend.
        </p>
      </div>
    )
  }

  const toggleCollapse = (table: string) => {
    setCollapsed((prev) => ({ ...prev, [table]: !prev[table] }))
  }

  return (
    <>
      {tables.length > 2 && (
        <div style={{ padding: '0 0 12px' }}>
          <input
            type="text"
            className="prompt-textarea"
            style={{
              width: '100%',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '8px 14px',
              fontSize: '0.82rem',
            }}
            placeholder="Search tables or columns..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}
      {filtered.map(([table, columns]) => {
        const isCollapsed = collapsed[table] ?? false
        const colEntries = Object.entries(columns)
        return (
          <div key={table} className="schema-table">
            <div className="schema-table-header" onClick={() => toggleCollapse(table)}>
              <span className="schema-table-name">
                {isCollapsed ? '▸' : '▾'} {table}
              </span>
              <span className="schema-row-count">{colEntries.length} cols</span>
            </div>
            {!isCollapsed && (
              <div className="schema-columns">
                {colEntries.map(([name, dtype]) => (
                  <div key={name} className="schema-col">
                    <span className="schema-col-name">{name}</span>
                    <span className={`schema-col-type ${getTypeClass(dtype)}`}>{dtype}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </>
  )
}

export default SchemaViewer
