from pydantic import BaseModel, Field
from typing import List


class ColumnMeta(BaseModel):
    """Metadata for a single table column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="SQL data type (e.g. VARCHAR, NUMERIC, TIMESTAMP)")
    description: str = Field(..., description="Plain-English description of the column")


class TableMeta(BaseModel):
    """Metadata for a single database table."""

    table_name: str = Field(..., description="Name of the table")
    description: str = Field(..., description="Plain-English description of what the table stores")
    columns: List[ColumnMeta] = Field(..., description="List of column definitions")


class SchemaContext(BaseModel):
    """Root schema metadata object loaded from schema.json."""

    tables: List[TableMeta] = Field(..., description="All known tables in the data model")
