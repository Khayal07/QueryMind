# Algorithmic Flow

This document describes the end-to-end data and control flow of the AI SQL Query Generator, from Excel ingestion through SQL generation and execution.

---

## High-Level Flow

```mermaid
flowchart TD
    A["📂 Excel File<br/>(data/*.xlsx)"] --> B["📖 Excel Loader<br/>(core/excel_loader.py)"]
    B --> C["🔍 Schema Builder<br/>(core/schema_builder.py)"]
    C --> D["💾 SQLite Database<br/>(database/generated.db)"]

    E["👤 User<br/>Natural Language Query"] --> F["⚛️ React Frontend<br/>(ui/src/App.tsx)"]
    F -->|POST /api/generate| G["🌐 FastAPI Router<br/>(api/routes.py)"]
    G --> H["🧠 SQL Generator<br/>(core/sql_generator.py)"]
    H --> I{"🔑 API Key<br/>Available?"}
    I -->|Yes| J["🤖 OpenAI API<br/>(gpt-4o-mini)"]
    I -->|No| K["⚡ Smart Fallback<br/>(keyword matching)"]
    J --> L["📝 Generated SQL"]
    K --> L
    L --> F

    F -->|POST /api/execute| M["▶️ Query Executor<br/>(core/query_executor.py)"]
    M --> D
    D --> N["📊 Query Results"]
    N --> F
```

---

## Detailed Step-by-Step Flow

### Phase 1: Startup & Data Ingestion

```mermaid
sequenceDiagram
    participant App as app.py
    participant EL as ExcelLoader
    participant SB as SchemaBuilder
    participant DB as SQLite

    App->>EL: find_excel_files()
    EL-->>App: [data/sales.xlsx, ...]
    App->>EL: load_sheets(excel_path)
    EL-->>App: {"Sheet1": DataFrame, ...}
    App->>SB: initialize_database_from_excel()
    loop For each sheet
        SB->>SB: sanitize_name(sheet_name)
        SB->>SB: infer_column_type(series)
        SB->>DB: CREATE TABLE (via SQLAlchemy)
        SB->>DB: INSERT rows (pandas to_sql)
    end
    SB-->>App: schema_description
    App->>App: Log AI mode & start server
```

1. **`app.py`** lifespan handler calls `load_excel_data()` to find the primary Excel file.
2. **`excel_loader.py`** scans `data/` for `.xlsx` files, loads all sheets into DataFrames.
3. **`schema_builder.py`** iterates each sheet:
   - Sanitizes table/column names (lowercase, underscores, no special chars).
   - Infers SQLAlchemy column types from pandas dtypes.
   - Creates/replaces SQLite tables and bulk-inserts rows.
4. The schema is built and ready for queries.

### Phase 2: Schema Display

```mermaid
sequenceDiagram
    participant UI as React App
    participant API as FastAPI
    participant SB as SchemaBuilder
    participant DB as SQLite

    UI->>API: GET /api/schema
    API->>SB: get_schema_description()
    SB->>DB: REFLECT metadata
    DB-->>SB: table/column info
    SB-->>API: {table: {col: type}}
    API-->>UI: JSON response
    UI->>UI: Render SchemaViewer
```

### Phase 3: SQL Generation

```mermaid
sequenceDiagram
    participant UI as React App
    participant API as FastAPI
    participant SG as SQLGenerator
    participant ML as ModelLoader
    participant OAI as OpenAI API

    UI->>API: POST /api/generate {prompt}
    API->>SG: create_sql_from_nl(prompt)
    SG->>SG: get_schema_description()
    SG->>ML: generate_sql(prompt, schema)

    alt API Key Available
        ML->>OAI: Chat completion request
        OAI-->>ML: SQL response
        ML->>ML: Strip markdown fences
    else No API Key
        ML->>ML: smart_fallback(prompt, tables)
        Note right of ML: Keyword matching:<br/>SELECT, COUNT, WHERE,<br/>ORDER BY, GROUP BY
    end

    ML-->>SG: (sql, mode)
    SG-->>API: (sql, mode)
    API-->>UI: {sql, ai_mode}
    UI->>UI: Prism.js highlight
    UI->>UI: Add to history
```

### Phase 4: Query Execution

```mermaid
sequenceDiagram
    participant UI as React App
    participant API as FastAPI
    participant QE as QueryExecutor
    participant DB as SQLite

    UI->>API: POST /api/execute {sql}
    API->>QE: execute_query(sql)
    QE->>DB: Execute via SQLAlchemy text()
    alt Success
        DB-->>QE: ResultProxy
        QE-->>API: {success, columns, rows, row_count}
        API-->>UI: 200 JSON response
        UI->>UI: Render ResultsTable
    else SQL Error
        DB-->>QE: SQLAlchemyError
        QE-->>API: {success: false, error}
        API-->>UI: 400 error
        UI->>UI: Show error toast
    end
```

---

## Smart Fallback Algorithm

When no OpenAI API key is configured, the system uses a keyword-based SQL generator:

```mermaid
flowchart TD
    A["User Prompt"] --> B{"Contains<br/>count/how many?"}
    B -->|Yes| C["SELECT COUNT(*)<br/>FROM table"]
    B -->|No| D{"Contains<br/>distinct/unique?"}
    D -->|Yes| E["SELECT DISTINCT col<br/>FROM table"]
    D -->|No| F{"Contains<br/>aggregation?"}
    F -->|Yes| G["SELECT col, AGG(col)<br/>FROM table GROUP BY"]
    F -->|No| H["SELECT *<br/>FROM table"]
    C --> I{"Has filter<br/>keywords?"}
    E --> I
    G --> I
    H --> I
    I -->|Yes| J["+ WHERE clause"]
    I -->|No| K{"Has sort<br/>keywords?"}
    J --> K
    K -->|Yes| L["+ ORDER BY clause"]
    K -->|No| M["+ LIMIT 50"]
    L --> M
    M --> N["Return SQL"]
```

The fallback detects these patterns:
- **COUNT**: "how many", "count", "total number"
- **DISTINCT**: "unique", "distinct", "different"
- **Aggregates**: "average", "sum", "maximum", "minimum"
- **Filters**: "where", "greater than", "less than", "equals"
- **Sorting**: "order by", "sort by", "highest", "lowest"
- **Grouping**: "group by", "per", "each", "by category"
