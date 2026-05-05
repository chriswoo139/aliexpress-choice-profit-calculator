# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from config import COMPLIANCE_RULES
from listing_generator import build_title, material_for
from models import ProductRecord


def compliance_check(record: ProductRecord) -> dict[str, Any]:
    title = build_title(record)
    title_lower = title.lower()
    issues: list[str] = []
    warnings: list[str] = []

    risky_words = [word for word in COMPLIANCE_RULES["risky_title_words"] if word in title_lower]
    if risky_words:
        issues.append(f"标题包含需谨慎使用的词：{', '.join(risky_words)}")

    adult_words = [
        word
        for word in COMPLIANCE_RULES["adult_sensitive_words"]
        if word in title_lower or word in record.differentiation.lower()
    ]
    if adult_words:
        issues.append(f"疑似成人敏感表达：{', '.join(adult_words)}")

    if record.compliance_risk:
        issues.append("手动标记为存在合规风险，建议人工复核标题、图片和详情页。")

    if record.product_type in {"胸贴", "塑身衣", "无痕内裤", "运动内衣"}:
        warnings.append("图片需避免过度性感、挑逗姿势和敏感成人表达。")
        warnings.append("模特图建议自然站姿、局部功能展示或平铺图，不强调身体暗示。")

    if not material_for(record):
        issues.append("材质说明缺失。")
    if record.size_count <= 0 and record.product_type not in {"文胸延长扣", "肩带防滑扣", "胸贴"}:
        issues.append("尺码表缺失或尺码数量为 0。")
    if record.combo_count <= 0:
        issues.append("包装数量不清楚。")
    if record.product_type in {"无痕内裤", "运动内衣", "塑身衣"} and record.size_count <= 1:
        warnings.append("服饰类尺码数量过少，需确认尺码表是否完整。")

    status = "高风险" if issues else ("注意" if warnings else "通过")
    return {
        "产品名称": record.product_name,
        "SKU": record.sku,
        "产品类型": record.product_type,
        "合规状态": status,
        "图片是否过度性感": "需人工确认，建议平铺/自然模特图" if record.product_type != "文胸延长扣" else "低风险",
        "标题是否有夸大词": "有风险词" if risky_words else "未发现",
        "材质是否填写完整": "完整" if material_for(record) else "缺失",
        "尺码表是否缺失": "可能缺失" if record.size_count <= 0 else "已生成基础尺码表",
        "包装数量是否清楚": "清楚" if record.combo_count > 0 else "不清楚",
        "是否涉及敏感成人表达": "疑似涉及" if adult_words else "未发现",
        "模特图表达建议": "；".join(COMPLIANCE_RULES["model_image_tips"]),
        "问题": "；".join(issues),
        "提醒": "；".join(warnings),
    }
