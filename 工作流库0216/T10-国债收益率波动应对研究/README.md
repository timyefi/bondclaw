# T10 - 国债收益率波动应对研究

## 项目概述

本项目专注于分析国债收益率的波动特征，识别波动周期和影响因素，制定相应的投资策略和风险管理方案。

### 核心功能

1. **行情突然性分析** - 分析国债收益率变动的集中度特征
2. **90%行情集中度指标** - 衡量达到90%累计变动所需的时间占比
3. **策略回测与优化** - 规则策略与买入持有策略的对比分析
4. **年度对比分析** - 历史年度策略表现的系统性评估

## 数据源

- **主要数据源**: MySQL数据库 `bond.marketinfo_curve` 表
- **债券代码**:
  - 10年国债: L001619604
  - 1年国债: L001618296
- **备用数据**: `data/国债收益率数据.xlsx`

## 目录结构

```
T10-国债收益率波动应对研究/
├── 重构.ipynb          # 主重构Notebook
├── config.py           # 配置参数
├── requirements.txt    # Python依赖
├── README.md           # 项目说明
├── src/                # 原始代码文件
│   ├── bond_yield_analysis.py              # 主分析脚本
│   ├── market_concentration_indicator.py   # 90%集中度指标计算
│   └── batch_historical_update.py          # 批量历史数据更新
├── data/               # 数据文件
├── assets/             # 图片资源
└── output/             # 输出结果
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

设置环境变量:
```bash
export DB_PASSWORD=your_password
```

### 3. 运行分析

```bash
# 运行主分析脚本
python src/bond_yield_analysis.py

# 计算当日90%集中度指标
python src/market_concentration_indicator.py

# 批量更新历史指标
python src/batch_historical_update.py
```

### 4. 使用Jupyter Notebook

```bash
jupyter notebook 重构.ipynb
```

## 核心算法

### 90%行情集中度指标

该指标衡量过去90天内收益率变动的集中程度:
- 计算每日收益率变化(BP)
- 分别统计正向和负向变化
- 找到累计达到90%总变动所需的天数
- 指标值越小表示行情突然性越强

### 行情阶段划分

使用 `scipy.signal.find_peaks` 识别收益率曲线的峰谷:
- 10年国债: prominence=25BP, min_distance=80天
- 1年国债: prominence=15BP, min_distance=60天

### 策略模拟

**规则策略**:
- 当收益率上涨超过阈值 -> 加仓
- 当收益率下跌超过阈值 -> 减仓
- 参数优化遍历多种组合

**买入持有基准**:
- 首日建仓100%并持有至期末

## 输出结果

### 数据库表
- `bond.market_concentration_90pct`: 90%行情集中度指标

### 分析图表
- 收益率走势图
- 90%行情时间分布图
- 年度策略表现分布图
- 历史策略表现汇总对比图

### CSV文件
- 行情阶段集中度分析
- 策略优化结果
- 年度对比分析汇总

## 质量控制指标

- 短期预测准确率: >=70%
- 中期预测准确率: >=65%
- VaR覆盖率: >=95%
- 最大回撤: <=5%

## 注意事项

1. 数据库密码通过环境变量配置，避免硬编码
2. 首次运行需要设置中文字体支持
3. 批量历史更新可能耗时较长

## 维护信息

- **负责人**: 量化研究员/风险分析师
- **执行频率**: 每周/每月
- **最后更新**: 2026-02-14
