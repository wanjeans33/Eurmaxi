import streamlit as st
import pandas as pd
import numpy as np

# 必须在所有其他 Streamlit 命令之前调用 set_page_config
st.set_page_config(page_title="德国家庭太阳能储能模拟", layout="wide")

# =============================================================================
# 德国家庭太阳能光伏与储能系统模拟
# =============================================================================
# 本 Streamlit 应用程序用于估算德国典型家庭（2个成人+2个儿童）安装
# 屋顶太阳能光伏系统（有储能/无储能）的经济效益。模型采用月度分辨率
# 以便于理解和性能优化。
#
# 主要功能：
# 1. 用户可调参数 - 光伏板/逆变器/电池规格和成本，电网价格，用电模式
# 2. 用电量估算 - 从典型的4000kWh/年家庭开始，按月份不均匀分布（冬季略高）
# 3. 发电量估算 - 使用德国月平均太阳辐照度，假设1kWp≈1000kWh/年
# 4. 电池模型（简化）- 每天允许一次完整充放电循环，受装机容量和光伏剩余限制
# 5. 现金流对比 - 计算两种方案的年度电费节省
# 6. 可视化 - 堆叠柱状图显示光伏发电的自用与上网比例
#
# 模型刻意保持简单但透明，所有计算都有详细注释供教学使用。
# =============================================================================

st.title("🏠 德国家庭太阳能光伏模拟")

# ---------------------------------------------------------------------
# 1. 默认常量和辅助数据
# ---------------------------------------------------------------------

# 德国月平均水平辐照度 (kWh/m²/day) - 基于PVGIS等数据集
# 这些数值是合理的近似值
MONTHLY_IRRADIANCE = np.array([
    0.83, 1.54, 2.56, 3.75, 4.81, 5.16,
    5.33, 4.98, 3.42, 2.07, 1.02, 0.70
])

# 每月天数（非闰年）
DAYS_IN_MONTH = np.array([
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
])
MONTH_NAMES = [
    "1月", "2月", "3月", "4月", "5月", "6月",
    "7月", "8月", "9月", "10月", "11月", "12月"
]

# 季节性用电系数 - 总和为1.0
# 冬季月份（12-2月）→ 用电量较高（供暖、照明）
# 夏季月份（6-8月）→ 用电量略低
CONSUMPTION_SEASONAL_FACTORS = np.array([
    0.095, 0.085, 0.09, 0.08, 0.08, 0.075,
    0.075, 0.075, 0.08, 0.085, 0.095, 0.105
])
# 完整性检查 - 如果上述系数总和不等于1则归一化
CONSUMPTION_SEASONAL_FACTORS = CONSUMPTION_SEASONAL_FACTORS / \
    CONSUMPTION_SEASONAL_FACTORS.sum()

# 预计算每装机kWp的月度kWh产量
annual_irradiance_sum = MONTHLY_IRRADIANCE.sum()
MONTHLY_KWH_PER_KWP = 1000 * MONTHLY_IRRADIANCE / annual_irradiance_sum

