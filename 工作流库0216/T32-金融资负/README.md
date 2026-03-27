# T32 金融资负

金融机构资产负债数据获取和处理模块。

## 项目概述

本项目用于获取和处理金融机构资产负债表数据，支持从Wind和同花顺数据源获取数据，并提供数据清洗和存储功能。

### 主要功能

1. **金融资负数据获取** - 从Wind EDB和同花顺EDB接口获取数据
2. **基金净申购数据** - 每日更新基金净申购数据
3. **数据清洗处理** - 清理重复数据，确保数据质量
4. **数据存储管理** - 将处理后的数据存储到MySQL数据库

### 应用场景

- 银行业研究
- 金融机构分析
- 宏观经济研究

## 项目结构

```
T32-金融资负/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── 金融资负取数.py
│   ├── 金融资负取数_简化版.py
│   ├── 清理金融资负表重复数据_最终版.py
│   └── README_简化版.md
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 数据更新策略

| 数据类型 | 更新频率 | 更新时间窗口 |
|---------|---------|-------------|
| 金融资负数据 | 每月一次 | 每月20-30号更新上月数据 |
| 基金净申购数据 | 每日 | 每天更新当日数据 |

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# Linux/Mac
export DB_PASSWORD="your_password"
export THS_USER="your_ths_user"
export THS_PASSWORD="your_ths_password"

# Windows
set DB_PASSWORD=your_password
set THS_USER=your_ths_user
set THS_PASSWORD=your_ths_password
```

### 3. 运行程序

```bash
# 使用Jupyter Notebook
jupyter notebook 重构.ipynb

# 或直接运行简化版脚本
python src/金融资负取数_简化版.py
```

## 配置说明

### 数据库配置

| 配置项 | 环境变量 | 默认值 |
|-------|---------|-------|
| 主机 | DB_HOST | rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com |
| 端口 | DB_PORT | 3306 |
| 用户 | DB_USER | hz_work |
| 密码 | DB_PASSWORD | (必须设置) |
| 数据库 | DB_NAME | yq |

### 更新策略配置

| 配置项 | 环境变量 | 默认值 |
|-------|---------|-------|
| 更新开始日期 | UPDATE_START_DAY | 20 |
| 更新结束日期 | UPDATE_END_DAY | 30 |
| API调用间隔 | API_CALL_INTERVAL | 0.1 |

## 数据源说明

### Wind EDB接口

- 提供宏观经济数据、金融数据等
- 需要安装WindPy客户端
- 数据代码格式：M开头（如M0001538）
- 支持约190个数据指标

### 同花顺EDB接口

- 提供经济数据
- 需要安装iFinDPy
- 数据代码格式：S开头（如S004345997）
- 支持5个数据指标

## 数据库表结构

### 金融资负表

| 字段 | 类型 | 说明 |
|-----|------|-----|
| dt | DATE | 日期（主键） |
| {指标代码} | FLOAT | 各金融指标值 |

### 基金净申购表

| 字段 | 类型 | 说明 |
|-----|------|-----|
| dt | DATE | 日期 |
| trade_code | VARCHAR | 基金代码 |
| 净申购 | FLOAT | 净申购金额 |

## 常见问题

### 1. 数据没有更新

- 检查是否在更新期间（20-30号）
- 检查API接口是否正常
- 检查数据库连接是否正常

### 2. 重复数据问题

- 使用清理脚本处理重复数据
- 程序会自动保留每月最后一天的数据

### 3. 数据源连接失败

- 确认Wind/同花顺客户端已安装并登录
- 检查网络连接

## 维护说明

### 添加新的数据代码

1. Wind数据：添加到 `WIND_CODES` 列表
2. 同花顺数据：添加到 `THS_CODES` 列表

### 修改更新时间

修改 `is_update_period()` 函数中的日期判断逻辑，或设置环境变量 `UPDATE_START_DAY` 和 `UPDATE_END_DAY`。

---

*生成时间: 2026-02-15*
