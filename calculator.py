from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any

import pandas as pd


def normalize_percentage(value: float | int | None) -> float:
    """Accept both 5 and 0.05 style percentage inputs."""
    if value is None:
        return 0.0
    numeric = float(value)
    if numeric < 0:
        return 0.0
    return numeric / 100 if numeric > 1 else numeric


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


@dataclass(slots=True)
class ProductInput:
    product_name: str = ""
    sku: str = ""
    category: str = ""
    currency: str = "RMB"
    unit_purchase_cost: float = 0.0
    units_per_set: int = 1
    packaging_cost: float = 0.0
    label_cost: float = 0.0
    domestic_logistics_cost: float = 0.0
    inbound_logistics_cost: float = 0.0
    qc_labor_cost: float = 0.0
    supply_price: float = 0.0
    loss_rate: float = 0.0
    return_reserve_rate: float = 0.0
    capital_cost_rate: float = 0.0
    exchange_loss_rate: float = 0.0
    target_margin_rate: float = 0.3
    cautious_margin_threshold: float = 0.2
    feasible_margin_threshold: float = 0.3


@dataclass(slots=True)
class ProfitResult:
    product_name: str
    sku: str
    category: str
    currency: str
    unit_base_cost: float
    set_base_cost: float
    loss_cost: float
    return_reserve_cost: float
    capital_cost: float
    exchange_loss_cost: float
    final_total_cost: float
    unit_net_profit: float
    set_net_profit: float
    gross_margin: float
    roi: float
    suggested_supply_price: float
    decision: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decision_label(
    gross_margin: float,
    cautious_margin_threshold: float = 0.2,
    feasible_margin_threshold: float = 0.3,
) -> str:
    if gross_margin >= feasible_margin_threshold:
        return "可做"
    if gross_margin >= cautious_margin_threshold:
        return "谨慎"
    return "不建议做"


def calculate_suggested_supply_price(
    final_total_cost: float,
    target_margin_rate: float,
) -> float:
    ratio = normalize_percentage(target_margin_rate)
    if ratio >= 1:
        return 0.0
    return safe_divide(final_total_cost, 1 - ratio)


def calculate_profit(product: ProductInput) -> ProfitResult:
    loss_rate = normalize_percentage(product.loss_rate)
    return_reserve_rate = normalize_percentage(product.return_reserve_rate)
    capital_rate = normalize_percentage(product.capital_cost_rate)
    exchange_loss_rate = normalize_percentage(product.exchange_loss_rate)
    target_margin_rate = normalize_percentage(product.target_margin_rate)
    cautious_margin = normalize_percentage(product.cautious_margin_threshold)
    feasible_margin = normalize_percentage(product.feasible_margin_threshold)

    unit_base_cost = float(product.unit_purchase_cost)
    set_base_cost = (
        unit_base_cost * int(product.units_per_set)
        + float(product.packaging_cost)
        + float(product.label_cost)
        + float(product.domestic_logistics_cost)
        + float(product.inbound_logistics_cost)
        + float(product.qc_labor_cost)
    )

    loss_cost = set_base_cost * loss_rate
    return_reserve_cost = set_base_cost * return_reserve_rate
    capital_cost = set_base_cost * capital_rate
    exchange_loss_cost = set_base_cost * exchange_loss_rate
    final_total_cost = (
        set_base_cost
        + loss_cost
        + return_reserve_cost
        + capital_cost
        + exchange_loss_cost
    )

    set_net_profit = float(product.supply_price) - final_total_cost
    unit_net_profit = safe_divide(set_net_profit, int(product.units_per_set))
    gross_margin = safe_divide(set_net_profit, float(product.supply_price))
    roi = safe_divide(float(product.supply_price), final_total_cost)
    suggested_supply_price = calculate_suggested_supply_price(
        final_total_cost=final_total_cost,
        target_margin_rate=target_margin_rate,
    )
    decision = decision_label(gross_margin, cautious_margin, feasible_margin)

    return ProfitResult(
        product_name=product.product_name,
        sku=product.sku,
        category=product.category,
        currency=product.currency,
        unit_base_cost=unit_base_cost,
        set_base_cost=set_base_cost,
        loss_cost=loss_cost,
        return_reserve_cost=return_reserve_cost,
        capital_cost=capital_cost,
        exchange_loss_cost=exchange_loss_cost,
        final_total_cost=final_total_cost,
        unit_net_profit=unit_net_profit,
        set_net_profit=set_net_profit,
        gross_margin=gross_margin,
        roi=roi,
        suggested_supply_price=suggested_supply_price,
        decision=decision,
    )


