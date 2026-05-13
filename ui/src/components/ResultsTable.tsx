import { useEffect, useState } from 'react'

type RequestPhase = 'idle' | 'generating' | 'generated' | 'executing' | 'ready'

type ResultsTableProps = {
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount?: number
  phase: RequestPhase
}

const PAGE_SIZE = 25

function ResultsTable({ columns, rows, rowCount, phase }: ResultsTableProps) {
  const [page, setPage] = useState(0)

  useEffect(() => {
    setPage(0)
  }, [rows, columns])

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const displayCount = rowCount ?? rows.length

  if (phase === 'executing') {
    return (
      <div className="visualization-empty">
        <div className="empty-icon">...</div>
        <p>Executing Query...</p>
        <span>The table view will appear as soon as rows are returned.</span>
      </div>
    )
  }

  if (rows.length === 0) {
    return (
      <div className="visualization-empty">
        <div className="empty-icon">Table</div>
        <p>No table data available yet</p>
        <span>
          {phase === 'generated'
            ? 'Run the generated SQL to populate this tab.'
            : 'This query returned no rows.'}
        </span>
      </div>
    )
  }

  return (
    <div className="table-view-container">
      <div className="table-wrapper">
        <table className="result-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>
                  <span className="column-header">{col}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, idx) => (
              <tr key={`${page}-${idx}`} className={idx % 2 === 0 ? 'even' : 'odd'}>
                {columns.map((col) => (
                  <td key={`${idx}-${col}`} title={String(row[col] ?? '')}>
                    <span className="cell-value">{String(row[col] ?? '')}</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            Prev
          </button>
          <span className="pagination-info">
            Page {page + 1} of {totalPages} - {displayCount} total rows
          </span>
          <button
            className="btn btn-ghost btn-sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

export default ResultsTable
