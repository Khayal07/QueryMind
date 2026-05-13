"""
Unit tests for the Excel loader module.

Tests file discovery, sheet loading, and edge cases.
"""

from pathlib import Path
import pandas as pd

from core.excel_loader import load_sheets


class TestLoadSheets:
    """Tests for the load_sheets() function."""

    def test_loads_single_sheet(self, sample_excel: Path):
        """Single-sheet Excel file returns one DataFrame entry."""
        sheets = load_sheets(sample_excel)
        assert isinstance(sheets, dict)
        assert len(sheets) == 1
        assert "Customers" in sheets
        df = sheets["Customers"]
        assert len(df) == 3
        assert "Customer Name" in df.columns

    def test_loads_multiple_sheets(self, multi_sheet_excel: Path):
        """Multi-sheet Excel file returns all sheets."""
        sheets = load_sheets(multi_sheet_excel)
        assert len(sheets) == 2
        assert "Products" in sheets
        assert "Orders" in sheets
        assert len(sheets["Products"]) == 2
        assert len(sheets["Orders"]) == 3

    def test_fills_na_values(self, tmp_path: Path):
        """Missing values are filled with empty strings."""
        df = pd.DataFrame({"A": [1, None, 3], "B": [None, "x", None]})
        path = tmp_path / "na_test.xlsx"
        df.to_excel(path, index=False, sheet_name="Sheet1")

        sheets = load_sheets(path)
        result = sheets["Sheet1"]
        # No NaN values should remain
        assert result.isna().sum().sum() == 0

    def test_returns_dict_type(self, sample_excel: Path):
        """Return type is a dictionary of string to DataFrame."""
        sheets = load_sheets(sample_excel)
        for key, value in sheets.items():
            assert isinstance(key, str)
            assert isinstance(value, pd.DataFrame)
