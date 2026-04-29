from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from calculator import (
    ProductInput,
    calculate_profit,
    calculate_suggested_supply_price,
    dataframe_to_excel_bytes,
    get_batch_template,
    normalize_percentage,
    process_batch_dataframe,
)


st.set_page_config(
    page_title="AliExpress Choice 全托管利润计算器",
    page_icon="📈",
    layout="wide",
)


DEFAULT_SETTINGS: dict[str, Any] = {
    "default_category": "女士内衣",
    "default_currency": "RMB",
    "default_packaging_cost": 0.0,
    "default_label_cost": 0.15,
    "default_domestic_logistics_cost": 0.5,
    "default_inbound_logistics_cost": 0.8,
    "default_qc_labor_cost": 0.2,
    "default_loss_rate": 3.0,
    "default_return_reserve_rate": 2.0,
    "default_capital_cost_rate": 1.5,
    "default_exchange_loss_rate": 1.0,
    "default_target_margin_rate": 30.0,
    "cautious_margin_threshold": 20.0,
    "feasible_margin_threshold": 30.0,
}

CURRENCY_SYMBOLS = {
    "RMB": "¥",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}


def init_settings() -> None:
    if "settings" not in st.session_state:
        st.session_state["settings"] = DEFAULT_SETTINGS.copy()


def get_settings() -> dict[str, Any]:
    return st.session_state["settings"]


def format_currency(value: float, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, "")
    return f"{symbol}{value:,.2f}"


def render_header() -> None:
    st.title("速卖通 AliExpress Choice 全托管利润计算器")
    st.caption("面向跨境卖家的中文利润测算工具，快速判断平台供货价是否值得做，并反推合理报价。")


