# Setup & Running Instructions

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Git (optional)

## Backend Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Edit `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./database/generated.db
```

> **Note**: If you don't have an OpenAI API key, the system will fall back to a basic SQL generator.

### 5. Start Backend Server

```bash
python app.py
```

The backend will:
- Load the Excel file from `data/` folder
- Create SQLite tables automatically
- Start FastAPI server on `http://0.0.0.0:8000`

**Expected Output:**
```
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
2026-05-12 20:04:09,877 [INFO] app: Loading Excel files and building schema
2026-05-12 20:04:33,037 [INFO] core.schema_builder: Created sqlite table ... with ... columns
INFO:     Application startup complete.
```

---

## Frontend Setup

### 1. Install Dependencies

Navigate to the `ui` folder:

```bash
cd ui
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

### 3. Access Application

Open your browser and go to:
- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://127.0.0.1:8000/api`

---

## Testing the API

### Check Schema

```bash
curl http://127.0.0.1:8000/api/schema
```

**Response Example:**
```json
{
  "schema": {
    "table_name": {
      "column_name": "TEXT",
      "column_id": "INTEGER"
    }
  }
}
```

### Generate SQL from Natural Language

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show all records"}'
```

**Response Example:**
```json
{
  "sql": "SELECT * FROM table_name;"
}
```

### Execute SQL Query

```bash
curl -X POST http://127.0.0.1:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM table_name LIMIT 5;"}'
```

**Response Example:**
```json
{
  "columns": ["column1", "column2"],
  "rows": [
    {"column1": "value1", "column2": "value2"}
  ]
}
```

---

## Production Build

### Build Frontend

```bash
cd ui
npm run build
```

Output will be in `ui/dist/`

### Serve Production

```bash
python app.py
```

The backend will automatically serve the frontend from `ui/dist/` if it exists.

---

## Troubleshooting

### Excel File Not Found
- Ensure your `.xlsx` file is in the `data/` folder or project root
- Check file name doesn't start with `~$` (temporary files)

### Port Already in Use
- Backend: Change port in `app.py` (default 8000)
- Frontend: Vite will suggest alternative port

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is correct in `.env`
- Check your OpenAI account has available credits
- Falls back to basic generator if key is invalid

### Schema Not Reflecting
- Restart the backend server
- Check Excel file format is `.xlsx`
- Ensure columns have proper names

---

## Project Structure

```
projectt/
├── app.py                    # FastAPI entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
│
├── core/                     # Business logic
│   ├── excel_loader.py      # Excel file handling
│   ├── schema_builder.py    # Schema extraction
│   ├── sql_generator.py     # NL to SQL conversion
│   ├── model_loader.py      # OpenAI integration
│   └── query_executor.py    # Query execution
│
├── api/
│   └── routes.py            # API endpoints
│
├── database/
│   ├── db_manager.py        # SQLAlchemy setup
│   └── generated.db         # SQLite database
│
├── ui/                       # React frontend
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── styles.css
│       └── components/
│
├── data/                     # Excel data files
│   └── sample.xlsx
│
└── documentation/            # Technical docs
    ├── PROJECT_ARCHITECTURE.md
    ├── TECHNICAL_DOCUMENTATION.md
    └── ALGORITHMIC_FLOW.md
```

---

## Next Steps

1. Add your Excel file to the `data/` folder
2. Start the backend
3. Start the frontend
4. Open http://localhost:5173 in your browser
5. Type natural language queries to generate SQL
