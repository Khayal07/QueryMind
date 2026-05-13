# Technical Documentation

## System Overview

The AI SQL Query Generator is a full-stack web application that converts natural language questions into executable SQL queries. It uses a **FastAPI** backend with an **SQLite** database and a **React + Vite** frontend with a premium dark-mode dashboard.

---

## Backend Architecture

### Application Entry Point — `app.py`

The FastAPI application is configured in `app.py` with:

- **Lifespan management**: Excel data is loaded and the SQLite schema is built during startup via an `asynccontextmanager`.
- **CORS middleware**: Allows requests from the Vite dev server (`localhost:5173`) and common local origins.
- **Static file serving**: If `ui/dist/` exists, the production React build is served at `/`.
- **OpenAPI docs**: Auto-generated at `/docs` (Swagger) and `/redoc` (ReDoc).

### Configuration — `config/settings.py`

All application settings are centralized using **Pydantic BaseSettings**:

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENAI_API_KEY` | `""` | OpenAI API key for AI-powered SQL generation |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use for chat completions |
| `DATABASE_URL` | `sqlite:///database/generated.db` | SQLAlchemy database URL |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | Server bind address |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DATA_DIR` | `data/` | Directory to scan for Excel files |

Settings are loaded from environment variables first, then from `.env` file.

### Core Modules

#### `core/excel_loader.py`
- **`find_excel_files()`**: Discovers all `.xlsx` files in `data/`, skipping temporary lock files (`~$`).
- **`load_sheets(path)`**: Reads every sheet into a `dict[str, pd.DataFrame]`, filling NaN values with empty strings.

#### `core/schema_builder.py`
- **`infer_column_type(series)`**: Maps pandas dtypes to SQLAlchemy types (`String`, `Integer`, `Float`, `Boolean`, `DateTime`, `Text`).
- **`initialize_database_from_excel(path)`**: Creates/replaces SQLite tables from Excel sheets. Sanitizes table and column names.
- **`get_schema_description()`**: Reflects the database and returns `{table: {col: type}}`.
- **`get_tables_metadata()`**: Returns enriched metadata including row counts and sample rows.

#### `core/model_loader.py`
Two generation modes:
1. **OpenAI mode**: Sends a schema-aware system prompt + user question to the OpenAI Chat Completions API. Strips markdown fences from responses.
2. **Smart fallback**: A keyword-based SQL generator that handles `SELECT`, `COUNT`, `DISTINCT`, `WHERE`, `ORDER BY`, `GROUP BY`, and aggregate patterns without any API key.

#### `core/sql_generator.py`
Orchestration layer that:
1. Retrieves the current schema description
2. Calls `generate_sql()` from `model_loader`
3. Returns `(sql_string, mode)` tuple

#### `core/query_executor.py`
- Executes SQL against SQLite using SQLAlchemy `text()`.
- Returns structured results: `{success, columns, rows, row_count}` or `{success: false, error}`.

### API Layer

#### `api/schemas.py`
Pydantic models provide:
- **Request validation** with `min_length`/`max_length` constraints
- **Auto-generated OpenAPI documentation** with field descriptions and examples
- **Type safety** across all endpoints

#### `api/routes.py`
See [API Reference](./API_REFERENCE.md) for full endpoint documentation.

### Database Layer — `database/db_manager.py`
- Creates a SQLAlchemy engine from `config.settings.DATABASE_URL`
- Ensures the `database/` directory exists before connecting
- Provides a module-level `engine` singleton used across the application

### Utilities

#### `utils/logger.py`
- Dual output: console (StreamHandler) + file (`logs/app.log`)
- **Rotating file handler**: 5 MB per file, 3 backup files
- Configurable log level via `LOG_LEVEL` setting

#### `utils/helpers.py`
- **`load_environment()`**: Backward-compatible env loader delegating to `config.settings`
- **`sanitize_name(name)`**: Cleans strings for SQL identifiers (lowercase, underscores, strip special chars)

---

## Frontend Architecture

### Technology Stack
- **React 18** with TypeScript
- **Vite 6** for build and dev server
- **Prism.js** for SQL syntax highlighting
- **Axios** for HTTP requests

### Component Hierarchy

```
App.tsx
├── Toast.tsx              (Notification toasts)
├── SchemaViewer.tsx        (Database schema explorer)
├── QueryHistory.tsx        (Session query log)
├── SqlOutput.tsx           (SQL display + execution)
│   └── ResultsTable.tsx    (Query results with pagination)
└── PromptBar.tsx           (Natural language input)
```

### Design System (`styles.css`)
- **CSS Custom Properties** for consistent theming
- **Glassmorphism** panels with animated borders
- **Gradient glow effects** on interactive elements
- **Micro-animations**: pulsing AI badge, shimmer loading skeletons, toast slide-ins
- **Custom scrollbar** styling for dark mode
- **Responsive breakpoints** at 1024px and 640px

### Key Features
- **Syntax highlighting**: Prism.js with custom SQL token colors
- **Query history**: Session-based sidebar with click-to-restore
- **Toast notifications**: Auto-dismissing success/error/info alerts
- **Keyboard shortcut**: `Ctrl+Enter` to generate SQL
- **Auto-resize textarea**: Grows with content, max 120px
- **Pagination**: Large result sets paginated at 25 rows per page

---

## Testing

Tests are located in `tests/` and use **pytest** with shared fixtures in `conftest.py`.

| Test file | Scope |
|-----------|-------|
| `test_schema_builder.py` | Type inference, name sanitization, schema build workflow |
| `test_excel_loader.py` | Sheet loading, NaN handling, multi-sheet files |
| `test_api.py` | All 5 API endpoints via FastAPI TestClient |

Run tests:
```bash
python -m pytest tests/ -v
```

---

## Deployment

### Development
```bash
# Backend
python app.py          # http://localhost:8000

# Frontend
cd ui && npm run dev   # http://localhost:5173
```

### Production
```bash
cd ui && npm run build   # Creates ui/dist/
python app.py            # Serves both API and UI
```
