# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import INPUT_COLUMNS, PRICING_RULES, PRODUCT_TYPES, SCORING_RULES
from exporter import build_all_outputs, dataframe_to_excel_bytes, workbook_to_excel_bytes
from listing_generator import build_size_table
from models import ProductRecord, normalize_dataframe, sample_dataframe


st.set_page_config(
    page_title="速卖通全托管女性内衣选品与报价工具",
    page_icon="📊",
    layout="wide",
)


def init_state() -> None:
    if "input_df" not in st.session_state:
        st.session_state["input_df"] = sample_dataframe()


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")
    return pd.read_excel(uploaded_file)


def render_header() -> None:
    st.title("速卖通全托管女性内衣选品与报价工具")
    st.caption("用于女性内衣、无痕内裤、运动内衣、文胸配件、文胸延长扣、防滑肩带扣等类目的选品评分、供货报价、资料生成与 Excel 导出。")
    st.info("竞品价格请手动录入或通过 CSV/Excel 导入。本工具不接入违反平台规则的爬虫。", icon="ℹ️")


def render_sidebar() -> None:
    with st.sidebar:
        st.header("规则摘要")
        st.write("评分满分 100 分，A/B/C/D 自动分级。")
        st.write(
            f"建议报价目标毛利率：{PRICING_RULES['target_margin_rate']:.0%}；"
            f"安全报价毛利率：{PRICING_RULES['safe_margin_rate']:.0%}。"
        )
        with st.expander("评分权重", expanded=False):
            for key, value in SCORING_RULES["weights"].items():
                label = {
                    "market_demand": "市场需求",
                    "supply_price_advantage": "供应价优势",
                    "size_stability": "尺码稳定性",
                    "differentiation": "差异化卖点",
                    "logistics_packaging": "物流包装友好度",
                    "return_risk": "退货风险",
                    "compliance_risk": "合规风险",
                }[key]
                st.write(f"{label}: {value} 分")


