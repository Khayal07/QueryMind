# API Reference

Base URL: `http://localhost:8000/api`

Interactive docs: http://localhost:8000/docs (Swagger) · http://localhost:8000/redoc (ReDoc)

---

## `GET /api/health`

**Response** `200 OK`
```json
{ "status": "ok", "version": "1.0.0", "database_ready": true, "ai_mode": "fallback" }
```
`ai_mode` is `"openai"` when a valid API key is set, otherwise `"fallback"`.

---

## `GET /api/schema`

Returns table → column/type mapping for all tables in the database.

**Response** `200 OK`
```json
{
  "schema": {
    "customers": { "customer_name": "String", "age": "Integer", "total_spent": "Float" },
    "orders":    { "order_id": "Integer", "product": "String", "amount": "Float" }
  }
}
```

---

## `GET /api/tables`

Returns enriched metadata with row counts and 3-row samples.

**Response** `200 OK`
```json
{
  "tables": [{
    "name": "customers",
    "columns": [{"name": "customer_name", "type": "String"}],
    "row_count": 150,
    "sample_rows": [{"customer_name": "Alice"}]
  }]
}
```

---

## `POST /api/generate`

Convert a natural language prompt into SQL.

**Request body**
```json
{ "prompt": "Show all customers who spent more than $100" }
```

| Field | Type | Constraints |
|-------|------|-------------|
| `prompt` | string | 1–2000 chars, required |

**Response** `200 OK`
```json
{ "sql": "SELECT * FROM customers WHERE total_spent > 100;", "ai_mode": "openai" }
```

**Errors**: `422` — empty/missing prompt.

---

## `POST /api/execute`

Execute a SQL query and return rows.

**Request body**
```json
{ "sql": "SELECT customer_name, total_spent FROM customers ORDER BY total_spent DESC" }
```

| Field | Type | Constraints |
|-------|------|-------------|
| `sql` | string | 1–5000 chars, required |

**Response** `200 OK`
```json
{
  "columns": ["customer_name", "total_spent"],
  "rows": [{"customer_name": "Alice", "total_spent": 280.0}],
  "row_count": 1
}
```

**Errors**: `400` — SQL execution failed · `422` — missing/empty SQL.

---

## Error Format

| Code | Meaning |
|------|---------|
| `400` | SQL execution error (bad syntax, missing table) |
| `422` | Request validation failed |
| `500` | Internal server error |

```json
{ "detail": "(sqlite3.OperationalError) no such table: foo" }
```
