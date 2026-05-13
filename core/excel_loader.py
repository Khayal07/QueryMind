"""
Excel file loader for the AI SQL Query Generator.

Discovers ``.xlsx`` files in the ``data/`` directory, reads every
sheet into pandas DataFrames, and normalises missing values so
downstream SQL generation stays stable.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def find_excel_files() -> List[Path]:
    """
    Discover all ``.xlsx`` files in the data directory.

    Skips temporary lock files (prefixed with ``~$``).

    Returns:
        Sorted list of Path objects for every discovered workbook.
    """
    data_dir = settings.DATA_DIR
    if not data_dir.exists():
        logger.warning("Data directory does not exist: %s", data_dir)
        return []

    files = sorted(
        path
        for path in data_dir.glob("*.xlsx")
        if not path.name.startswith("~$")
    )
    logger.info("Found %d Excel file(s) in %s", len(files), data_dir)
    return files


def find_excel_file() -> Optional[Path]:
    """
    Return the first available Excel file (backward-compatible helper).

    Returns:
        Path to the first workbook, or ``None`` if none found.
    """
    files = find_excel_files()
    return files[0] if files else None


def load_excel_data() -> Path:
    """
    Locate the primary Excel file used during startup.

    Raises:
        FileNotFoundError: If no ``.xlsx`` file is found in ``data/``.

    Returns:
        Path to the first available workbook.
    """
    excel_path = find_excel_file()
    if excel_path is None:
        raise FileNotFoundError(
            f"No Excel file found in {settings.DATA_DIR}. "
            "Place at least one .xlsx file in the data/ folder."
        )
    logger.info("Primary Excel file: %s", excel_path.name)
    return excel_path


def load_sheets(excel_path: Path) -> dict[str, pd.DataFrame]:
    """
    Read every sheet from an Excel workbook into DataFrames.

    Missing values are filled with empty strings to prevent
    NULL-related issues in downstream SQL queries.

    Args:
        excel_path: Path to the ``.xlsx`` file.

    Returns:
        Dictionary mapping sheet names to their DataFrames.
    """
    logger.info("Loading sheets from %s", excel_path.name)
    workbook = pd.ExcelFile(excel_path, engine="openpyxl")
    sheets: dict[str, pd.DataFrame] = {}

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(workbook, sheet_name=sheet_name, engine="openpyxl")
        df = df.fillna("")
        sheets[sheet_name] = df
        logger.info(
            "  Sheet '%s': %d rows × %d columns",
            sheet_name, len(df), len(df.columns),
        )

    return sheets
