# T05 对冲策略

## 项目概述

本项目专注于债券或ETF的对冲策略分析，提供完整的对冲策略分析工具链，支持多种市场环境下的策略优化。

### 核心功能

- **市场环境分析**：波动率、相关性、趋势环境分析
- **历史场景识别**：识别历史上的类似市场环境
- **策略回测**：不同对冲比率的收益和风险分析
- **风险评估**：VaR、CVaR、最大回撤等风险指标计算
- **报告生成**：生成交互式HTML报告

## 目录结构

```
T05-对冲策略/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖
├── README.md          # 项目说明
├── src/               # 原始代码文件
│   └── 对冲策略报告生成.py
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 数据源

- MySQL数据库（marketinfo_fund表）
- Wind API（数据更新，可选）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 使用Notebook

打开 `重构.ipynb`，按顺序执行各个单元格。

### 2. 快速分析

```python
from config import get_database_url
# 运行快速分析
quick_analysis(
    trade_code1='511220.SH',  # 城投ETF
    trade_code2='518880.SH',  # 黄金ETF
    name1='城投ETF',
    name2='黄金ETF',
    shares1=10000,
    shares2=5000,
    cash=100000
)
```

## 策略说明

### 风险平价策略
- 基于各资产的波动率动态调整权重
- 当某个资产波动率升高时，自动降低其权重
- 目标：通过动态调整实现风险贡献的平衡

### 动态调整策略
- 综合考虑相关性、动量和波动率
- 在基准权重(60/40)基础上动态调整
- 调整范围：30%-80%之间

### 固定配置策略
- 维持固定的资产配置比例
- 定期进行再平衡以保持目标权重
- 提供70/30和50/50两种固定配置方案

## 配置说明

在 `config.py` 中可以配置：

- 数据库连接参数（建议使用环境变量存储密码）
- 分析参数（回测期间、异常值阈值等）
- 可视化参数（图表样式、颜色等）

## 环境变量

为保护敏感信息，建议设置以下环境变量：

```bash
export DB_HOST=your_database_host
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=your_database
```

## 输出结果

- 策略净值对比图表（PNG和HTML格式）
- 市场环境热力图
- 策略信号强度图
- 完整的HTML分析报告

## 注意事项

1. 本项目需要连接MySQL数据库获取市场数据
2. Wind API功能需要安装Wind终端（可选）
3. 首次运行前请确保已安装所有依赖
4. 数据库密码等敏感信息请使用环境变量配置

## 维护信息

- **创建日期**: 2026-02-14
- **最后更新**: 2026-02-14
- **负责人**: 量化研究员
