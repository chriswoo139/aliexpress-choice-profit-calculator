# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from config import SCORING_RULES
from models import ProductRecord, safe_divide
from pricing import PricingResult, calculate_pricing


@dataclass(slots=True)
class ScoreResult:
    product_name: str
    sku: str
    product_type: str
    market_demand: float
    supply_price_advantage: float
    size_stability: float
    differentiation: float
    logistics_packaging: float
    return_risk: float
    compliance_risk: float
    total_score: float
    grade: str
    sample_advice: str
    quote_advice: str
    final_advice: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def calculate_market_demand(record: ProductRecord) -> float:
    base = SCORING_RULES["market_base_score"].get(record.product_type, 10)
    if record.competitor_mainstream_price > record.competitor_lowest_price > 0:
        spread = safe_divide(
            record.competitor_mainstream_price - record.competitor_lowest_price,
            record.competitor_lowest_price,
        )
        base += 1.5 if spread >= 0.35 else 0.5
    if record.color_count >= 4:
        base += 0.5
    return clamp(base, 0, SCORING_RULES["weights"]["market_demand"])


def calculate_supply_advantage(record: ProductRecord, pricing: PricingResult) -> float:
    max_score = SCORING_RULES["weights"]["supply_price_advantage"]
    if record.estimated_supply_price <= 0:
        return 8

    competitor_anchor = record.competitor_mainstream_price or record.competitor_lowest_price
    price_ratio_score = 0.0
    if competitor_anchor > 0:
        ratio = safe_divide(record.estimated_supply_price, competitor_anchor)
        if ratio <= 0.45:
            price_ratio_score = 10
        elif ratio <= 0.60:
            price_ratio_score = 8
        elif ratio <= 0.75:
            price_ratio_score = 6
        else:
            price_ratio_score = 3
    else:
        price_ratio_score = 5

    margin = pricing.gross_margin
    if margin >= 0.35:
        margin_score = 10
    elif margin >= 0.25:
        margin_score = 8
    elif margin >= 0.15:
        margin_score = 5
    elif margin > 0:
        margin_score = 2
    else:
        margin_score = 0

    return clamp(price_ratio_score + margin_score, 0, max_score)


def calculate_size_stability(record: ProductRecord) -> float:
    accessory_types = {"文胸延长扣", "肩带防滑扣", "胸贴"}
    max_score = SCORING_RULES["weights"]["size_stability"]
    if record.product_type in accessory_types:
        score = 14 if record.size_count <= 2 else 12
    elif record.product_type == "塑身衣":
        score = 8 if record.size_count >= 5 else 10
    else:
        if 3 <= record.size_count <= 5:
            score = 13
        elif record.size_count in {1, 2}:
            score = 10
        else:
            score = 8
    if record.easy_return:
        score -= 3
    return clamp(score, 0, max_score)


def calculate_differentiation(record: ProductRecord) -> float:
    text = record.differentiation.strip()
    if not text:
        return 3
    score = min(len(text) / 6, 10)
    separators = ["，", ",", "、", ";", "；", "|"]
    if any(separator in text for separator in separators):
        score += 3
    if any(word in text.lower() for word in ["无痕", "防滑", "多色", "可调", "组合", "亲肤", "高弹", "seamless", "anti-slip"]):
        score += 2
    return clamp(score, 0, SCORING_RULES["weights"]["differentiation"])


def calculate_logistics_packaging(record: ProductRecord) -> float:
    score = 10
    if not record.is_light_small:
        score -= 3
    if record.unit_weight_g > 100:
        score -= 2
    if record.unit_weight_g > 250:
        score -= 2
    if record.combo_count > 6:
        score -= 1
    if record.packaging_cost_rmb > 1.5:
        score -= 1
    return clamp(score, 0, SCORING_RULES["weights"]["logistics_packaging"])


def calculate_return_risk(record: ProductRecord) -> float:
    score = 10
    if record.easy_return:
        score -= 5
    if record.product_type in {"运动内衣", "塑身衣"}:
        score -= 2
    if record.size_count >= 6:
        score -= 2
    return clamp(score, 0, SCORING_RULES["weights"]["return_risk"])


def calculate_compliance_risk(record: ProductRecord) -> float:
    score = 10
    if record.compliance_risk:
        score -= 6
    if record.product_type in {"胸贴", "塑身衣"}:
        score -= 1
    return clamp(score, 0, SCORING_RULES["weights"]["compliance_risk"])


def grade_for_score(score: float) -> str:
    for grade, threshold in SCORING_RULES["grade_thresholds"].items():
        if score >= threshold:
            return grade
    return "D"


def build_reason(record: ProductRecord, pricing: PricingResult, score: float) -> str:
    reasons: list[str] = []
    if pricing.gross_margin >= 0.28:
        reasons.append("毛利率达到目标区间")
    elif pricing.gross_margin > 0:
        reasons.append("有利润但安全垫偏薄")
    else:
        reasons.append("当前供货价低于真实成本")
    if record.easy_return:
        reasons.append("尺码或试穿退货风险需要控制")
    if record.compliance_risk:
        reasons.append("图片与表达需重点合规审核")
    if record.is_light_small:
        reasons.append("轻小件物流友好")
    return "；".join(reasons) if reasons else "基础信息不足，建议补充竞品售价与卖点"


def calculate_score(record: ProductRecord) -> ScoreResult:
    pricing = calculate_pricing(record)
    market = calculate_market_demand(record)
    supply = calculate_supply_advantage(record, pricing)
    size = calculate_size_stability(record)
    diff = calculate_differentiation(record)
    logistics = calculate_logistics_packaging(record)
    returns = calculate_return_risk(record)
    compliance = calculate_compliance_risk(record)
    total = round(market + supply + size + diff + logistics + returns + compliance, 1)
    grade = grade_for_score(total)

    actions = SCORING_RULES["actions"]
    sample_advice = "建议打样" if total >= actions["sample_score"] and not record.compliance_risk else "暂缓打样"
    quote_advice = (
        "建议报价"
        if total >= actions["quote_score"] and pricing.gross_margin >= actions["minimum_margin_for_quote"]
        else "谨慎/暂不报价"
    )
    if total < actions["abandon_below_score"] or pricing.gross_margin < 0:
        final_advice = "建议放弃"
    elif quote_advice == "建议报价":
        final_advice = "进入报价池"
    else:
        final_advice = "补充信息后复核"

    return ScoreResult(
        product_name=record.product_name,
        sku=record.sku,
        product_type=record.product_type,
        market_demand=market,
        supply_price_advantage=supply,
        size_stability=size,
        differentiation=diff,
        logistics_packaging=logistics,
        return_risk=returns,
        compliance_risk=compliance,
        total_score=total,
        grade=grade,
        sample_advice=sample_advice,
        quote_advice=quote_advice,
        final_advice=final_advice,
        reason=build_reason(record, pricing, total),
    )


def score_to_export_row(result: ScoreResult) -> dict[str, Any]:
    return {
        "产品名称": result.product_name,
        "SKU": result.sku,
        "产品类型": result.product_type,
        "市场需求": result.market_demand,
        "供应价优势": result.supply_price_advantage,
        "尺码稳定性": result.size_stability,
        "差异化卖点": result.differentiation,
        "物流包装友好度": result.logistics_packaging,
        "退货风险": result.return_risk,
        "合规风险": result.compliance_risk,
        "总分": result.total_score,
        "等级": result.grade,
        "是否建议打样": result.sample_advice,
        "是否建议报价": result.quote_advice,
        "最终建议": result.final_advice,
        "原因": result.reason,
    }