def get_batch_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "产品名称": "女士无痕内裤",
                "SKU": "NXK-001",
                "采购价": 3.2,
                "件数": 3,
                "包装成本": 0.8,
                "物流成本": 1.2,
                "供货价": 15.9,
                "损耗率": 3,
                "目标毛利率": 30,
            },
            {
                "产品名称": "文胸洗衣袋",
                "SKU": "WXXYD-002",
                "采购价": 2.8,
                "件数": 1,
                "包装成本": 0.5,
                "物流成本": 0.9,
                "供货价": 8.5,
                "损耗率": 2,
                "目标毛利率": 28,
            },
        ]
    )


def dataframe_to_excel_bytes(dataframe: pd.DataFrame, sheet_name: str = "测算结果") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                max(max_length + 2, 12),
                28,
            )

        percent_columns = {"毛利率"}
        currency_columns = {"最终成本", "供货价", "净利润", "建议供货价"}
        for header_cell in worksheet[1]:
            header = header_cell.value
            column_letter = header_cell.column_letter
            if header in percent_columns:
                for cell in worksheet[column_letter][1:]:
                    cell.number_format = "0.00%"
            elif header in currency_columns:
                for cell in worksheet[column_letter][1:]:
                    cell.number_format = "0.00"

    buffer.seek(0)
    return buffer.getvalue()


def _pick_value(row: pd.Series, aliases: list[str], default: Any = 0.0) -> Any:
    for alias in aliases:
        if alias in row.index and pd.notna(row[alias]):
            return row[alias]
    return default


def process_batch_dataframe(
    dataframe: pd.DataFrame,
    defaults: dict[str, Any],
) -> pd.DataFrame:
    required_columns = {"产品名称", "SKU", "采购价", "件数", "包装成本", "物流成本", "供货价", "损耗率", "目标毛利率"}
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        missing_text = "、".join(missing_columns)
        raise ValueError(f"上传文件缺少必要字段：{missing_text}")

    results: list[dict[str, Any]] = []
    for _, row in dataframe.iterrows():
        product = ProductInput(
            product_name=str(_pick_value(row, ["产品名称"], "")),
            sku=str(_pick_value(row, ["SKU"], "")),
            category=str(_pick_value(row, ["类目"], defaults.get("default_category", ""))),
            currency=str(_pick_value(row, ["币种"], defaults.get("default_currency", "RMB"))),
            unit_purchase_cost=float(_pick_value(row, ["采购价", "单件采购成本"], 0.0)),
            units_per_set=int(_pick_value(row, ["件数", "每套件数"], 1)),
            packaging_cost=float(_pick_value(row, ["包装成本"], defaults.get("default_packaging_cost", 0.0))),
            label_cost=float(_pick_value(row, ["贴标成本"], defaults.get("default_label_cost", 0.0))),
            domestic_logistics_cost=float(_pick_value(row, ["物流成本", "国内物流摊销"], defaults.get("default_domestic_logistics_cost", 0.0))),
            inbound_logistics_cost=float(_pick_value(row, ["入仓物流摊销"], defaults.get("default_inbound_logistics_cost", 0.0))),
            qc_labor_cost=float(_pick_value(row, ["质检人工摊销"], defaults.get("default_qc_labor_cost", 0.0))),
            supply_price=float(_pick_value(row, ["供货价", "平台供货价", "结算价"], 0.0)),
            loss_rate=float(_pick_value(row, ["损耗率"], defaults.get("default_loss_rate", 0.0))),
            return_reserve_rate=float(_pick_value(row, ["退供/滞销预提率"], defaults.get("default_return_reserve_rate", 0.0))),
            capital_cost_rate=float(_pick_value(row, ["资金成本率"], defaults.get("default_capital_cost_rate", 0.0))),
            exchange_loss_rate=float(_pick_value(row, ["汇率损耗率"], defaults.get("default_exchange_loss_rate", 0.0))),
            target_margin_rate=float(_pick_value(row, ["目标毛利率"], defaults.get("default_target_margin_rate", 30.0))),
            cautious_margin_threshold=float(defaults.get("cautious_margin_threshold", 20.0)),
            feasible_margin_threshold=float(defaults.get("feasible_margin_threshold", 30.0)),
        )
        result = calculate_profit(product)
        results.append(
            {
                "产品名称": result.product_name,
                "SKU": result.sku,
                "最终成本": result.final_total_cost,
                "供货价": product.supply_price,
                "净利润": result.set_net_profit,
                "毛利率": result.gross_margin,
                "建议供货价": result.suggested_supply_price,
                "是否值得做": result.decision,
            }
        )

    return pd.DataFrame(results)
