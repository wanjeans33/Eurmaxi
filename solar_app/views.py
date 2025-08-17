"""
Django Views for Solar Simulation App
处理用户请求和页面渲染的视图函数
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .forms import SolarSimulationForm
from .solar_calculator import SolarCalculator


def index(request):
    """主页视图 - 显示太阳能模拟表单"""
    form = SolarSimulationForm()
    context = {
        'form': form,
        'title': '🏠 德国家庭太阳能光伏模拟'
    }
    return render(request, 'solar_app/index.html', context)


def simulate(request):
    """处理太阳能模拟计算请求"""
    if request.method == 'POST':
        form = SolarSimulationForm(request.POST)
        
        if form.is_valid():
            # 获取计算参数
            params = form.get_calculation_params()
            # 将表单原始数据存入 session，便于语言切换后恢复
            request.session['last_form_data'] = request.POST.dict()
            
            # 执行计算
            calculator = SolarCalculator()
            results = calculator.calculate(params)
            
            # 准备图表数据
            chart_data = prepare_chart_data(results)
            
            # 计算储能投资分析
            extra_savings = results['savings_with_batt'] - results['savings_no_batt']
            payback_years = None
            if extra_savings > 0:
                payback_years = params['battery_cost'] / extra_savings
            
            context = {
                'form': form,
                'results': results,
                'chart_data': chart_data,
                'params': params,
                'extra_savings': extra_savings,
                'payback_years': payback_years,
                'title': '🏠 德国家庭太阳能光伏模拟 - 计算结果'
            }
            # 也缓存结果页所需的上下文（轻量字段）
            request.session['last_results'] = {
                'results': {
                    'monthly_data': results['monthly_data'],
                    'baseline_cost': results['baseline_cost'],
                    'cost_no_batt': results['cost_no_batt'],
                    'cost_with_batt': results['cost_with_batt'],
                    'savings_no_batt': results['savings_no_batt'],
                    'savings_with_batt': results['savings_with_batt'],
                },
                'params': params,
            }

            return render(request, 'solar_app/results.html', context)
        else:
            # 表单验证失败，返回带错误信息的表单
            context = {
                'form': form,
                'title': '🏠 德国家庭太阳能光伏模拟'
            }
            return render(request, 'solar_app/index.html', context)
    
    # GET: 如果存在上一次的session数据，使用其重算/恢复结果页，实现语言切换保留状态
    last_form_data = request.session.get('last_form_data')
    if last_form_data:
        form = SolarSimulationForm(last_form_data)
        if form.is_valid():
            params = form.get_calculation_params()
            calculator = SolarCalculator()
            results = calculator.calculate(params)
            chart_data = prepare_chart_data(results)
            extra_savings = results['savings_with_batt'] - results['savings_no_batt']
            payback_years = None
            if extra_savings > 0:
                payback_years = params['battery_cost'] / extra_savings
            context = {
                'form': form,
                'results': results,
                'chart_data': chart_data,
                'params': params,
                'extra_savings': extra_savings,
                'payback_years': payback_years,
                'title': '🏠 德国家庭太阳能光伏模拟 - 计算结果'
            }
            return render(request, 'solar_app/results.html', context)

    # 否则返回首页
    return index(request)


def prepare_chart_data(results):
    """准备图表所需的数据格式"""
    monthly_data = results['monthly_data']
    
    # 准备无储能方案的图表数据
    no_battery_data = {
        'labels': [item['月份'] for item in monthly_data],
        'datasets': [
            {
                'label': '自用电量',
                'data': [item['自用电量_无储能'] for item in monthly_data],
                'backgroundColor': 'rgba(54, 162, 235, 0.8)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            },
            {
                'label': '上网电量',
                'data': [item['上网电量_无储能'] for item in monthly_data],
                'backgroundColor': 'rgba(255, 206, 86, 0.8)',
                'borderColor': 'rgba(255, 206, 86, 1)',
                'borderWidth': 1
            }
        ]
    }
    
    # 准备有储能方案的图表数据
    with_battery_data = {
        'labels': [item['月份'] for item in monthly_data],
        'datasets': [
            {
                'label': '自用电量',
                'data': [item['自用电量_有储能'] for item in monthly_data],
                'backgroundColor': 'rgba(75, 192, 192, 0.8)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            },
            {
                'label': '上网电量',
                'data': [item['上网电量_有储能'] for item in monthly_data],
                'backgroundColor': 'rgba(255, 159, 64, 0.8)',
                'borderColor': 'rgba(255, 159, 64, 1)',
                'borderWidth': 1
            }
        ]
    }
    
    # 月度发电量和用电量对比
    generation_consumption_data = {
        'labels': [item['月份'] for item in monthly_data],
        'datasets': [
            {
                'label': '发电量',
                'data': [item['发电量'] for item in monthly_data],
                'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 2,
                'type': 'line'
            },
            {
                'label': '用电量',
                'data': [item['用电量'] for item in monthly_data],
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 2,
                'type': 'line'
            }
        ]
    }
    
    return {
        'no_battery': json.dumps(no_battery_data),
        'with_battery': json.dumps(with_battery_data),
        'generation_consumption': json.dumps(generation_consumption_data)
    }


@csrf_exempt
def api_simulate(request):
    """API接口 - 返回JSON格式的计算结果"""
    if request.method == 'POST':
        try:
            # 解析JSON请求
            data = json.loads(request.body)
            form = SolarSimulationForm(data)
            
            if form.is_valid():
                params = form.get_calculation_params()
                calculator = SolarCalculator()
                results = calculator.calculate(params)
                
                # 转换DataFrame为可序列化的格式
                results['monthly_data'] = results['monthly_data']
                results.pop('df', None)  # 移除DataFrame对象
                
                return JsonResponse({
                    'success': True,
                    'results': results
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '无效的JSON数据'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': '仅支持POST请求'
    })
