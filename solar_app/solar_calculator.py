"""
太阳能光伏与储能系统计算模块
从原始Streamlit应用提取的核心计算逻辑
"""
import numpy as np
import pandas as pd


class SolarCalculator:
    """太阳能模拟计算器"""
    
    # 德国月平均水平辐照度 (kWh/m²/day) - 基于PVGIS等数据集
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
    
    def __init__(self):
        # 归一化季节性系数
        self.seasonal_factors = self.CONSUMPTION_SEASONAL_FACTORS / \
            self.CONSUMPTION_SEASONAL_FACTORS.sum()
        
        # 预计算每装机kWp的月度kWh产量
        annual_irradiance_sum = self.MONTHLY_IRRADIANCE.sum()
        self.monthly_kwh_per_kwp = 1000 * self.MONTHLY_IRRADIANCE / annual_irradiance_sum
    
    def simulate_month(self, gen_kwh: float, c_mid: float, c_me: float, 
                      c_night: float, batt_capacity: float, days: int):
        """
        模拟单个月份两种方案的函数
        
        返回 (无储能结果, 有储能结果) 的元组。
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
    
    def calculate(self, params):
        """
        执行完整的太阳能模拟计算
        
        params: 字典，包含所有输入参数
        返回: 计算结果字典
        """
        # 提取参数
        pv_capacity_kwp = params['pv_capacity_kwp']
        battery_capacity_kwh = params['battery_capacity_kwh']
        annual_consumption_kwh = params['annual_consumption_kwh']
        cons_fraction_night = params['cons_fraction_night']
        cons_fraction_morn_even = params['cons_fraction_morn_even']
        cons_fraction_midday = params['cons_fraction_midday']
        grid_price = params['grid_price']
        feed_in_price = params['feed_in_price']
        
        # 构建月度用电和发电曲线
        monthly_consumption = annual_consumption_kwh * self.seasonal_factors
        monthly_generation = pv_capacity_kwp * self.monthly_kwh_per_kwp  # kWh

        # 将月度用电量分配到三个时间窗口
        cons_night = monthly_consumption * cons_fraction_night
        cons_morn_even = monthly_consumption * cons_fraction_morn_even
        cons_midday = monthly_consumption * cons_fraction_midday

        # 运行12个月的模拟
        results = []
        for i in range(12):
            no_batt, with_batt = self.simulate_month(
                gen_kwh=monthly_generation[i],
                c_mid=cons_midday[i],
                c_me=cons_morn_even[i],
                c_night=cons_night[i],
                batt_capacity=battery_capacity_kwh,
                days=self.DAYS_IN_MONTH[i]
            )
            results.append({
                "月份": self.MONTH_NAMES[i],
                "发电量": monthly_generation[i],
                "用电量": monthly_consumption[i],
                # 无储能
                "自用电量_无储能": no_batt["self_use"],
                "上网电量_无储能": no_batt["export"],
                "购电量_无储能": no_batt["grid_purchase"],
                # 有储能
                "自用电量_有储能": with_batt["self_use"],
                "上网电量_有储能": with_batt["export"],
                "购电量_有储能": with_batt["grid_purchase"],
            })

        df = pd.DataFrame(results)

        # 经济效益评估
        baseline_cost = annual_consumption_kwh * grid_price

        cost_no_batt = df["购电量_无储能"].sum() * grid_price - \
            df["上网电量_无储能"].sum() * feed_in_price

        cost_with_batt = df["购电量_有储能"].sum() * grid_price - \
            df["上网电量_有储能"].sum() * feed_in_price

        savings_no_batt = baseline_cost - cost_no_batt
        savings_with_batt = baseline_cost - cost_with_batt

        return {
            'monthly_data': df.to_dict('records'),
            'baseline_cost': baseline_cost,
            'cost_no_batt': cost_no_batt,
            'cost_with_batt': cost_with_batt,
            'savings_no_batt': savings_no_batt,
            'savings_with_batt': savings_with_batt,
            'df': df  # 用于图表生成
        }
