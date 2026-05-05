# -*- coding: utf-8 -*-
from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

from compliance import compliance_check
from config import INPUT_COLUMNS
from listing_generator import generate_listing
from models import ProductRecord, normalize_dataframe
from pricing import calculate_pricing, pricing_to_export_row
from scoring import calculate_score, score_to_export_row


def records_from_dataframe(dataframe: pd.DataFrame) -> list[ProductRecord]:
    normalized = normalize_dataframe(dataframe)
    records: list[ProductRecord] = []
    for _, row in normalized.iterrows():
        record = ProductRecord.from_series(row)
        if record.product_name or record.sku:
            records.append(record)
    return records


def build_all_outputs(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    records = records_from_dataframe(dataframe)
    score_rows = [score_to_export_row(calculate_score(record)) for record in records]
    quote_rows = [pricing_to_export_row(calculate_pricing(record)) for record in records]
    listing_rows = [generate_listing(record) for record in records]
    compliance_rows = [compliance_check(record) for record in records]

    return {
        "录入数据": pd.DataFrame([record.to_input_row() for record in records], columns=INPUT_COLUMNS),
        "选品评分": pd.DataFrame(score_rows),
        "报价测算": pd.DataFrame(quote_rows),
        "商品资料": pd.DataFrame(listing_rows),
        "合规检查": pd.DataFrame(compliance_rows),
    }


def dataframe_to_excel_bytes(dataframe: pd.DataFrame, sheet_name: str) -> bytes:
    return workbook_to_excel_bytes({sheet_name: dataframe})


def workbook_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, dataframe in sheets.items():
            safe_sheet_name = sheet_name[:31]
            dataframe.to_excel(writer, index=False, sheet_name=safe_sheet_name)
            format_worksheet(writer.sheets[safe_sheet_name])
    buffer.seek(0)
    return buffer.getvalue()


def format_worksheet(worksheet: Any) -> None:
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for column_cells in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        width = min(max(max_length + 2, 12), 42)
        worksheet.column_dimensions[column_cells[0].column_letter].width = width
        for cell in column_cells[1:]:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    percent_headers = {"毛利率"}
    money_keywords = ["成本", "供货价", "报价", "毛利", "售价"]
    for header_cell in worksheet[1]:
        header = str(header_cell.value or "")
        column_letter = header_cell.column_letter
        if header in percent_headers:
            for cell in worksheet[column_letter][1:]:
                cell.number_format = "0.00%"
        elif any(keyword in header for keyword in money_keywords):
            for cell in worksheet[column_letter][1:]:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "0.00"

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
