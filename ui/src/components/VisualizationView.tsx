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
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { buildVisualizationPlan, formatChartData } from '../utils/chartSelector'

type VisualizationViewProps = {
  columns: string[]
  rows: Record<string, unknown>[]
  loading?: boolean
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#06b6d4', '#f97316']

function VisualizationView({ columns, rows, loading = false }: VisualizationViewProps) {
  if (loading) {
    return (
      <div className="visualization-empty">
        <div className="empty-icon">...</div>
        <p>Building Visualization...</p>
        <span>Analyzing the result set and preparing the best chart.</span>
      </div>
    )
  }

  const plan = buildVisualizationPlan(columns, rows)
  const chartData = formatChartData(rows, plan)

  const tooltipStyle = {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
  }

  const renderChart = () => {
    switch (plan.chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" name={plan.yAxis} />
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
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#10b981" name={plan.yAxis} />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'pie': {
        const pieData = chartData.slice(0, 8)
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={130}
                labelLine={false}
                dataKey="value"
                nameKey="name"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        )
      }

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis type="number" dataKey="x" name={plan.xAxis} />
              <YAxis type="number" dataKey="y" name={plan.yAxis} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={tooltipStyle} />
              <Legend />
              <Scatter name={`${plan.xAxis} vs ${plan.yAxis}`} data={chartData} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>
        )

      default:
        return (
          <div className="visualization-empty">
            <div className="empty-icon">Chart</div>
            <p>Visualization unavailable</p>
            <span>{plan.reason}</span>
          </div>
        )
    }
  }

  return (
    <div className="visualization-container">
      <div className="visualization-info">
        <span className="info-badge">
          {plan.chartType === 'table' ? 'Table Fallback' : `${plan.chartType.toUpperCase()} Chart`}
        </span>
        <span className="info-text">{plan.reason}</span>
      </div>
      <div className="visualization-content">{renderChart()}</div>
    </div>
  )
}

export default VisualizationView
