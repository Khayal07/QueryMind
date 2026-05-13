import os
from pathlib import Path

import pandas as pd

from core.excel_loader import find_excel_file, load_sheets
from core.schema_builder import (
    initialize_database_from_excel,
    get_schema_description,
    infer_column_type,
)
from utils.helpers import sanitize_name


class TestInferColumnType:
    """Tests for the infer_column_type() function."""

    def test_integer_column(self):
        series = pd.Series([1, 2, 3], dtype="int64")
        result = infer_column_type(series)
        assert result.__name__ == "Integer"

    def test_float_column(self):
        series = pd.Series([1.5, 2.5, 3.5], dtype="float64")
        result = infer_column_type(series)
        assert result.__name__ == "Float"

    def test_string_column(self):
        series = pd.Series(["a", "b", "c"], dtype="object")
        result = infer_column_type(series)
        assert result.__name__ == "String"

    def test_boolean_column(self):
        series = pd.Series([True, False, True], dtype="bool")
        result = infer_column_type(series)
        assert result.__name__ == "Boolean"


class TestSanitizeName:
    """Tests for the sanitize_name() helper."""

    def test_basic_name(self):
        assert sanitize_name("Customer Name") == "customer_name"

    def test_special_characters(self):
        assert sanitize_name("price ($)") == "price"

    def test_leading_digits(self):
        assert sanitize_name("123abc") == "col_123abc"

    def test_empty_string(self):
        assert sanitize_name("") == "unnamed"

    def test_multiple_spaces(self):
        assert sanitize_name("  hello   world  ") == "hello_world"


class TestSchemaBuilder:
    """Tests for the full schema build workflow."""

    def test_find_excel_file(self):
        excel_path = find_excel_file()
        assert excel_path is None or excel_path.exists()

    def test_load_sheets(self):
        excel_path = find_excel_file()
        if excel_path is None:
            return
        sheets = load_sheets(excel_path)
        assert isinstance(sheets, dict)
        assert len(sheets) > 0

    def test_initialize_database_from_excel(self):
        excel_path = find_excel_file()
        if excel_path is None:
            return
        schema = initialize_database_from_excel(excel_path)
        assert isinstance(schema, dict)
        assert len(schema) > 0
        reflected = get_schema_description()
        assert reflected == schema

    def test_schema_description_returns_correct_structure(self):
        """Schema description should be a dict of dicts with string values."""
        excel_path = find_excel_file()
        if excel_path is None:
            return
        initialize_database_from_excel(excel_path)
        schema = get_schema_description()
        for table_name, columns in schema.items():
            assert isinstance(table_name, str)
            assert isinstance(columns, dict)
            for col_name, col_type in columns.items():
                assert isinstance(col_name, str)
                assert isinstance(col_type, str)
