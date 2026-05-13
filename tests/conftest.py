"""
Shared pytest fixtures for the AI SQL Query Generator test suite.

Provides reusable test data, temporary Excel files, and a FastAPI
TestClient so integration tests don't require a running server.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is on sys.path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """A small DataFrame simulating a typical Excel sheet."""
    return pd.DataFrame({
        "Customer Name": ["Alice", "Bob", "Charlie"],
        "Age": [28, 35, 42],
        "Total Spent": [150.50, 280.00, 90.75],
        "Is VIP": [True, True, False],
    })


@pytest.fixture
def sample_excel(tmp_path: Path, sample_dataframe: pd.DataFrame) -> Path:
    """Create a temporary Excel file with one sheet."""
    excel_path = tmp_path / "test_data.xlsx"
    sample_dataframe.to_excel(excel_path, index=False, sheet_name="Customers")
    return excel_path


@pytest.fixture
def multi_sheet_excel(tmp_path: Path) -> Path:
    """Create a temporary Excel file with two sheets."""
    excel_path = tmp_path / "multi_sheet.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame({
            "Product": ["Widget", "Gadget"],
            "Price": [29.99, 49.99],
        }).to_excel(writer, index=False, sheet_name="Products")

        pd.DataFrame({
            "Order ID": [1, 2, 3],
            "Customer": ["Alice", "Bob", "Alice"],
            "Amount": [59.98, 49.99, 29.99],
        }).to_excel(writer, index=False, sheet_name="Orders")
    return excel_path


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient for integration tests."""
    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)
