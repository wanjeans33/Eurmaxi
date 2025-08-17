# 德国家庭太阳能光伏模拟 - Django版本

这是一个用Django重新实现的太阳能光伏与储能系统模拟器，原本是用Streamlit开发的。

## 📋 功能特性

- **用户可调参数**: 光伏板/逆变器/电池规格和成本，电网价格，用电模式
- **用电量估算**: 从典型的4000kWh/年家庭开始，按月份不均匀分布（冬季略高）
- **发电量估算**: 使用德国月平均太阳辐照度，假设1kWp≈1000kWh/年
- **电池模型**: 简化模型，每天允许一次完整充放电循环
- **现金流对比**: 计算两种方案的年度电费节省
- **数据可视化**: 使用Chart.js显示光伏发电的自用与上网比例

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Django 4.2+
- pandas, numpy

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库迁移

```bash
python manage.py migrate
```

### 4. 国际化（中/英/德）

启用语言：中文(默认)、English、Deutsch。

1) 安装 gettext（Windows 建议安装 `choco install gettext` 或手动安装）

2) 生成/更新翻译文件：
```bash
django-admin makemessages -l zh_Hans
django-admin makemessages -l en
django-admin makemessages -l de
```

3) 在 `locale/<lang>/LC_MESSAGES/django.po` 填写翻译。

4) 编译翻译：
```bash
django-admin compilemessages
```

切换语言：右上角语言菜单。

### 5. 启动服务器

```bash
python manage.py runserver
```

或者使用快捷脚本：

```bash
python run_server.py
```

### 5. 访问应用

在浏览器中打开 http://127.0.0.1:8000/

## 📁 项目结构

```
Eurmaxi/
├── manage.py                 # Django管理脚本
├── run_server.py            # 快速启动脚本
├── requirements.txt         # 依赖包列表
├── solar_project/           # Django项目配置
│   ├── __init__.py
│   ├── settings.py         # 项目设置
│   ├── urls.py            # 主URL配置
│   └── wsgi.py            # WSGI配置
├── solar_app/              # 太阳能应用
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py           # Django表单
│   ├── views.py           # 视图函数
│   ├── urls.py            # 应用URL配置
│   ├── solar_calculator.py # 核心计算逻辑
│   └── templates/         # HTML模板
│       └── solar_app/
│           ├── base.html
│           ├── index.html
│           └── results.html
└── static/                # 静态文件
    └── solar_app/
        └── css/
            └── style.css
```

## 🔧 使用说明

1. **参数设置**: 在左侧面板调整太阳能系统参数
   - 太阳能板容量和成本
   - 逆变器功率和成本
   - 电池容量和成本（可选）
   - 电网电价和上网电价
   - 年度用电量和日间用电分布

2. **模拟计算**: 点击"开始模拟"按钮执行计算

3. **结果查看**: 查看经济效益评估、图表分析和详细数据表格

## 🎯 技术特点

- **响应式设计**: 使用Bootstrap 5，支持移动设备
- **数据可视化**: Chart.js实现交互式图表
- **表单验证**: Django Forms进行数据验证
- **模块化设计**: 计算逻辑与界面分离
- **API支持**: 提供JSON API接口

## 📊 计算模型

- **月度分辨率**: 为了理解和性能优化
- **德国数据**: 基于德国月平均太阳辐照度
- **季节性考虑**: 冬季用电量高（供暖、照明）
- **简化电池模型**: 100%往返效率，每日一次充放电
- **透明计算**: 所有计算步骤都有详细说明

## 🌐 API接口

### POST /api/simulate/

提交计算参数，返回JSON格式结果。

请求示例：
```json
{
    "pv_capacity_kwp": 5.0,
    "battery_capacity_kwh": 10.0,
    "annual_consumption_kwh": 4000,
    "pct_night": 30,
    "pct_morning_evening": 60,
    "pct_midday": 10,
    "grid_price": 0.30,
    "feed_in_price": 0.01
}
```

## ⚠️ 注意事项

- 所有数据仅供参考
- 实际性能可能因天气、设备效率、安装角度、阴影遮挡等因素而异
- 建议咨询专业的太阳能安装商获取准确评估

## 🔄 从Streamlit迁移

这个Django版本保持了原Streamlit应用的所有核心功能：

- ✅ 相同的计算逻辑和算法
- ✅ 相同的参数和配置选项
- ✅ 相同的图表类型和数据展示
- ✅ 更好的用户界面和交互体验
- ✅ 更强的扩展性和自定义能力

## 📝 开发说明

### 添加新功能

1. 修改 `solar_app/forms.py` 添加新的表单字段
2. 更新 `solar_app/solar_calculator.py` 添加新的计算逻辑
3. 修改模板文件添加新的界面元素

### 自定义样式

编辑 `static/solar_app/css/style.css` 文件来自定义外观。

### 部署到生产环境

1. 设置 `DEBUG = False` in settings.py
2. 配置 `ALLOWED_HOSTS`
3. 配置静态文件服务
4. 使用WSGI服务器（如uWSGI, Gunicorn）

## 📄 许可证

本项目仅供教学和演示使用。
