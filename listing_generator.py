# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

import pandas as pd

from config import PRODUCT_COPY_RULES
from models import ProductRecord


def trim_title(title: str, limit: int = 128) -> str:
    title = " ".join(title.split())
    if len(title) <= limit:
        return title
    return title[:limit].rsplit(" ", 1)[0]


def build_title(record: ProductRecord) -> str:
    suffix = PRODUCT_COPY_RULES["title_suffix"].get(record.product_type, "Women Underwear Accessory")
    keywords = PRODUCT_COPY_RULES["feature_keywords"].get(record.product_type, [])
    pack_text = f"{record.combo_count} Pack" if record.combo_count > 1 else ""
    color_text = "Multi Color" if record.color_count >= 3 else ""
    title = f"{pack_text} {color_text} {suffix} {' '.join(keywords[:2])}"
    if record.product_name and record.product_type == "其他":
        title = f"{record.product_name} Women Underwear Accessory"
    return trim_title(title)


def build_bullets(record: ProductRecord) -> list[str]:
    material = material_for(record)
    pack = f"{record.combo_count} piece{'s' if record.combo_count > 1 else ''}"
    selling_point = record.differentiation or "comfortable daily wear and easy matching"
    bullets = [
        f"Soft Material: Made of {material.lower()} for a smooth and comfortable touch.",
        f"Practical Pack: Includes {pack}, suitable for daily use, travel or replacement needs.",
        f"Comfort Fit: Designed for lightweight wear with flexible movement and a neat look under outfits.",
        f"Easy Care: Simple to wash, dry and store; suitable for regular wardrobe rotation.",
        f"Product Feature: {selling_point}.",
    ]
    return bullets


def material_for(record: ProductRecord) -> str:
    return PRODUCT_COPY_RULES["material_by_type"].get(record.product_type, "Soft synthetic blend")


def build_description(record: ProductRecord) -> str:
    title = build_title(record)
    material = material_for(record)
    return (
        f"{title} is designed for women's daily underwear and accessory needs. "
        f"The product uses {material.lower()} with a lightweight feel and practical packaging. "
        "It is suitable for everyday dressing, travel, sports or wardrobe adjustment depending on the product type. "
        "Please check the size information and package quantity before purchase."
    )


def build_attributes(record: ProductRecord) -> dict[str, str]:
    return {
        "Product Type": record.product_type,
        "Material": material_for(record),
        "Quantity": f"{record.combo_count} piece(s)",
        "Color Options": f"{record.color_count} color(s)",
        "Size Options": f"{record.size_count} size(s)",
        "Feature": record.differentiation or ", ".join(PRODUCT_COPY_RULES["feature_keywords"].get(record.product_type, [])),
        "Care Instructions": "Hand wash recommended; air dry; keep away from sharp objects.",
        "Target Gender": "Women",
    }


def build_size_table(record: ProductRecord) -> pd.DataFrame:
    if record.product_type in {"文胸延长扣", "肩带防滑扣", "胸贴"}:
        return pd.DataFrame(
            [
                {"Size": "One Size", "Fit / Dimension": "Universal daily use", "Note": "Please check product images for exact shape."}
            ]
        )
    if record.product_type == "运动内衣":
        return pd.DataFrame(
            [
                {"Size": "S", "Bust cm": "68-78", "Recommended Cup": "A-B"},
                {"Size": "M", "Bust cm": "78-88", "Recommended Cup": "B-C"},
                {"Size": "L", "Bust cm": "88-98", "Recommended Cup": "C-D"},
                {"Size": "XL", "Bust cm": "98-108", "Recommended Cup": "D-E"},
            ]
        )
    if record.product_type == "塑身衣":
        return pd.DataFrame(
            [
                {"Size": "S", "Waist cm": "60-68", "Hip cm": "78-88"},
                {"Size": "M", "Waist cm": "68-76", "Hip cm": "88-96"},
                {"Size": "L", "Waist cm": "76-84", "Hip cm": "96-104"},
                {"Size": "XL", "Waist cm": "84-92", "Hip cm": "104-112"},
            ]
        )
    return pd.DataFrame(
        [
            {"Size": "S", "Waist cm": "60-68", "Hip cm": "78-88"},
            {"Size": "M", "Waist cm": "68-76", "Hip cm": "88-96"},
            {"Size": "L", "Waist cm": "76-84", "Hip cm": "96-104"},
            {"Size": "XL", "Waist cm": "84-92", "Hip cm": "104-112"},
        ]
    )


def build_packaging_info(record: ProductRecord) -> str:
    return (
        f"Package includes {record.combo_count} piece(s). "
        "Default package: individual OPP bag or simple retail-ready poly bag. "
        f"Estimated product weight: {record.unit_weight_g:g} g per piece before outer carton."
    )


def build_image_prompts(record: ProductRecord) -> dict[str, str]:
    title = build_title(record)
    neutral_style = "clean white background, soft natural light, accurate color, non-explicit commercial ecommerce style"
    return {
        "图片拍摄提示词": f"{title}, flat lay and detail close-up, show material texture and package quantity, {neutral_style}",
        "主图提示词": f"Main image for {title}, product only, front view, no provocative model pose, {neutral_style}",
        "详情页图片文案": "Soft touch | Comfortable fit | Easy to match | Clear pack quantity | Check size before order",
    }


def generate_listing(record: ProductRecord) -> dict[str, Any]:
    attributes = build_attributes(record)
    prompts = build_image_prompts(record)
    return {
        "产品名称": record.product_name,
        "SKU": record.sku,
        "产品类型": record.product_type,
        "英文标题": build_title(record),
        "五点卖点1": build_bullets(record)[0],
        "五点卖点2": build_bullets(record)[1],
        "五点卖点3": build_bullets(record)[2],
        "五点卖点4": build_bullets(record)[3],
        "五点卖点5": build_bullets(record)[4],
        "英文详情页描述": build_description(record),
        "商品属性": "\n".join(f"{key}: {value}" for key, value in attributes.items()),
        "材质说明": material_for(record),
        "尺码表": build_size_table(record).to_json(orient="records", force_ascii=False),
        "包装信息": build_packaging_info(record),
        **prompts,
    }