# ---------------------------------------------------------------------
# 2. 侧边栏 - 用户输入
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("🔧 模拟参数")

    st.subheader("系统组件")
    pv_capacity_kwp = st.number_input(
        "太阳能板容量 [kWp]",
        min_value=0.0, value=5.0, step=0.5,
        help="光伏阵列的装机峰值功率"
    )
    pv_cost = st.number_input("光伏阵列成本 [€]", min_value=0, value=9000, step=500)

    inverter_power_kw = st.number_input(
        "逆变器功率 [kW]", min_value=0.0, value=5.0, step=0.5,
        help="逆变器的交流输出限制"
    )
    inverter_cost = st.number_input("逆变器成本 [€]", min_value=0, value=1500, step=100)

    st.subheader("电池（可选）")
    battery_capacity_kwh = st.number_input(
        "电池容量 [kWh]", min_value=0.0, value=10.0, step=1.0,
        help="可用电池容量。0 = 仅无储能方案"
    )
    battery_cost = st.number_input("电池成本 [€]", min_value=0, value=6000, step=500)

    st.subheader("电价")
    grid_price = st.number_input("电网电价 [€/kWh]", min_value=0.0, value=0.30, step=0.01)
    feed_in_price = st.number_input("上网电价 [€/kWh]", min_value=0.0, value=0.01, step=0.01)

    st.subheader("用电模式")
    annual_consumption_kwh = st.number_input(
        "年度家庭用电量 [kWh]",
        min_value=0, value=4000, step=100,
        help="典型的2成人+2儿童家庭 ≈ 4000 kWh/年"
    )

    st.markdown("**日间用电分布** *(必须总和为100%)*")
    col1, col2, col3 = st.columns(3)
    with col1:
        pct_night = st.number_input("22-06时 [%]", min_value=0, max_value=100, value=30)
    with col2:
        pct_morning_evening = st.number_input("06-09时 & 17-22时 [%]", min_value=0, max_value=100, value=60)
    with col3:
        pct_midday = st.number_input("09-17时 [%]", min_value=0, max_value=100, value=10)

    if pct_night + pct_morning_evening + pct_midday != 100:
        st.error("日间用电百分比必须总和为100%！")

# 将百分比转换为分数
cons_fraction_night = pct_night / 100
cons_fraction_morn_even = pct_morning_evening / 100
cons_fraction_midday = pct_midday / 100

# ---------------------------------------------------------------------
# 3. 构建月度用电和发电曲线
# ---------------------------------------------------------------------
monthly_consumption = annual_consumption_kwh * CONSUMPTION_SEASONAL_FACTORS
monthly_generation = pv_capacity_kwp * MONTHLY_KWH_PER_KWP  # kWh

# 将月度用电量分配到三个时间窗口
cons_night = monthly_consumption * cons_fraction_night
cons_morn_even = monthly_consumption * cons_fraction_morn_even
cons_midday = monthly_consumption * cons_fraction_midday

# ---------------------------------------------------------------------
# 4. 模拟单个月份两种方案的函数
# ---------------------------------------------------------------------

def simulate_month(gen_kwh: float,
                   c_mid: float, c_me: float, c_night: float,
                   batt_capacity: float, days: int):
    """返回 (无储能结果, 有储能结果) 的元组。

    每个结果都是包含以下键的字典：
        - self_use (kWh) 自用电量
        - export (kWh) 上网电量
        - grid_purchase (kWh) 从电网购电量
    """
    # --------------------- 方案1 - 无储能 -------------------
    self_use_no_batt = min(gen_kwh, c_mid)           # 仅中午时段重叠
    export_no_batt = max(0, gen_kwh - c_mid)         # 剩余送入电网
    grid_no_batt = c_mid + c_me + c_night - self_use_no_batt

    no_batt = dict(self_use=self_use_no_batt,
                   export=export_no_batt,
                   grid_purchase=grid_no_batt)

    # --------------------- 方案2 - 有储能 -----------------
    if batt_capacity <= 0:
        # 退化情况 - 与无储能相同
        return no_batt, no_batt

    # 1) 中午时段优先自用
    self_use_mid = min(gen_kwh, c_mid)
    surplus = max(0, gen_kwh - c_mid)

    # 2) 电池每天可充电至其容量。近似计算
    #    月度可储存能量为容量 * 天数
    monthly_batt_limit = batt_capacity * days

    batt_charge = min(surplus, monthly_batt_limit, c_me + c_night)  # 储存不超过后续需求
    export_with_batt = surplus - batt_charge

    # 3) 电池放电覆盖早晚+夜间负荷
    energy_from_batt = batt_charge  # 为简化假设往返效率 = 100%

    remaining_load = c_me + c_night - energy_from_batt
    grid_with_batt = max(0, remaining_load)

    self_use_with_batt = self_use_mid + energy_from_batt

    with_batt = dict(self_use=self_use_with_batt,
                     export=export_with_batt,
                     grid_purchase=grid_with_batt)

    return no_batt, with_batt

