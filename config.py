# -*- coding: utf-8 -*-
"""业务规则配置。

运营同事后续只需要改这里的权重、阈值、默认成本和文案映射，不需要改计算代码。
"""

PRODUCT_TYPES = [
    "无痕内裤",
    "运动内衣",
    "文胸延长扣",
    "肩带防滑扣",
    "胸贴",
    "塑身衣",
    "其他",
]

SCORING_RULES = {
    "weights": {
        "market_demand": 20,
        "supply_price_advantage": 20,
        "size_stability": 15,
        "differentiation": 15,
        "logistics_packaging": 10,
        "return_risk": 10,
        "compliance_risk": 10,
    },
    "market_base_score": {
        "无痕内裤": 18,
        "运动内衣": 17,
        "文胸延长扣": 14,
        "肩带防滑扣": 13,
        "胸贴": 15,
        "塑身衣": 16,
        "其他": 10,
    },
    "grade_thresholds": {
        "A": 85,
        "B": 70,
        "C": 55,
        "D": 0,
    },
    "actions": {
        "sample_score": 70,
        "quote_score": 65,
        "abandon_below_score": 55,
        "minimum_margin_for_quote": 0.12,
    },
}

PRICING_RULES = {
    "domestic_shipping_rmb": 0.50,
    "qc_labor_rmb": 0.20,
    "loss_rate": 0.03,
    "capital_cost_rate": 0.015,
    "minimum_margin_rate": 0.15,
    "aggressive_margin_rate": 0.20,
    "target_margin_rate": 0.28,
    "safe_margin_rate": 0.35,
}

FORMULA_RULES = {
    "单件真实成本": "采购价 RMB × 组合件数 + 包装成本 RMB + 国内运费 RMB + 质检人工 RMB + 损耗成本 + 资金占用成本",
    "损耗成本": "(采购价 RMB × 组合件数 + 包装成本 RMB + 国内运费 RMB + 质检人工 RMB) × 损耗率",
    "资金占用成本": "(采购价 RMB × 组合件数 + 包装成本 RMB + 国内运费 RMB + 质检人工 RMB) × 资金占用率",
    "单件毛利": "预估平台供货价 - 单件真实成本",
    "毛利率": "单件毛利 / 预估平台供货价",
    "按毛利率反推报价": "单件真实成本 / (1 - 目标毛利率)",
}

PRODUCT_COPY_RULES = {
    "material_by_type": {
        "无痕内裤": "Nylon and spandex blend",
        "运动内衣": "Nylon, polyester and spandex blend",
        "文胸延长扣": "Soft polyester fabric with stainless steel hooks",
        "肩带防滑扣": "Soft silicone",
        "胸贴": "Skin-friendly silicone",
        "塑身衣": "Nylon and spandex compression fabric",
        "其他": "Soft synthetic blend",
    },
    "feature_keywords": {
        "无痕内裤": ["seamless", "no-show", "stretchy", "breathable"],
        "运动内衣": ["wireless", "padded", "supportive", "workout"],
        "文胸延长扣": ["bra extender", "adjustable", "comfortable", "multi-hook"],
        "肩带防滑扣": ["anti-slip", "strap holder", "invisible", "easy to use"],
        "胸贴": ["self-adhesive", "invisible", "reusable", "backless"],
        "塑身衣": ["tummy control", "smooth fit", "shaping", "stretch"],
        "其他": ["comfortable", "lightweight", "daily use", "easy care"],
    },
    "title_suffix": {
        "无痕内裤": "Seamless No Show Panties for Women",
        "运动内衣": "Wireless Padded Sports Bra for Women",
        "文胸延长扣": "Bra Extender Hooks for Women",
        "肩带防滑扣": "Anti Slip Bra Strap Clips",
        "胸贴": "Invisible Silicone Nipple Covers",
        "塑身衣": "Women Shapewear Bodysuit",
        "其他": "Women Underwear Accessory",
    },
}

COMPLIANCE_RULES = {
    "risky_title_words": [
        "sexy",
        "erotic",
        "adult",
        "nude",
        "hot",
        "seductive",
        "guaranteed",
        "best",
        "medical",
        "cure",
    ],
    "adult_sensitive_words": [
        "fetish",
        "bdsm",
        "porn",
        "lingerie model",
        "see through body",
    ],
    "model_image_tips": [
        "避免过度暴露、挑逗姿势和成人暗示场景。",
        "优先使用平铺图、模特半身正面自然站姿或局部功能展示。",
        "胸贴、内裤、塑身衣类目建议准备无真人主图或谨慎模特图方案。",
    ],
}

INPUT_COLUMNS = [
    "产品名称",
    "SKU",
    "产品类型",
    "采购价 RMB",
    "包装成本 RMB",
    "国内运费 RMB",
    "质检人工 RMB",
    "损耗率 %",
    "资金占用率 %",
    "单品重量 g",
    "组合件数",
    "供应商起订量",
    "颜色数量",
    "尺码数量",
    "是否轻小件",
    "是否容易退货",
    "是否有合规风险",
    "差异化卖点",
    "竞品最低售价",
    "竞品主流售价",
    "预估平台供货价",
]