def render_upload_area() -> None:
    st.subheader("1. 数据录入")
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        uploaded_file = st.file_uploader("上传 CSV / Excel", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            try:
                st.session_state["input_df"] = normalize_dataframe(read_uploaded_file(uploaded_file))
                st.success("文件已导入，可以在下方表格继续编辑。")
            except Exception as exc:  # pragma: no cover - Streamlit UI guard
                st.error(f"导入失败：{exc}")
    with col2:
        template = pd.DataFrame(columns=INPUT_COLUMNS)
        st.download_button(
            "下载空白导入模板",
            dataframe_to_excel_bytes(template, "导入模板"),
            file_name="aliexpress_choice_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col3:
        if st.button("恢复示例数据", use_container_width=True):
            st.session_state["input_df"] = sample_dataframe()
            st.rerun()


def render_manual_add_form() -> None:
    with st.expander("手动新增一个产品", expanded=False):
        with st.form("manual_add_form", clear_on_submit=False):
            left, middle, right = st.columns(3)
            with left:
                product_name = st.text_input("产品名称", value="女士无痕内裤")
                sku = st.text_input("SKU", value="NEW-001")
                product_type = st.selectbox("产品类型", PRODUCT_TYPES)
                purchase_price = st.number_input("采购价 RMB", min_value=0.0, value=3.0, step=0.1)
                packaging_cost = st.number_input("包装成本 RMB", min_value=0.0, value=0.5, step=0.1)
                domestic_shipping = st.number_input("国内运费 RMB", min_value=0.0, value=float(PRICING_RULES["domestic_shipping_rmb"]), step=0.1)
                qc_labor = st.number_input("质检人工 RMB", min_value=0.0, value=float(PRICING_RULES["qc_labor_rmb"]), step=0.05)
            with middle:
                loss_rate = st.number_input("损耗率 %", min_value=0.0, value=float(PRICING_RULES["loss_rate"] * 100), step=0.5)
                capital_rate = st.number_input("资金占用率 %", min_value=0.0, value=float(PRICING_RULES["capital_cost_rate"] * 100), step=0.5)
                unit_weight = st.number_input("单品重量 g", min_value=0.0, value=30.0, step=1.0)
                combo_count = st.number_input("组合件数", min_value=1, value=1, step=1)
                supplier_moq = st.number_input("供应商起订量", min_value=0, value=300, step=50)
                color_count = st.number_input("颜色数量", min_value=0, value=4, step=1)
                size_count = st.number_input("尺码数量", min_value=0, value=4, step=1)
            with right:
                is_light_small = st.checkbox("是否轻小件", value=True)
                easy_return = st.checkbox("是否容易退货", value=False)
                compliance_risk = st.checkbox("是否有合规风险", value=False)
                competitor_lowest = st.number_input("竞品最低售价", min_value=0.0, value=16.9, step=0.1)
                competitor_mainstream = st.number_input("竞品主流售价", min_value=0.0, value=22.9, step=0.1)
                estimated_supply = st.number_input("预估平台供货价", min_value=0.0, value=12.9, step=0.1)
                differentiation = st.text_area("差异化卖点", value="无痕、亲肤、高弹、多色组合")

            submitted = st.form_submit_button("添加到表格", use_container_width=True)
            if submitted:
                record = ProductRecord(
                    product_name=product_name,
                    sku=sku,
                    product_type=product_type,
                    purchase_price_rmb=purchase_price,
                    packaging_cost_rmb=packaging_cost,
                    domestic_shipping_rmb=domestic_shipping,
                    qc_labor_rmb=qc_labor,
                    loss_rate=loss_rate / 100,
                    capital_cost_rate=capital_rate / 100,
                    unit_weight_g=unit_weight,
                    combo_count=combo_count,
                    supplier_moq=supplier_moq,
                    color_count=color_count,
                    size_count=size_count,
                    is_light_small=is_light_small,
                    easy_return=easy_return,
                    compliance_risk=compliance_risk,
                    differentiation=differentiation,
                    competitor_lowest_price=competitor_lowest,
                    competitor_mainstream_price=competitor_mainstream,
                    estimated_supply_price=estimated_supply,
                )
                st.session_state["input_df"] = pd.concat(
                    [st.session_state["input_df"], pd.DataFrame([record.to_input_row()])],
                    ignore_index=True,
                )
                st.success("已添加。")


def render_data_editor() -> pd.DataFrame:
    st.write("可以直接在表格中修改数据，新增行后系统会自动参与评分和报价。")
    edited_df = st.data_editor(
        normalize_dataframe(st.session_state["input_df"]),
        num_rows="dynamic",
        use_container_width=True,
        height=380,
        column_config={
            "产品类型": st.column_config.SelectboxColumn("产品类型", options=PRODUCT_TYPES, required=True),
            "是否轻小件": st.column_config.CheckboxColumn("是否轻小件"),
            "是否容易退货": st.column_config.CheckboxColumn("是否容易退货"),
            "是否有合规风险": st.column_config.CheckboxColumn("是否有合规风险"),
            "差异化卖点": st.column_config.TextColumn("差异化卖点", width="large"),
        },
        key="input_editor",
    )
    st.session_state["input_df"] = normalize_dataframe(edited_df)
    return st.session_state["input_df"]


def render_score_tab(score_df: pd.DataFrame) -> None:
    st.subheader("2. 选品评分")
    if score_df.empty:
        st.warning("请先录入产品数据。")
        return

    metrics = st.columns(4)
    metrics[0].metric("产品数", len(score_df))
    metrics[1].metric("A级产品", int((score_df["等级"] == "A").sum()))
    metrics[2].metric("建议报价", int((score_df["是否建议报价"] == "建议报价").sum()))
    metrics[3].metric("平均得分", f"{score_df['总分'].mean():.1f}")
    st.dataframe(score_df.sort_values("总分", ascending=False), use_container_width=True, hide_index=True)


def render_pricing_tab(quote_df: pd.DataFrame) -> None:
    st.subheader("3. 利润与报价")
    if quote_df.empty:
        st.warning("请先录入产品数据。")
        return
    display_df = quote_df.copy()
    display_df["毛利率"] = display_df["毛利率"].map(lambda value: f"{value:.2%}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption("单件真实成本 = 采购价 × 组合件数 + 包装成本 + 国内运费 + 质检人工 + 损耗成本 + 资金占用成本。")


def render_listing_tab(listing_df: pd.DataFrame, input_df: pd.DataFrame) -> None:
    st.subheader("4. 商品资料生成")
    if listing_df.empty:
        st.warning("请先录入产品数据。")
        return
    st.dataframe(listing_df, use_container_width=True, hide_index=True)

    records = [ProductRecord.from_series(row) for _, row in normalize_dataframe(input_df).iterrows()]
    if records:
        selected = st.selectbox("查看尺码表示例", options=[record.sku or record.product_name for record in records])
        record = next(record for record in records if (record.sku or record.product_name) == selected)
        st.dataframe(build_size_table(record), use_container_width=True, hide_index=True)


def render_compliance_tab(compliance_df: pd.DataFrame) -> None:
    st.subheader("5. 合规检查")
    if compliance_df.empty:
        st.warning("请先录入产品数据。")
        return
    st.dataframe(compliance_df, use_container_width=True, hide_index=True)
    st.caption("合规检查为运营提醒，不替代平台规则和人工审核。内衣类目请重点复核主图、模特姿势、标题用词、材质、尺码和包装数量。")


def render_export_tab(outputs: dict[str, pd.DataFrame]) -> None:
    st.subheader("6. Excel 导出")
    st.write("可分别导出评分、报价、商品资料，也可以导出包含全部工作表的总表。")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            "导出评分表",
            dataframe_to_excel_bytes(outputs["选品评分"], "选品评分"),
            file_name="product_score_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "导出报价表",
            dataframe_to_excel_bytes(outputs["报价测算"], "报价测算"),
            file_name="quotation_sheet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "导出上架资料",
            dataframe_to_excel_bytes(outputs["商品资料"], "商品资料"),
            file_name="listing_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col4:
        st.download_button(
            "导出总表",
            workbook_to_excel_bytes(outputs),
            file_name="aliexpress_choice_full_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def main() -> None:
    init_state()
    render_header()
    render_sidebar()
    render_upload_area()
    render_manual_add_form()
    input_df = render_data_editor()
    outputs = build_all_outputs(input_df)

    score_tab, pricing_tab, listing_tab, compliance_tab, export_tab = st.tabs(
        ["选品评分", "利润报价", "商品资料", "合规检查", "导出"]
    )
    with score_tab:
        render_score_tab(outputs["选品评分"])
    with pricing_tab:
        render_pricing_tab(outputs["报价测算"])
    with listing_tab:
        render_listing_tab(outputs["商品资料"], input_df)
    with compliance_tab:
        render_compliance_tab(outputs["合规检查"])
    with export_tab:
        render_export_tab(outputs)


if __name__ == "__main__":
    main()
