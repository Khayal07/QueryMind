import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { extractChartData, formatDataForChart, selectChartType } from '../utils/chartSelector'

type VisualizationViewProps = {
  columns: string[]
  rows: Record<string, unknown>[]
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

function VisualizationView({ columns, rows }: VisualizationViewProps) {
  if (!rows || rows.length === 0) {
    return (
      <div className="visualization-empty">
        <div className="empty-icon">📊</div>
        <p>No data to visualize</p>
        <span>Execute a query to see visualizations</span>
      </div>
    )
  }

  const { numericCols, categoricalCols } = extractChartData(columns, rows)
  const chartType = selectChartType(columns, rows)

  // Get primary numeric and categorical columns
  const xAxis = categoricalCols[0] || numericCols[0] || columns[0]
  const yAxis = numericCols[0] || columns[1] || columns[0]

  const chartData = formatDataForChart(rows, xAxis, yAxis)

  const renderChart = () => {
    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" name={yAxis} />
            </BarChart>
          </ResponsiveContainer>
        )

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" name={yAxis} />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorValue)"
                name={yAxis}
              />
            </AreaChart>
          </ResponsiveContainer>
        )

      case 'pie': {
        const pieData = chartData.slice(0, 5).map((item, idx) => ({
          name: String(item.name),
          value: parseFloat(String(item.value)) || 0,
        }))

        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={120}
                fill="#3b82f6"
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )
      }

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
              data={chartData}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis type="number" dataKey="value" name={xAxis} />
              <YAxis type="number" dataKey="value" name={yAxis} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              />
              <Scatter name={yAxis} data={chartData} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>
        )

      default:
        return (
          <div className="visualization-empty">
            <div className="empty-icon">📊</div>
            <p>Chart type not suitable for this data</p>
            <span>Use Table View to see detailed results</span>
          </div>
        )
    }
  }

  return (
    <div className="visualization-container">
      <div className="visualization-info">
        <span className="info-badge">
          {chartType === 'table' ? '📋' : '📊'} {chartType.toUpperCase()}
        </span>
        <span className="info-text">
          {rows.length} rows • {columns.length} columns
        </span>
      </div>
      <div className="visualization-content">{renderChart()}</div>
    </div>
  )
}

export default VisualizationView
