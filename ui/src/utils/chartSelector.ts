export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'table'

interface ColumnInfo {
  name: string
  type: 'numeric' | 'categorical' | 'date' | 'text'
  uniqueValues: number
}

export type VisualizationPlan = {
  chartType: ChartType
  reason: string
  xAxis?: string
  yAxis?: string
}

function isNumericValue(value: unknown): boolean {
  if (typeof value === 'number') return Number.isFinite(value)
  if (typeof value !== 'string') return false
  const parsed = Number.parseFloat(value)
  return !Number.isNaN(parsed) && Number.isFinite(parsed)
}

function getColumnType(values: unknown[]): ColumnInfo['type'] {
  const samples = values.filter((value) => value !== null && value !== undefined && value !== '').slice(0, 20)
  if (samples.length === 0) return 'text'

  const numericCount = samples.filter(isNumericValue).length
  if (numericCount >= Math.ceil(samples.length * 0.85)) return 'numeric'

  const dateCount = samples.filter((value) => !Number.isNaN(new Date(String(value)).getTime())).length
  if (dateCount >= Math.ceil(samples.length * 0.75)) return 'date'

  const uniqueSet = new Set(samples.map(String))
  if (uniqueSet.size <= 12) return 'categorical'

  return 'text'
}

function analyzeColumns(columns: string[], rows: Record<string, unknown>[]): ColumnInfo[] {
  return columns.map((col) => {
    const values = rows.map((row) => row[col])
    return {
      name: col,
      type: getColumnType(values),
      uniqueValues: new Set(values.map(String)).size,
    }
  })
}

function isLikelyPercentage(columnName: string): boolean {
  const lowerName = columnName.toLowerCase()
  return (
    lowerName.includes('percent') ||
    lowerName.includes('ratio') ||
    lowerName.includes('share') ||
    lowerName.includes('proportion')
  )
}

export function buildVisualizationPlan(
  columns: string[],
  rows: Record<string, unknown>[]
): VisualizationPlan {
  if (!rows.length) {
    return { chartType: 'table', reason: 'No query results available yet.' }
  }

  if (columns.length < 2) {
    return { chartType: 'table', reason: 'At least two columns are needed for a chart.' }
  }

  if (rows.length > 500) {
    return { chartType: 'table', reason: 'Large result sets stay in table view for readability.' }
  }

  const columnInfo = analyzeColumns(columns, rows)
  const numericCols = columnInfo.filter((column) => column.type === 'numeric')
  const categoricalCols = columnInfo.filter((column) => column.type === 'categorical')
  const dateCols = columnInfo.filter((column) => column.type === 'date')

  if (dateCols.length > 0 && numericCols.length > 0) {
    return {
      chartType: 'line',
      reason: 'Date + numeric data is best shown as a trend line.',
      xAxis: dateCols[0].name,
      yAxis: numericCols[0].name,
    }
  }

  if (numericCols.length >= 2) {
    return {
      chartType: 'scatter',
      reason: 'Multiple numeric columns can be compared in a scatter plot.',
      xAxis: numericCols[0].name,
      yAxis: numericCols[1].name,
    }
  }

  if (numericCols.length === 1 && categoricalCols.length > 0) {
    const category = categoricalCols[0]
    return {
      chartType:
        category.uniqueValues <= 6 || isLikelyPercentage(numericCols[0].name) ? 'pie' : 'bar',
      reason: 'Categorical labels with a numeric measure can be summarized visually.',
      xAxis: category.name,
      yAxis: numericCols[0].name,
    }
  }

  return {
    chartType: 'table',
    reason: 'This result is not numeric or categorical enough for a meaningful chart.',
  }
}

export function formatChartData(
  rows: Record<string, unknown>[],
  plan: VisualizationPlan
): Record<string, unknown>[] {
  if (!plan.xAxis || !plan.yAxis) return []

  if (plan.chartType === 'scatter') {
    return rows
      .map((row) => ({
        x: Number.parseFloat(String(row[plan.xAxis!])),
        y: Number.parseFloat(String(row[plan.yAxis!])),
        label: String(row[plan.xAxis!]),
      }))
      .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
  }

  return rows.map((row) => ({
    name: String(row[plan.xAxis!] ?? ''),
    value: Number.parseFloat(String(row[plan.yAxis!] ?? 0)) || 0,
  }))
}
