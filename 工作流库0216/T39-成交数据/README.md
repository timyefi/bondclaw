# T39 - 成交数据

## 项目概述

成交数据项目专注于收集、处理和分析债券市场的成交数据，包括成交量、成交金额、成交价格、成交结构等，为市场流动性分析、交易策略制定和投资决策提供数据支持。

## 功能特性

- **数据采集**: 从评级狗(ratingdog.cn)获取债券成交历史数据
- **中介成交**: 获取中介成交历史数据
- **全部成交**: 获取全部成交历史数据（包括非中介）
- **分页获取**: 支持大数据量分页获取
- **数据库存储**: 自动存储到MySQL数据库

## 目录结构

```
T39-成交数据/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   ├── YY成交中介.ipynb
│   └── YY成交全部.ipynb
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

在执行前需要设置以下环境变量：

```bash
# 数据库配置
export DB_HOST=your_db_host
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=yq

# 评级狗API配置
export RATINGDOG_USERNAME=your_username
export RATINGDOG_PASSWORD=your_password
export RATINGDOG_TENANT_ID=114
```

## 使用方法

### 方式一：使用重构Notebook

```bash
jupyter notebook 重构.ipynb
```

### 方式二：查看原始代码

原始代码位于 `src/` 目录：
- `YY成交中介.ipynb`: 中介成交数据采集
- `YY成交全部.ipynb`: 全部成交数据采集

## 核心流程

```
数据库查询日期范围 -> 评级狗API登录 -> 分页获取成交数据 -> 存储数据库
        ↓                  ↓                  ↓               ↓
    abs表日期         accessToken        items[]         yq.cjqb表
```

## 数据库表

### 输入表
- `bond.marketinfo_abs` - ABS市场信息表（获取日期范围）

### 输出表
- `yq.cjqb` - 成交数据表（全部成交）
- `yq.cj` - 成交数据表（中介成交）

## API说明

### 登录API
- **地址**: `https://auth.ratingdog.cn/api/TokenAuth/Authenticate`
- **方式**: POST
- **返回**: accessToken

### 成交数据API
- **地址**: `https://host.ratingdog.cn/api/services/app/Bond/QueryTradedHistoricalOfFrontDeskTenants`
- **方式**: POST
- **分页**: 每页最多150条记录

## 注意事项

1. API有请求频率限制，建议添加适当延迟
2. 大数据量获取时注意内存管理
3. 网络异常时实现了自动重试机制
4. 敏感信息通过环境变量配置，请勿硬编码

## 更新日志

- 2026-02-15: 完成项目重构，规范化代码结构

## 负责人

数据分析师/量化研究员
