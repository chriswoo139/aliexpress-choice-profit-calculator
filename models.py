# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from config import INPUT_COLUMNS, PRICING_RULES, PRODUCT_TYPES


def to_float(value: Any, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    if isinstance(value, str):
        value = value.strip().replace("%", "")
        if value in {"", "-", "无"}:
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    return int(round(to_float(value, float(default))))


def to_bool(value: Any, default: bool = False) -> bool:
    if pd.isna(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"是", "有", "高", "true", "yes", "y", "1"}


def normalize_rate(value: float | int | None) -> float:
    if value is None:
        return 0.0
    numeric = max(float(value), 0.0)
    return numeric / 100 if numeric > 1 else numeric


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


@dataclass(slots=True)
class ProductRecord:
    product_name: str = ""
    sku: str = ""
    product_type: str = "无痕内裤"
    purchase_price_rmb: float = 0.0
    packaging_cost_rmb: float = 0.0
    domestic_shipping_rmb: float = PRICING_RULES["domestic_shipping_rmb"]
    qc_labor_rmb: float = PRICING_RULES["qc_labor_rmb"]
    loss_rate: float = PRICING_RULES["loss_rate"]
    capital_cost_rate: float = PRICING_RULES["capital_cost_rate"]
    unit_weight_g: float = 0.0
    combo_count: int = 1
    supplier_moq: int = 0
    color_count: int = 1
    size_count: int = 1
    is_light_small: bool = True
    easy_return: bool = False
    compliance_risk: bool = False
    differentiation: str = ""
    competitor_lowest_price: float = 0.0
    competitor_mainstream_price: float = 0.0
    estimated_supply_price: float = 0.0

    @classmethod
    def from_series(cls, row: pd.Series) -> "ProductRecord":
        product_type = str(row.get("产品类型", "无痕内裤")).strip() or "无痕内裤"
        if product_type not in PRODUCT_TYPES:
            product_type = "其他"

        return cls(
            product_name=str(row.get("产品名称", "")).strip(),
            sku=str(row.get("SKU", "")).strip(),
            product_type=product_type,
            purchase_price_rmb=to_float(row.get("采购价 RMB")),
            packaging_cost_rmb=to_float(row.get("包装成本 RMB")),
            domestic_shipping_rmb=to_float(row.get("国内运费 RMB"), PRICING_RULES["domestic_shipping_rmb"]),
            qc_labor_rmb=to_float(row.get("质检人工 RMB"), PRICING_RULES["qc_labor_rmb"]),
            loss_rate=normalize_rate(to_float(row.get("损耗率 %"), PRICING_RULES["loss_rate"])),
            capital_cost_rate=normalize_rate(to_float(row.get("资金占用率 %"), PRICING_RULES["capital_cost_rate"])),
            unit_weight_g=to_float(row.get("单品重量 g")),
            combo_count=max(to_int(row.get("组合件数"), 1), 1),
            supplier_moq=max(to_int(row.get("供应商起订量"), 0), 0),
            color_count=max(to_int(row.get("颜色数量"), 1), 0),
            size_count=max(to_int(row.get("尺码数量"), 1), 0),
            is_light_small=to_bool(row.get("是否轻小件"), True),
            easy_return=to_bool(row.get("是否容易退货"), False),
            compliance_risk=to_bool(row.get("是否有合规风险"), False),
            differentiation=str(row.get("差异化卖点", "")).strip(),
            competitor_lowest_price=to_float(row.get("竞品最低售价")),
            competitor_mainstream_price=to_float(row.get("竞品主流售价")),
            estimated_supply_price=to_float(row.get("预估平台供货价")),
        )

    def to_input_row(self) -> dict[str, Any]:
        return {
            "产品名称": self.product_name,
            "SKU": self.sku,
            "产品类型": self.product_type,
            "采购价 RMB": self.purchase_price_rmb,
            "包装成本 RMB": self.packaging_cost_rmb,
            "国内运费 RMB": self.domestic_shipping_rmb,
            "质检人工 RMB": self.qc_labor_rmb,
            "损耗率 %": self.loss_rate * 100,
            "资金占用率 %": self.capital_cost_rate * 100,
            "单品重量 g": self.unit_weight_g,
            "组合件数": self.combo_count,
            "供应商起订量": self.supplier_moq,
            "颜色数量": self.color_count,
            "尺码数量": self.size_count,
            "是否轻小件": self.is_light_small,
            "是否容易退货": self.easy_return,
            "是否有合规风险": self.compliance_risk,
            "差异化卖点": self.differentiation,
            "竞品最低售价": self.competitor_lowest_price,
            "竞品主流售价": self.competitor_mainstream_price,
            "预估平台供货价": self.estimated_supply_price,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=INPUT_COLUMNS)


def sample_dataframe() -> pd.DataFrame:
    rows = [
        ProductRecord(
            product_name="女士无痕冰丝内裤三条装",
            sku="NXK-3P-001",
            product_type="无痕内裤",
            purchase_price_rmb=3.2,
            packaging_cost_rmb=0.55,
            unit_weight_g=35,
            combo_count=3,
            supplier_moq=300,
            color_count=6,
            size_count=4,
            is_light_small=True,
            easy_return=False,
            compliance_risk=False,
            differentiation="无痕、冰丝触感、中腰、三条装、颜色组合好",
            competitor_lowest_price=16.9,
            competitor_mainstream_price=22.9,
            estimated_supply_price=15.9,
        ),
        ProductRecord(
            product_name="三排两扣文胸延长扣",
            sku="BRA-EXT-002",
            product_type="文胸延长扣",
            purchase_price_rmb=0.42,
            packaging_cost_rmb=0.18,
            unit_weight_g=8,
            combo_count=6,
            supplier_moq=500,
            color_count=4,
            size_count=1,
            is_light_small=True,
            easy_return=False,
            compliance_risk=False,
            differentiation="多色组合、柔软底布、三排两扣、适配日常文胸",
            competitor_lowest_price=7.9,
            competitor_mainstream_price=12.9,
            estimated_supply_price=6.8,
        ),
    ]
    return pd.DataFrame([item.to_input_row() for item in rows], columns=INPUT_COLUMNS)


def normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in INPUT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = "" if column in {"产品名称", "SKU", "产品类型", "差异化卖点"} else 0
    normalized = normalized[INPUT_COLUMNS]
    if normalized.empty:
        return sample_dataframe()
    return normalized
