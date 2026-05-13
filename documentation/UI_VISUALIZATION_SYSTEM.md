# Enhanced UI: Results Visualization System

## Overview

This document describes the professional result visualization system added to the QueryMind frontend. The system enables users to view SQL query results in multiple formats: traditional table view and interactive charts/visualizations.

---

## Architecture

### Component Structure

```
ui/src/
├── components/
│   ├── SqlOutput.tsx              # Main SQL output container
│   ├── ResultsTabView.tsx         # ✨ NEW: Tab switcher for results
│   ├── ResultsTable.tsx           # Table view for query results
│   ├── VisualizationView.tsx      # ✨ NEW: Chart visualization component
│   ├── PromptBar.tsx              # Natural language input
│   ├── SchemaViewer.tsx           # Database schema display
│   ├── QueryHistory.tsx           # Query history
│   ├── Toast.tsx                  # Notification system
│   └── ... (other components)
├── utils/
│   └── chartSelector.ts           # ✨ NEW: Intelligent chart type selection
└── styles.css                      # Unified styling with new visualization styles
```

---

## Key Components

### 1. ResultsTabView.tsx

**Purpose:** Container component that manages tab switching between Table and Visualization views.

**Features:**
- Tab navigation UI with visual feedback
- Displays row count and data metadata
- Responsive layout for mobile devices
- Smooth transitions between tabs

**Props:**
```typescript
interface ResultsTabViewProps {
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount?: number
  visualizing?: boolean
}
```

**State:**
- `activeTab`: 'table' | 'visualization' - tracks selected view

---

### 2. VisualizationView.tsx

**Purpose:** Intelligent chart component that automatically selects and renders the most appropriate chart type for given data.

**Supported Chart Types:**
- **Bar Chart**: Categorical + Numeric columns (e.g., sales by region)
- **Line Chart**: Time-series + Numeric data (e.g., stock prices over time)
- **Area Chart**: Multiple numeric columns (e.g., cumulative metrics)
- **Pie Chart**: Percentages or proportions with ≤5 categories
- **Scatter Plot**: Multiple numeric columns with 100+ rows
- **Table**: Fallback for complex or unsuitable data

**Features:**
- Dark theme compatible
- Responsive sizing
- Interactive tooltips
- Legend display
- Smooth animations

**Libraries Used:**
- Recharts v2.10.0 - Professional React charting library

---

### 3. chartSelector.ts (Utility)

**Purpose:** Core logic for intelligent chart type selection based on data analysis.

**Key Functions:**

#### `selectChartType(columns: string[], rows: Record<string, unknown>[]): ChartType`

Analyzes data and returns the best chart type:

1. **Row Count Check**: Returns 'table' if >500 rows
2. **Column Analysis**: Categorizes columns as:
   - `numeric`: Numbers and parseable values
   - `categorical`: Low-unique-value strings
   - `date`: Date/timestamp values
   - `text`: High-cardinality text

3. **Pattern Matching**:
   - Time series (date + numeric) → `line`
   - Multiple numeric → `scatter` or `area`
   - Single numeric + categorical → `bar` or `pie`
   - Multiple categorical → `bar`

#### `extractChartData(columns, rows): { numericCols, categoricalCols, dateCols }`

Extracts typed column information for rendering.

#### `formatDataForChart(rows, xAxis, yAxis): Record<string, unknown>[]`

Formats data for Recharts library consumption.

---

## UI Enhancements

### SQL Output Panel Layout

```
┌─ SQL Output Panel ────────────────────────┐
│ ┌─ SQL Code Editor ─────────────────────┐ │
│ │ SELECT * FROM customers LIMIT 50     │ │
│ │                                       │ │
│ │ 🤖 OpenAI | 📋 Copy                   │ │
│ └───────────────────────────────────────┘ │
│ [ ▶ Execute ] [ 📋 Copy SQL ]            │
│                                           │
│ ┌─ Results Tab View ──────────────────────┤
│ │ [📋 Table View] [📊 Visualization]      │
│ │ 50 rows · 12 columns                    │
│ ├─────────────────────────────────────────┤
│ │ ┌─ Table / Chart Renders Here ────────┐ │
│ │ │                                       │ │
│ │ │ Paginated table or interactive chart │ │
│ │ │                                       │ │
│ │ └───────────────────────────────────────┘ │
│ └───────────────────────────────────────────┘
└───────────────────────────────────────────────┘
```

### Loading States

**Generating SQL:**
```
⚡ Generating SQL...
```

**Executing Query:**
```
⏳ Executing Query...
Retrieving results from database
```

**Building Visualization:**
```
[Smooth fade-in of chart]
```

### Styling Features

- **Dark Mode**: All components follow dark theme design
- **Responsive**: Adapts to mobile, tablet, desktop
- **Smooth Transitions**: Fade animations between tabs
- **Visual Feedback**: Active tab highlighting, hover states
- **Accessibility**: Clear labels and keyboard support

---

## Query Execution Flow

```
User Input
    ↓
[QueryMind interface]
    ↓
App.tsx: handleGenerate()
    ↓
API: /api/generate (NL → SQL)
    ↓
SQL Generated
    ↓
SqlOutput Component: onExecute()
    ↓
API: /api/execute (SQL → Results)
    ↓
Results Received
    ↓
ResultsTabView: Displays Results
    ├── Table Tab: ResultsTable component
    │   ├── Paginated table grid
    │   ├── Column headers (sticky)
    │   └── Pagination controls
    │
    └── Visualization Tab: VisualizationView component
        ├── chartSelector.selectChartType()
        ├── Intelligent chart selection
        ├── formatDataForChart()
        └── Recharts rendering
```

---

## Data Analysis Algorithm

### Column Type Detection

