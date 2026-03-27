# SVG数据提取工具

## 项目简介

本项目是一个从网页SVG图表中提取数据的工具集，支持从Highcharts生成的SVG图表中精确提取数据点。

## 主要功能

1. **SVG图表解析**: 从SVG文件中提取数据点坐标
2. **多图表类型支持**: 支持柱形图、线图等多种图表类型
3. **坐标转换**: 将SVG坐标转换为实际数据值
4. **线性插值**: 基于已知点进行精确插值
5. **X轴标签生成**: 根据起止日期自动生成时间序列

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 柱形图数据提取

```python
from config import get_known_points
from 重构 import extract_svg_data, save_to_excel

# 定义已知点 (svg_y, actual_y)
known_points = [
    (-68, -18.6),   # 最小值
    (83, 22.7),     # 中间值
    (186, 51.1)     # 最大值
]

# 提取数据
df = extract_svg_data(
    svg_file='chart.svg',
    known_points=known_points,
    start_year=1968,
    start_month=5,
    end_year=2024,
    end_month=5,
    chart_type='bar'
)

# 保存到Excel
save_to_excel(df, 'output.xlsx')
```

### 2. 线图数据提取

```python
df = extract_svg_data(
    svg_file='line_chart.svg',
    known_points=known_points,
    start_year=2000,
    start_month=1,
    end_year=2024,
    end_month=12,
    chart_type='line'
)
```

### 3. 保存到数据库

```python
from config import get_database_engine
from 重构 import save_to_database

engine = get_database_engine()
save_to_database(df, 'my_table', engine)
```

## 核心算法

### 线性插值

使用3个已知点进行线性插值，将SVG坐标转换为实际数值:

```
actual_y = actual_y2 + (svg_y - svg_y2) / (svg_y3 - svg_y2) * (actual_y3 - actual_y2)
```

### Y轴零点检测

自动检测柱形图中的Y轴零点位置:

- 正值柱形: y < y_zero
- 负值柱形: y = y_zero

## 项目结构

```
T52-svg提取数据/
├── 重构.ipynb        # 重构后的Jupyter Notebook
├── config.py         # 配置文件
├── requirements.txt  # 依赖列表
├── README.md         # 项目说明
└── src/              # 源代码目录
```

## 配置说明

在 `config.py` 中配置数据库连接和环境变量:

```python
# 环境变量
DB_HOST     # 数据库主机
DB_PORT     # 数据库端口
DB_USER     # 数据库用户名
DB_PASSWORD # 数据库密码
DB_NAME     # 数据库名称
```

## 注意事项

1. **已知点选择**: 选择图表上的最小值、中间值和最大值作为已知点
2. **Y轴零点**: 对于柱形图，需要正确设置Y轴零点
3. **数据验证**: 提取后建议验证数据的合理性

## 版本历史

- v1.0: 初始版本，支持基本的SVG数据提取功能