def render_single_product_page() -> None:
    settings = get_settings()
    st.subheader("单品测算")

    with st.form("single_product_form"):
        left_col, right_col = st.columns(2)
        with left_col:
            product_name = st.text_input("产品名称", value="女士无痕内裤")
            sku = st.text_input("SKU", value="NXK-001")
            category = st.text_input("类目", value=settings["default_category"])
            currency = st.selectbox("币种", options=list(CURRENCY_SYMBOLS.keys()), index=list(CURRENCY_SYMBOLS.keys()).index(settings["default_currency"]))
            unit_purchase_cost = st.number_input("单件采购成本", min_value=0.0, value=3.20, step=0.1)
            units_per_set = st.number_input("每套件数", min_value=1, value=3, step=1)
            packaging_cost = st.number_input("包装成本", min_value=0.0, value=float(settings["default_packaging_cost"]), step=0.1)
            label_cost = st.number_input("贴标成本", min_value=0.0, value=float(settings["default_label_cost"]), step=0.05)

        with right_col:
            domestic_logistics_cost = st.number_input("国内物流摊销", min_value=0.0, value=float(settings["default_domestic_logistics_cost"]), step=0.1)
            inbound_logistics_cost = st.number_input("入仓物流摊销", min_value=0.0, value=float(settings["default_inbound_logistics_cost"]), step=0.1)
            qc_labor_cost = st.number_input("质检人工摊销", min_value=0.0, value=float(settings["default_qc_labor_cost"]), step=0.05)
            supply_price = st.number_input("平台供货价 / 结算价", min_value=0.0, value=15.90, step=0.1)
            loss_rate = st.number_input("损耗率 %", min_value=0.0, value=float(settings["default_loss_rate"]), step=0.5)
            return_reserve_rate = st.number_input("退供/滞销预提率 %", min_value=0.0, value=float(settings["default_return_reserve_rate"]), step=0.5)
            capital_cost_rate = st.number_input("资金成本率 %", min_value=0.0, value=float(settings["default_capital_cost_rate"]), step=0.5)
            exchange_loss_rate = st.number_input("汇率损耗率 %", min_value=0.0, value=float(settings["default_exchange_loss_rate"]), step=0.5)
            target_margin_rate = st.number_input("目标毛利率 %", min_value=0.0, max_value=99.0, value=float(settings["default_target_margin_rate"]), step=1.0)

        submitted = st.form_submit_button("开始测算", use_container_width=True)

    if not submitted:
        st.info("填写参数后点击“开始测算”，即可看到单品利润、毛利率和建议供货价。")
        return

    product = ProductInput(
        product_name=product_name,
        sku=sku,
        category=category,
        currency=currency,
        unit_purchase_cost=unit_purchase_cost,
        units_per_set=units_per_set,
        packaging_cost=packaging_cost,
        label_cost=label_cost,
        domestic_logistics_cost=domestic_logistics_cost,
        inbound_logistics_cost=inbound_logistics_cost,
        qc_labor_cost=qc_labor_cost,
        supply_price=supply_price,
        loss_rate=loss_rate,
        return_reserve_rate=return_reserve_rate,
        capital_cost_rate=capital_cost_rate,
        exchange_loss_rate=exchange_loss_rate,
        target_margin_rate=target_margin_rate,
        cautious_margin_threshold=float(settings["cautious_margin_threshold"]),
        feasible_margin_threshold=float(settings["feasible_margin_threshold"]),
    )
    result = calculate_profit(product)

    metric_cols = st.columns(4)
    metric_cols[0].metric("单套净利润", format_currency(result.set_net_profit, currency))
    metric_cols[1].metric("毛利率", f"{result.gross_margin:.2%}")
    metric_cols[2].metric("最终总成本", format_currency(result.final_total_cost, currency))
    metric_cols[3].metric("最低建议供货价", format_currency(result.suggested_supply_price, currency))

    st.success(f"结论：{result.decision}")

    detail_df = pd.DataFrame(
        [
            ("单件基础成本", result.unit_base_cost),
            ("单套基础成本", result.set_base_cost),
            ("损耗成本", result.loss_cost),
            ("退供/滞销预提成本", result.return_reserve_cost),
            ("资金成本", result.capital_cost),
            ("汇率损耗成本", result.exchange_loss_cost),
            ("最终总成本", result.final_total_cost),
            ("单件净利润", result.unit_net_profit),
            ("单套净利润", result.set_net_profit),
            ("毛利率", result.gross_margin),
            ("投入产出比", result.roi),
            ("建议供货价", result.suggested_supply_price),
        ],
        columns=["指标", "结果"],
    )
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
    )

    export_df = pd.DataFrame(
        [
            {
                "产品名称": product_name,
                "SKU": sku,
                "最终成本": result.final_total_cost,
                "供货价": supply_price,
                "净利润": result.set_net_profit,
                "毛利率": result.gross_margin,
                "建议供货价": result.suggested_supply_price,
                "是否值得做": result.decision,
            }
        ]
    )
    st.download_button(
        "导出当前测算结果 Excel",
        data=dataframe_to_excel_bytes(export_df),
        file_name=f"{sku or 'single-product'}_利润测算.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_reverse_pricing_page() -> None:
    settings = get_settings()
    st.subheader("供货价反推")
    st.caption("基于最终成本和目标毛利率，反推最低建议供货价。")

    reverse_mode = st.radio(
        "反推方式",
        options=["直接输入最终成本", "按成本结构计算最终成本"],
        horizontal=True,
    )

    if reverse_mode == "直接输入最终成本":
        col1, col2 = st.columns(2)
        with col1:
            currency = st.selectbox("币种", options=list(CURRENCY_SYMBOLS.keys()), key="reverse_currency")
            final_total_cost = st.number_input("最终总成本", min_value=0.0, value=10.0, step=0.1, key="reverse_final_cost")
        with col2:
            target_margin_rate = st.number_input(
                "目标毛利率 %",
                min_value=0.0,
                max_value=99.0,
                value=float(settings["default_target_margin_rate"]),
                step=1.0,
                key="reverse_target_margin_direct",
            )

        suggested_price = calculate_suggested_supply_price(final_total_cost, target_margin_rate)
        st.metric("最低建议供货价", format_currency(suggested_price, currency))
        st.info(f"计算公式：最低供货价 = {final_total_cost:.2f} / (1 - {normalize_percentage(target_margin_rate):.2%})")
        return

    with st.form("reverse_cost_breakdown_form"):
        left_col, right_col = st.columns(2)
        with left_col:
            product_name = st.text_input("产品名称", value="文胸延长扣", key="reverse_product_name")
            sku = st.text_input("SKU", value="YCK-001", key="reverse_sku")
            currency = st.selectbox("币种", options=list(CURRENCY_SYMBOLS.keys()), key="reverse_currency_cost")
            unit_purchase_cost = st.number_input("单件采购成本", min_value=0.0, value=0.85, step=0.05, key="reverse_unit_purchase_cost")
            units_per_set = st.number_input("每套件数", min_value=1, value=2, step=1, key="reverse_units_per_set")
            packaging_cost = st.number_input("包装成本", min_value=0.0, value=float(settings["default_packaging_cost"]), step=0.1, key="reverse_packaging_cost")
            label_cost = st.number_input("贴标成本", min_value=0.0, value=float(settings["default_label_cost"]), step=0.05, key="reverse_label_cost")
        with right_col:
            domestic_logistics_cost = st.number_input("国内物流摊销", min_value=0.0, value=float(settings["default_domestic_logistics_cost"]), step=0.1, key="reverse_domestic")
            inbound_logistics_cost = st.number_input("入仓物流摊销", min_value=0.0, value=float(settings["default_inbound_logistics_cost"]), step=0.1, key="reverse_inbound")
            qc_labor_cost = st.number_input("质检人工摊销", min_value=0.0, value=float(settings["default_qc_labor_cost"]), step=0.05, key="reverse_qc")
            loss_rate = st.number_input("损耗率 %", min_value=0.0, value=float(settings["default_loss_rate"]), step=0.5, key="reverse_loss_rate")
            return_reserve_rate = st.number_input("退供/滞销预提率 %", min_value=0.0, value=float(settings["default_return_reserve_rate"]), step=0.5, key="reverse_return_rate")
            capital_cost_rate = st.number_input("资金成本率 %", min_value=0.0, value=float(settings["default_capital_cost_rate"]), step=0.5, key="reverse_capital_rate")
            exchange_loss_rate = st.number_input("汇率损耗率 %", min_value=0.0, value=float(settings["default_exchange_loss_rate"]), step=0.5, key="reverse_exchange_rate")
            target_margin_rate = st.number_input("目标毛利率 %", min_value=0.0, max_value=99.0, value=float(settings["default_target_margin_rate"]), step=1.0, key="reverse_target_margin_cost")

        submitted = st.form_submit_button("反推建议供货价", use_container_width=True)

    if not submitted:
        st.info("你可以直接输入最终成本，也可以按完整成本结构自动反推供货价。")
        return

    result = calculate_profit(
        ProductInput(
            product_name=product_name,
            sku=sku,
            currency=currency,
            unit_purchase_cost=unit_purchase_cost,
            units_per_set=units_per_set,
            packaging_cost=packaging_cost,
            label_cost=label_cost,
            domestic_logistics_cost=domestic_logistics_cost,
            inbound_logistics_cost=inbound_logistics_cost,
            qc_labor_cost=qc_labor_cost,
            supply_price=0.0,
            loss_rate=loss_rate,
            return_reserve_rate=return_reserve_rate,
            capital_cost_rate=capital_cost_rate,
            exchange_loss_rate=exchange_loss_rate,
            target_margin_rate=target_margin_rate,
            cautious_margin_threshold=float(settings["cautious_margin_threshold"]),
            feasible_margin_threshold=float(settings["feasible_margin_threshold"]),
        )
    )

    reverse_cols = st.columns(3)
    reverse_cols[0].metric("最终总成本", format_currency(result.final_total_cost, currency))
    reverse_cols[1].metric("最低建议供货价", format_currency(result.suggested_supply_price, currency))
    reverse_cols[2].metric("目标毛利率", f"{normalize_percentage(target_margin_rate):.2%}")

    st.dataframe(
        pd.DataFrame(
            [
                ("单套基础成本", result.set_base_cost),
                ("损耗成本", result.loss_cost),
                ("退供/滞销预提成本", result.return_reserve_cost),
                ("资金成本", result.capital_cost),
                ("汇率损耗成本", result.exchange_loss_cost),
                ("最终总成本", result.final_total_cost),
                ("建议供货价", result.suggested_supply_price),
            ],
            columns=["指标", "结果"],
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_batch_page() -> None:
    settings = get_settings()
    st.subheader("批量测算")
    st.caption("上传 Excel 后自动批量测算利润，并支持结果导出。")

    template_df = get_batch_template()
    st.download_button(
        "下载批量导入模板",
        data=dataframe_to_excel_bytes(template_df, sheet_name="导入模板"),
        file_name="AliExpress_Choice_批量测算模板.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown(
        """
        必填字段：
        `产品名称`、`SKU`、`采购价`、`件数`、`包装成本`、`物流成本`、`供货价`、`损耗率`、`目标毛利率`

        可选字段：
        `类目`、`币种`、`贴标成本`、`入仓物流摊销`、`质检人工摊销`、`退供/滞销预提率`、`资金成本率`、`汇率损耗率`
        """
    )

    uploaded_file = st.file_uploader("上传批量测算 Excel", type=["xlsx", "xls"])
    if uploaded_file is None:
        st.info("先下载模板填数，或直接上传你自己的 SKU 测算表。")
        return

    raw_df = pd.read_excel(uploaded_file)
    st.write("上传预览")
    st.dataframe(raw_df, use_container_width=True, hide_index=True)

    try:
        result_df = process_batch_dataframe(raw_df, settings)
    except ValueError as exc:
        st.error(str(exc))
        return

    st.write("测算结果")
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    feasible_count = int((result_df["是否值得做"] == "可做").sum())
    cautious_count = int((result_df["是否值得做"] == "谨慎").sum())
    not_recommended_count = int((result_df["是否值得做"] == "不建议做").sum())
    summary_cols = st.columns(3)
    summary_cols[0].metric("可做 SKU", feasible_count)
    summary_cols[1].metric("谨慎 SKU", cautious_count)
    summary_cols[2].metric("不建议 SKU", not_recommended_count)

    st.download_button(
        "导出批量测算结果 Excel",
        data=dataframe_to_excel_bytes(result_df),
        file_name="AliExpress_Choice_批量测算结果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_settings_page() -> None:
    st.subheader("参数设置")
    st.caption("这里的默认参数会影响单品测算、供货价反推和批量测算中的默认值。")
    settings = get_settings().copy()

    with st.form("settings_form"):
        col1, col2 = st.columns(2)
        with col1:
            settings["default_category"] = st.text_input("默认类目", value=settings["default_category"])
            settings["default_currency"] = st.selectbox(
                "默认币种",
                options=list(CURRENCY_SYMBOLS.keys()),
                index=list(CURRENCY_SYMBOLS.keys()).index(settings["default_currency"]),
            )
            settings["default_packaging_cost"] = st.number_input("默认包装成本", min_value=0.0, value=float(settings["default_packaging_cost"]), step=0.1)
            settings["default_label_cost"] = st.number_input("默认贴标成本", min_value=0.0, value=float(settings["default_label_cost"]), step=0.05)
            settings["default_domestic_logistics_cost"] = st.number_input("默认国内物流摊销", min_value=0.0, value=float(settings["default_domestic_logistics_cost"]), step=0.1)
            settings["default_inbound_logistics_cost"] = st.number_input("默认入仓物流摊销", min_value=0.0, value=float(settings["default_inbound_logistics_cost"]), step=0.1)

        with col2:
            settings["default_qc_labor_cost"] = st.number_input("默认质检人工摊销", min_value=0.0, value=float(settings["default_qc_labor_cost"]), step=0.05)
            settings["default_loss_rate"] = st.number_input("默认损耗率 %", min_value=0.0, value=float(settings["default_loss_rate"]), step=0.5)
            settings["default_return_reserve_rate"] = st.number_input("默认退供/滞销预提率 %", min_value=0.0, value=float(settings["default_return_reserve_rate"]), step=0.5)
            settings["default_capital_cost_rate"] = st.number_input("默认资金成本率 %", min_value=0.0, value=float(settings["default_capital_cost_rate"]), step=0.5)
            settings["default_exchange_loss_rate"] = st.number_input("默认汇率损耗率 %", min_value=0.0, value=float(settings["default_exchange_loss_rate"]), step=0.5)
            settings["default_target_margin_rate"] = st.number_input("默认目标毛利率 %", min_value=0.0, max_value=99.0, value=float(settings["default_target_margin_rate"]), step=1.0)

        threshold_cols = st.columns(2)
        with threshold_cols[0]:
            settings["cautious_margin_threshold"] = st.number_input("“谨慎”下限 %", min_value=0.0, max_value=99.0, value=float(settings["cautious_margin_threshold"]), step=1.0)
        with threshold_cols[1]:
            settings["feasible_margin_threshold"] = st.number_input("“可做”下限 %", min_value=0.0, max_value=99.0, value=float(settings["feasible_margin_threshold"]), step=1.0)

        save_settings = st.form_submit_button("保存参数设置", use_container_width=True)

    if save_settings:
        st.session_state["settings"] = settings
        st.success("默认参数已更新。")

    st.write("当前默认参数")
    st.json(st.session_state["settings"])


def main() -> None:
    init_settings()
    render_header()
    page = st.sidebar.radio(
        "功能导航",
        options=["单品测算", "批量测算", "供货价反推", "参数设置"],
    )

    if page == "单品测算":
        render_single_product_page()
    elif page == "批量测算":
        render_batch_page()
    elif page == "供货价反推":
        render_reverse_pricing_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()
