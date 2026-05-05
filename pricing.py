# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from config import PRICING_RULES
from models import ProductRecord, safe_divide


@dataclass(slots=True)
class PricingResult:
    product_name: str
    sku: str
    product_type: str
    base_cost_rmb: float
    loss_cost_rmb: float
    capital_cost_rmb: float
    real_unit_cost_rmb: float
    platform_supply_price_rmb: float
    gross_profit_rmb: float
    gross_margin: float
    minimum_acceptable_supply_price_rmb: float
    aggressive_quote_rmb: float
    safe_quote_rmb: float
    suggested_quote_low_rmb: float
    suggested_quote_high_rmb: float
    abandon_below_rmb: float
    pricing_decision: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["毛利率 %"] = self.gross_margin * 100
        return data


def price_for_margin(cost: float, margin_rate: float) -> float:
    if margin_rate >= 1:
        return 0.0
    return safe_divide(cost, 1 - margin_rate)


def calculate_pricing(record: ProductRecord) -> PricingResult:
    base_cost = (
        record.purchase_price_rmb * record.combo_count
        + record.packaging_cost_rmb
        + record.domestic_shipping_rmb
        + record.qc_labor_rmb
    )
    loss_cost = base_cost * record.loss_rate
    capital_cost = base_cost * record.capital_cost_rate
    real_cost = base_cost + loss_cost + capital_cost

    supply_price = record.estimated_supply_price
    gross_profit = supply_price - real_cost
    gross_margin = safe_divide(gross_profit, supply_price)

    min_price = price_for_margin(real_cost, PRICING_RULES["minimum_margin_rate"])
    aggressive_price = price_for_margin(real_cost, PRICING_RULES["aggressive_margin_rate"])
    target_price = price_for_margin(real_cost, PRICING_RULES["target_margin_rate"])
    safe_price = price_for_margin(real_cost, PRICING_RULES["safe_margin_rate"])

    if supply_price <= 0:
        decision = "待报价"
    elif supply_price < min_price:
        decision = "放弃报价"
    elif gross_margin < PRICING_RULES["target_margin_rate"]:
        decision = "谨慎报价"
    else:
        decision = "建议报价"

    return PricingResult(
        product_name=record.product_name,
        sku=record.sku,
        product_type=record.product_type,
        base_cost_rmb=base_cost,
        loss_cost_rmb=loss_cost,
        capital_cost_rmb=capital_cost,
        real_unit_cost_rmb=real_cost,
        platform_supply_price_rmb=supply_price,
        gross_profit_rmb=gross_profit,
        gross_margin=gross_margin,
        minimum_acceptable_supply_price_rmb=min_price,
        aggressive_quote_rmb=aggressive_price,
        safe_quote_rmb=safe_price,
        suggested_quote_low_rmb=target_price,
        suggested_quote_high_rmb=safe_price,
        abandon_below_rmb=min_price,
        pricing_decision=decision,
    )


def pricing_to_export_row(result: PricingResult) -> dict[str, Any]:
    return {
        "产品名称": result.product_name,
        "SKU": result.sku,
        "产品类型": result.product_type,
        "单件真实成本": round(result.real_unit_cost_rmb, 2),
        "平台供货价": round(result.platform_supply_price_rmb, 2),
        "单件毛利": round(result.gross_profit_rmb, 2),
        "毛利率": result.gross_margin,
        "最低可接受供货价": round(result.minimum_acceptable_supply_price_rmb, 2),
        "建议报价区间低": round(result.suggested_quote_low_rmb, 2),
        "建议报价区间高": round(result.suggested_quote_high_rmb, 2),
        "安全报价": round(result.safe_quote_rmb, 2),
        "激进报价": round(result.aggressive_quote_rmb, 2),
        "放弃报价": round(result.abandon_below_rmb, 2),
        "报价建议": result.pricing_decision,
    }
