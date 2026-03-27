# 可转债数据采集

## 项目概述

本项目用于采集和管理可转债市场数据，从同花顺(iFinD)数据接口获取可转债行情数据并存储到MySQL数据库。

## 功能特性

- 从同花顺iFinD数据接口获取可转债行情数据
- 支持历史数据采集和数据补充
- 将数据存储到MySQL数据库
- 提供交易日历管理功能
- 支持批量数据处理

## 数据指标

采集的指标包括：
- 收盘价 (close)
- 成交额 (amount)
- 纯债溢价率 (pure_premium)
- 纯债到期收益率 (ytm)
- 转股溢价率 (conv_premium)
- 转股市盈率 (conv_pe)
- 正股市盈率 (stock_pe)
- 正股市净率 (stock_pb)
- 转股市净率 (conv_pb)
- 未转股余额 (un_conversion_balance)

## 目录结构

```
T24-可转债数据采集/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

```
# 数据库配置
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=bond

# 同花顺数据接口配置
THS_USERNAME=your_ths_username
THS_PASSWORD=your_ths_password
```

### 3. 安装同花顺数据接口

同花顺iFinD数据接口需要单独安装，请联系同花顺获取安装包。

## 使用方法

### 运行Notebook

1. 打开 `重构.ipynb`
2. 按顺序执行各个单元格
3. 在执行数据采集前，确保已配置好同花顺账号

### 执行数据采集

```python
from config import *
from 重构 import BondDataCollector

# 创建采集器
collector = BondDataCollector()

# 连接同花顺
collector.connect()

# 采集历史数据
collector.collect_historical_data('2025-01-01', '2025-02-15')

# 断开连接
collector.disconnect()
```

## 数据库表结构

### marketinfo_equity1

可转债行情数据表，包含以下字段：
- dt: 日期
- trade_code: 可转债代码
- close: 收盘价
- amount: 成交额
- pure_premium: 纯债溢价率
- ytm: 纯债到期收益率
- conv_premium: 转股溢价率
- conv_pe: 转股市盈率
- stock_pe: 正股市盈率
- stock_pb: 正股市净率
- conv_pb: 转股市净率
- un_conversion_balance: 未转股余额

## 注意事项

- 请确保同花顺账号有足够的权限
- 数据采集过程中会自动进行本地备份
- 建议定期检查日志文件
- 敏感信息（密码、密钥）请使用环境变量配置

## 任务信息

- 任务ID: T24
- 任务名称: 可转债数据采集
- 创建时间: 2026-02-15