# ---------------------------------------------------------------------
# 5. 运行12个月的模拟
# ---------------------------------------------------------------------
results = []
for i in range(12):
    no_batt, with_batt = simulate_month(
        gen_kwh=monthly_generation[i],
        c_mid=cons_midday[i],
        c_me=cons_morn_even[i],
        c_night=cons_night[i],
        batt_capacity=battery_capacity_kwh,
        days=DAYS_IN_MONTH[i]
    )
    results.append({
        "月份": MONTH_NAMES[i],
        "发电量": monthly_generation[i],
        "用电量": monthly_consumption[i],
        # 无储能
        "自用电量(无储能)": no_batt["self_use"],
        "上网电量(无储能)": no_batt["export"],
        "购电量(无储能)": no_batt["grid_purchase"],
        # 有储能
        "自用电量(有储能)": with_batt["self_use"],
        "上网电量(有储能)": with_batt["export"],
        "购电量(有储能)": with_batt["grid_purchase"],
    })

df = pd.DataFrame(results)

# ---------------------------------------------------------------------
# 6. 经济效益评估
# ---------------------------------------------------------------------

# 基准成本 - 无光伏，全部从电网购电
baseline_cost = annual_consumption_kwh * grid_price

cost_no_batt = df["购电量(无储能)"].sum() * grid_price - \
    df["上网电量(无储能)"].sum() * feed_in_price

cost_with_batt = df["购电量(有储能)"].sum() * grid_price - \
    df["上网电量(有储能)"].sum() * feed_in_price

savings_no_batt = baseline_cost - cost_no_batt
savings_with_batt = baseline_cost - cost_with_batt

# ---------------------------------------------------------------------
# 7. 显示关键指标
# ---------------------------------------------------------------------
col_a, col_b, col_c = st.columns(3)
col_a.metric("基准年度电费", f"€ {baseline_cost:,.0f}")
col_b.metric("无储能方案电费", f"€ {cost_no_batt:,.0f}", 
             delta=f"节省 € {savings_no_batt:,.0f}")
col_c.metric("有储能方案电费", f"€ {cost_with_batt:,.0f}", 
             delta=f"节省 € {savings_with_batt:,.0f}")

st.markdown("---")

# ---------------------------------------------------------------------
# 8. 可视化 - 堆叠柱状图
# ---------------------------------------------------------------------
import altair as alt

def make_stack(df: pd.DataFrame, cols: list, title: str):
    """返回Altair堆叠柱状图"""
    base = pd.melt(
        df, id_vars=["月份"], value_vars=cols,
        var_name="类别", value_name="kWh"
    )
    chart = alt.Chart(base).mark_bar().encode(
        x=alt.X('月份:N', sort=MONTH_NAMES),
        y=alt.Y('kWh:Q', title='电量 (kWh)'),
        color=alt.Color('类别:N'),
        tooltip=['类别', 'kWh']
    ).properties(title=title, height=400)
    return chart

st.altair_chart(make_stack(df, ["自用电量(无储能)", "上网电量(无储能)"],
                          "光伏利用情况 - 无储能方案"), use_container_width=True)

if battery_capacity_kwh > 0:
    st.altair_chart(make_stack(df, ["自用电量(有储能)", "上网电量(有储能)"],
                              "光伏利用情况 - 有储能方案"),
                    use_container_width=True)

# ---------------------------------------------------------------------
# 9. 详细结果表格（可选）
# ---------------------------------------------------------------------
with st.expander("显示详细月度数据"):
    st.dataframe(df.style.format({col: "{:.1f}" for col in df.columns if col != "月份"}))

st.caption("© 2025 太阳能模拟演示 - 所有数据仅供参考，实际性能可能因天气、设备效率等因素而异") 