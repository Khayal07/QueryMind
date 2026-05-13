"""
Integration tests for the FastAPI API layer.

Uses FastAPI TestClient to test all endpoints without
needing a running server or external dependencies.
"""

import pytest


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_ok(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert "ai_mode" in data

    def test_health_returns_database_ready(self, test_client):
        response = test_client.get("/api/health")
        data = response.json()
        assert data["database_ready"] is True


class TestSchemaEndpoint:
    """Tests for GET /api/schema."""

    def test_schema_returns_dict(self, test_client):
        response = test_client.get("/api/schema")
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert isinstance(data["schema"], dict)


class TestTablesEndpoint:
    """Tests for GET /api/tables."""

    def test_tables_returns_list(self, test_client):
        response = test_client.get("/api/tables")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)


class TestGenerateEndpoint:
    """Tests for POST /api/generate."""

    def test_generate_with_valid_prompt(self, test_client):
        response = test_client.post(
            "/api/generate",
            json={"prompt": "Show all records"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sql" in data
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert "ai_mode" in data

    def test_generate_with_empty_prompt_returns_422(self, test_client):
        response = test_client.post(
            "/api/generate",
            json={"prompt": ""}
        )
        assert response.status_code == 422

    def test_generate_without_body_returns_422(self, test_client):
        response = test_client.post("/api/generate")
        assert response.status_code == 422


class TestExecuteEndpoint:
    """Tests for POST /api/execute."""

    def test_execute_valid_sql(self, test_client):
        """Execute a simple SELECT on sqlite_master (always exists)."""
        response = test_client.post(
            "/api/execute",
            json={"sql": "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data

    def test_execute_invalid_sql_returns_400(self, test_client):
        response = test_client.post(
            "/api/execute",
            json={"sql": "INVALID SQL QUERY HERE !!!"}
        )
        assert response.status_code == 400

    def test_execute_empty_sql_returns_422(self, test_client):
        response = test_client.post(
            "/api/execute",
            json={"sql": ""}
        )
        assert response.status_code == 422