```typescript
Sample Values (up to 10)
    ↓
    ├─ Check if numeric (80%+ match) → 'numeric'
    ├─ Check if date (70%+ match) → 'date'
    ├─ Check if low unique values (≤20) → 'categorical'
    └─ Default → 'text'
```

### Chart Selection Logic

```
Input: Columns array, Rows array
    ↓
    ├─ If rows < 10 → suggest 'table'
    ├─ If rows > 500 → force 'table'
    │
    ├─ Count numeric, categorical, date columns
    │
    ├─ If time-series detected (date + numeric) → 'line'
    ├─ If multiple numeric (≥2) → 'scatter' or 'area'
    ├─ If numeric + categorical → 'bar' or 'pie'
    ├─ If multiple categorical → 'bar'
    │
    └─ Default → 'table'
```

### Special Case Handling

1. **Empty Results**: Shows placeholder message
2. **Single Column**: Always uses table
3. **Percentage Detection**: Detects column names containing "percent", "ratio", "share" → pie chart
4. **Large Datasets**: >500 rows → table only
5. **Non-numeric Data**: Categorizes and groups appropriately

---

## CSS Styling System

### Design Variables

```css
/* Charts use these colors */
--accent-blue:    #5d7cff    /* Primary */
--accent-cyan:    #2cc1ff    /* Secondary */
--accent-green:   #27fe97    /* Success */
--accent-amber:   #fbbf24    /* Warning */
--accent-purple:  #a855f7    /* Accent */
--accent-red:     #ff6b82    /* Error */

/* Backgrounds */
--bg-card:        rgba(16, 23, 53, 0.88)
--bg-secondary:   var(--bg-elevated)

/* Borders */
--border-subtle:  rgba(255, 255, 255, 0.06)
--border-accent:  rgba(99, 135, 255, 0.16)
```

### New CSS Classes

- `.results-tab-view` - Tab container
- `.results-header` - Tab controls area
- `.tab-btn`, `.tab-btn.active` - Tab buttons
- `.table-view-container` - Table wrapper
- `.visualization-container` - Chart wrapper
- `.execution-status` - Loading status display
- Responsive utilities for mobile

---

## Error Handling

### Visualization Edge Cases

| Condition | Handling |
|-----------|----------|
| No data | Show "No data to visualize" message |
| Single row | Show table, suppress chart |
| All non-numeric | Use bar chart with categorical grouping |
| Mixed data types | Try to separate numeric and categorical |
| Very large numbers | Recharts handles auto-scaling |
| Invalid chart selection | Fall back to table |

---

## Performance Considerations

1. **Data Sampling**: Charts limit to first 500 rows max
2. **Column Analysis**: Only examines first 10 values per column
3. **Lazy Rendering**: Charts only render when tab is active
4. **Memoization**: Component props prevent unnecessary re-renders

---

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (15+)
- Mobile browsers: Responsive design adapts UI

---

## Future Enhancements

Potential improvements for v2:

1. **Additional Chart Types**:
   - Bubble charts
   - Heatmaps
   - Gantt charts
   - Waterfall charts

2. **Advanced Features**:
   - Custom chart configuration UI
   - Data aggregation (groupBy, sum, average)
   - Export as PNG/SVG
   - Chart sharing via URL

3. **Performance**:
   - Virtual scrolling for large tables
   - Web workers for data analysis
   - Query result caching

4. **Analytics**:
   - Summary statistics
   - Data quality metrics
   - Column correlation heatmaps

---

## Development Guide

### Adding a New Chart Type

1. Add type to `ChartType` in `chartSelector.ts`
2. Add detection logic to `selectChartType()`
3. Add rendering case to `VisualizationView.tsx`
4. Add CSS styles to `styles.css`
5. Test with sample data

### Example: Adding Bubble Chart

```typescript
// 1. Update type
export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'area' | 'bubble' | 'table'

// 2. Add detection
if (numericCols.length === 3) return 'bubble'

// 3. Add rendering
case 'bubble':
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BubbleChart data={chartData}>
        {/* ... */}
      </BubbleChart>
    </ResponsiveContainer>
  )
```

---

## Troubleshooting

### Charts Not Showing

1. Verify data has numeric columns
2. Check browser console for errors
3. Ensure Recharts is installed: `npm list recharts`
4. Verify CSS is loaded

### Table Not Pagination

1. Check if rows > 25 (PAGE_SIZE)
2. Verify `rowCount` prop passed correctly
3. Check browser console for JS errors

### Styling Issues

1. Clear browser cache
2. Run `npm run build` for production
3. Check CSS custom properties in `:root`

---

## Files Modified/Created

### New Files
- `ui/src/components/ResultsTabView.tsx` - Tab view component
- `ui/src/components/VisualizationView.tsx` - Chart visualization
- `ui/src/utils/chartSelector.ts` - Chart selection logic

### Modified Files
- `ui/src/components/SqlOutput.tsx` - Integrated ResultsTabView
- `ui/src/components/ResultsTable.tsx` - Enhanced styling
- `ui/src/styles.css` - Added 300+ lines of new styles
- `ui/package.json` - Added Recharts dependency

### Dependencies Added
- `recharts@^2.10.0` - React charting library

---

## Testing Checklist

- [ ] Table view displays results correctly
- [ ] Pagination works with >25 rows
- [ ] Visualization tab renders appropriate chart type
- [ ] Charts are interactive (hover tooltips work)
- [ ] Dark theme is properly applied
- [ ] Mobile responsive (test at 480px, 768px, 1024px)
- [ ] Loading states display correctly
- [ ] Error states handled gracefully
- [ ] No console errors

---

**Last Updated:** 2026-05-13  
**Version:** 2.0.0  
**Author:** GitHub Copilot - AI SQL Query Generator Team
