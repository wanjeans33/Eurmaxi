"""
Django Forms for Solar Simulation App
处理用户输入参数的表单定义
"""
from django import forms
from django.utils.translation import gettext_lazy as _


class SolarSimulationForm(forms.Form):
    """太阳能模拟参数表单"""
    
    # 系统组件
    pv_capacity_kwp = forms.FloatField(
        label=_('太阳能板容量 [kWp]'),
        initial=5.0,
        min_value=0.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'placeholder': '光伏阵列的装机峰值功率'
        }),
        help_text=_('光伏阵列的装机峰值功率')
    )
    
    pv_cost = forms.IntegerField(
        label=_('光伏阵列成本 [€]'),
        initial=9000,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '500'
        })
    )
    
    inverter_power_kw = forms.FloatField(
        label=_('逆变器功率 [kW]'),
        initial=5.0,
        min_value=0.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'placeholder': '逆变器的交流输出限制'
        }),
        help_text=_('逆变器的交流输出限制')
    )
    
    inverter_cost = forms.IntegerField(
        label=_('逆变器成本 [€]'),
        initial=1500,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '100'
        })
    )
    
    # 电池（可选）
    battery_capacity_kwh = forms.FloatField(
        label=_('电池容量 [kWh]'),
        initial=10.0,
        min_value=0.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1.0',
            'placeholder': '可用电池容量。0 = 仅无储能方案'
        }),
        help_text=_('可用电池容量。0 = 仅无储能方案')
    )
    
    battery_cost = forms.IntegerField(
        label=_('电池成本 [€]'),
        initial=6000,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '500'
        })
    )
    
    # 电价
    grid_price = forms.FloatField(
        label=_('电网电价 [€/kWh]'),
        initial=0.30,
        min_value=0.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    feed_in_price = forms.FloatField(
        label=_('上网电价 [€/kWh]'),
        initial=0.01,
        min_value=0.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    # 用电模式
    annual_consumption_kwh = forms.IntegerField(
        label=_('年度家庭用电量 [kWh]'),
        initial=4000,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '100',
            'placeholder': '典型的2成人+2儿童家庭 ≈ 4000 kWh/年'
        }),
        help_text=_('典型的2成人+2儿童家庭 ≈ 4000 kWh/年')
    )
    
    # 日间用电分布
    pct_night = forms.IntegerField(
        label=_('22-06时 [%]'),
        initial=30,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100'
        })
    )
    
    pct_morning_evening = forms.IntegerField(
        label=_('06-09时 & 17-22时 [%]'),
        initial=60,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100'
        })
    )
    
    pct_midday = forms.IntegerField(
        label=_('09-17时 [%]'),
        initial=10,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100'
        })
    )
    
    def clean(self):
        """表单级别的验证"""
        cleaned_data = super().clean()
        pct_night = cleaned_data.get('pct_night', 0)
        pct_morning_evening = cleaned_data.get('pct_morning_evening', 0)
        pct_midday = cleaned_data.get('pct_midday', 0)
        
        # 验证日间用电百分比总和为100%
        total_pct = pct_night + pct_morning_evening + pct_midday
        if total_pct != 100:
            raise forms.ValidationError(
                f'日间用电百分比必须总和为100%！当前总和为{total_pct}%'
            )
        
        return cleaned_data
    
    def get_calculation_params(self):
        """将表单数据转换为计算模块所需的参数格式"""
        if not self.is_valid():
            return None
            
        data = self.cleaned_data
        return {
            'pv_capacity_kwp': data['pv_capacity_kwp'],
            'battery_capacity_kwh': data['battery_capacity_kwh'],
            'annual_consumption_kwh': data['annual_consumption_kwh'],
            'cons_fraction_night': data['pct_night'] / 100.0,
            'cons_fraction_morn_even': data['pct_morning_evening'] / 100.0,
            'cons_fraction_midday': data['pct_midday'] / 100.0,
            'grid_price': data['grid_price'],
            'feed_in_price': data['feed_in_price'],
            # 也保存成本信息用于后续扩展
            'pv_cost': data['pv_cost'],
            'inverter_cost': data['inverter_cost'],
            'battery_cost': data['battery_cost'],
            'inverter_power_kw': data['inverter_power_kw'],
        }
