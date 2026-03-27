# T07 - 弘则信用债指数

## 项目概述

弘则信用债指数项目是一个完整的债券指数构建和分析系统，专注于构建信用债和金融债的标准10-100分位数指数。通过收益率分组和余额加权的方式计算指数，提供债券市场的分位数收益表现分析。

## 功能特性

- **分位数指数构建**: 将债券按收益率分为10个分位数组（0-10%, 10-20%, ..., 90-100%）
- **双维度分类**: 按债券类型（信用债/金融债）和收益率分位数双重分类
- **全价和净价并行**: 同时计算全价和净价指数
- **余额加权**: 使用债券余额作为权重，更反映市场实际情况
- **动态可视化**: 生成交互式Plotly图表，支持多维度分析
- **缓存机制**: 支持数据缓存，加速重复运行

## 目录结构

```
T07-弘则信用债指数/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── bond_system_2.py
│   ├── 1_complete_bond_index_analysis.py
│   ├── 2_daily_bond_index_update.py
│   └── 3_excel_bond_index_analysis.py
├── data/              # 数据文件
├── assets/            # 图片等资源
├── output/            # 输出目录
└── cache/             # 缓存目录（自动创建）
```

## 数据源

### PostgreSQL (tsdb)
- `hzcurve_credit`: 信用债收益率曲线数据
- `basicinfo_credit`: 信用债基础信息
- `basicinfo_finance`: 金融债基础信息

### MySQL (bond)
- `marketinfo_credit`: 信用债市场行情
- `marketinfo_finance`: 金融债市场行情
- `bond_indices`: 指数存储表
- `bond_index_constituents`: 指数构成表

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量（可选，用于数据库密码）
export PG_PASSWORD=your_password
export MYSQL_PASSWORD=your_password
```

## 使用方法

### 运行Notebook

```bash
# 启动Jupyter
jupyter notebook 重构.ipynb
```

### Notebook章节说明

1. **项目概述** - 功能描述、数据源、输出结果
2. **环境配置** - 导入依赖、配置参数
3. **数据获取** - 数据库连接、数据读取
4. **数据处理** - 分位数分组
5. **核心逻辑** - 指数计算
6. **执行与测试** - 数据验证、可视化、保存结果
7. **工具函数** - 每日更新、历史补充函数

### 核心函数

```python
# 每日更新
update_daily_indices(target_date, db, credit_bonds, finance_bonds)

# 历史数据补充
backfill_historical_indices(start_date, end_date, db, credit_bonds, finance_bonds)
```

## 输出结果

### 指数列表
- **信用债全价指数**: Credit_0-10_Full, Credit_10-20_Full, ..., Credit_90-100_Full
- **信用债净价指数**: Credit_0-10_Net, Credit_10-20_Net, ..., Credit_90-100_Net
- **金融债全价指数**: Finance_0-10_Full, Finance_10-20_Full, ..., Finance_90-100_Full
- **金融债净价指数**: Finance_0-10_Net, Finance_10-20_Net, ..., Finance_90-100_Net

### 输出文件
- `bond_indices_dashboard.html` - 交互式图表
- `bond_indices_data.csv` - 指数数据
- `bond_grouped_data.csv` - 分组数据

## 指数构建逻辑

1. **数据获取**: 从PostgreSQL获取标准期限为3年的收益率数据
2. **债券分类**: 根据basicinfo表区分信用债和金融债
3. **分位数分组**: 按收益率排序，分为10个分位数组
4. **指数计算**: 使用债券余额作为权重，计算全价和净价的加权平均指数
5. **结果输出**: 生成交互式图表和数据文件

## 配置说明

编辑 `config.py` 文件修改配置：

```python
# 指数配置
INDEX_CONFIG = {
    'target_term': 3,           # 目标期限（年）
    'percentile_groups': 10,     # 分位数组数
    'bond_types': ['credit', 'finance'],
    'price_types': ['full', 'net'],
}

# 日期范围（在Notebook中修改）
START_DATE = '2024-08-01'
END_DATE = '2025-02-14'
```

## 注意事项

1. 确保数据库连接正常
2. 第一次运行可能需要较长时间处理历史数据
3. 建议定期备份指数数据
4. 数据库密码建议使用环境变量配置

## 原始源代码

原始源代码位于 `src/` 目录：

- `bond_system_2.py` - 基础版本
- `1_complete_bond_index_analysis.py` - 完整分析版本（带缓存）
- `2_daily_bond_index_update.py` - 每日更新版本（带指数构成）
- `3_excel_bond_index_analysis.py` - Excel版本

## 更新日志

- 2026-02-14: 初始重构版本

## 维护者

量化研究员/债券分析师
