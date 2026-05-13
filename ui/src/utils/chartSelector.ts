/**
 * Chart Selection Logic
 * Intelligently determines the best visualization type based on query results
 */

export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'area' | 'table'

interface ColumnInfo {
  name: string
  type: 'numeric' | 'categorical' | 'date' | 'text'
  uniqueValues: number
}

/**
 * Analyze column type based on sample values
 */
function getColumnType(values: unknown[]): ColumnInfo['type'] {
  const sampleSize = Math.min(10, values.length)
  const samples = values.slice(0, sampleSize)

  // Check if numeric
  const numericCount = samples.filter(v => {
    if (typeof v === 'number') return true
    if (typeof v === 'string') {
      const num = parseFloat(v)
      return !isNaN(num)
    }
    return false
  }).length

  if (numericCount === sampleSize) return 'numeric'

  // Check if date
  const dateCount = samples.filter(v => {
    if (!v) return false
    const dateTest = new Date(String(v))
    return !isNaN(dateTest.getTime())
  }).length

  if (dateCount > sampleSize * 0.7) return 'date'

  // Check if categorical (low unique values)
  const uniqueSet = new Set(samples.map(String))
  if (uniqueSet.size <= 20) return 'categorical'

  return 'text'
}

/**
 * Analyze all columns
 */
function analyzeColumns(
  columns: string[],
  rows: Record<string, unknown>[]
): ColumnInfo[] {
  if (!rows || rows.length === 0) return []

  return columns.map(col => {
    const values = rows.map(r => r[col])
    const uniqueValues = new Set(values.map(String)).size

    return {
      name: col,
      type: getColumnType(values),
      uniqueValues,
    }
  })
}

/**
 * Main chart selection function
 */
export function selectChartType(
  columns: string[],
  rows: Record<string, unknown>[]
): ChartType {
  if (!rows || rows.length === 0) return 'table'

  // Too many rows for meaningful visualization
  if (rows.length > 500) return 'table'

  const columnInfo = analyzeColumns(columns, rows)

  // Single column - not suitable for charts
  if (columnInfo.length === 1) return 'table'

  // Find numeric and categorical columns
  const numericCols = columnInfo.filter(c => c.type === 'numeric')
  const categoricalCols = columnInfo.filter(c => c.type === 'categorical')
  const dateCols = columnInfo.filter(c => c.type === 'date')

  // Time series detection
  if (dateCols.length > 0 && numericCols.length > 0) {
    return 'line'
  }

  // Multiple numeric columns - scatter or area
  if (numericCols.length >= 2) {
    return rows.length > 100 ? 'scatter' : 'area'
  }

  // Single numeric, single categorical - bar chart
  if (numericCols.length === 1 && categoricalCols.length >= 1) {
    const uniqueCategories = categoricalCols[0].uniqueValues
    // Pie chart if percentages or small number of categories
    if (uniqueCategories <= 5 && isLikelyPercentage(numericCols[0].name)) {
      return 'pie'
    }
    return 'bar'
  }

  // Multiple categorical columns
  if (categoricalCols.length >= 2) {
    return 'bar'
  }

  // Default to table
  return 'table'
}

/**
 * Check if a column name suggests percentages or proportions
 */
function isLikelyPercentage(columnName: string): boolean {
  const lowerName = columnName.toLowerCase()
  return (
    lowerName.includes('percent') ||
    lowerName.includes('ratio') ||
    lowerName.includes('share') ||
    lowerName.includes('proportion')
  )
}

/**
 * Extract numeric and categorical columns for charting
 */
export function extractChartData(
  columns: string[],
  rows: Record<string, unknown>[]
): {
  numericCols: string[]
  categoricalCols: string[]
  dateCols: string[]
} {
  const columnInfo = analyzeColumns(columns, rows)

  return {
    numericCols: columnInfo.filter(c => c.type === 'numeric').map(c => c.name),
    categoricalCols: columnInfo.filter(c => c.type === 'categorical').map(c => c.name),
    dateCols: columnInfo.filter(c => c.type === 'date').map(c => c.name),
  }
}

/**
 * Format data for Recharts
 */
export function formatDataForChart(
  rows: Record<string, unknown>[],
  xAxis: string,
  yAxis: string
): Record<string, unknown>[] {
  return rows.map(row => ({
    name: String(row[xAxis]),
    value: parseFloat(String(row[yAxis])) || 0,
    ...row,
  }))
}
