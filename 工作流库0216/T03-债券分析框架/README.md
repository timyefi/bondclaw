# T03 - 债券分析框架

## 项目概述

债券分析框架是信用研究的核心基础设施，用于分析不同期限、不同评级、不同类型债券的收益率、投资策略和风险评估。

## 功能特性

- **收益率曲线分析**：查询和分析不同债券品种的收益率曲线数据
- **投资策略分析**：支持久期维度、品种维度、资质维度三种策略分析
- **投资组合优化**：构建和评估不同债券投资组合的表现
- **可视化报告**：生成收益率对比图表、稳定性分析图表、累计收益图表

## 目录结构

```
T03-债券分析框架/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件
│   ├── 不同曲线投资顺序分析.py
│   ├── 债券数据准备.py
│   ├── 数据准备.py
│   ├── 数据分析.py
│   ├── 生成周期标注.py
│   ├── 国债收益率走势分析.py
│   └── 投资组合分析.py
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 数据源

- **数据库表**：
  - `bond.marketinfo_curve`：市场行情数据
  - `bond.basicinfo_curve`：基础信息数据

- **支持的债券类型**：
  - 利率债：国债、国开、口行、农发、地方债
  - 金融债：存单、普通金融债、二永
  - 信用债：城投、产业

## 安装说明

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
创建 `.env` 文件，配置数据库连接信息：
```
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_DATABASE=bond
```

3. 运行Notebook：
```bash
jupyter notebook 重构.ipynb
```

## 使用方法

### 1. 数据获取

```python
from config import Config
config = Config()

# 获取债券收益率数据
bond_data = get_all_bond_yield_data('2014-01-01', '2024-12-08')
```

### 2. 策略分析

```python
# 初始化策略分析器
portfolio = PortfolioStrategy()

# 获取各维度策略
dimension_strategies = portfolio.generate_dimension_strategies()

# 执行策略分析
results = analyze_dimension_performance(strategies, cycle_id)
```

### 3. 可视化

```python
# 绘制收益率曲线
plot_yield_curve(data, title='收益率曲线')

# 生成策略分析报告
generate_analysis_report(results_df, dimension, output_dir='output')
```

## 核心组件

### 1. 收益率数据查询

支持按债券类型、期限、评级等条件筛选数据：
- 债券类型：国债、国开、口行、农发、地方债、城投、产业等
- 期限范围：0-1年、1-3年、3-5年、5-7年、7-10年等
- 信用评级：AAA、AA+、AA、AA(2)、AA-

### 2. 策略维度

- **品种维度策略**：利率债 -> 金融债 -> 信用债 的不同排序
- **久期维度策略**：长久期优先 vs 短久期优先
- **资质维度策略**：高资质优先 vs 弱资质优先

### 3. 收益率下行周期

定义了6个历史收益率下行周期用于回测：
- 周期1：2014-01-02 至 2015-02-13
- 周期2：2015-06-11 至 2016-01-11
- 周期3：2018-01-18 至 2019-02-02
- 周期4：2019-11-04 至 2020-04-21
- 周期5：2021-03-10 至 2022-08-29
- 周期6：2023-02-22 至 2024-08-20

## 输出结果

- 收益率对比数据（CSV）
- 收益率走势图表（PNG）
- 投资策略分析报告（TXT）
- 策略统计信息（CSV）
- 累计收益图表（PNG）

## 注意事项

1. 数据库密码不应硬编码在代码中，请使用环境变量
2. 大数据量查询建议使用缓存机制
3. 可视化图表需要配置中文字体支持

## 更新日志

- 2024-02-14: 完成项目重构，创建Notebook和配置文件
