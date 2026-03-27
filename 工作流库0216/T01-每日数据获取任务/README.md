# T01-每日数据获取任务

## 概述

每日数据获取是债券研究的核心基础设施，包含THS（同花顺）期货债券数据、可转债数据、债券指数等关键数据的自动采集和更新。

**任务ID**: T01
**优先级**: 最高
**执行频率**: 每日
**原始路径**: `代码库/daily/每日ths取数（最新）/`

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**: THS API (iFinDPy) 需要单独安装，请联系同花顺获取安装包。

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# MySQL 数据库配置
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password

# PostgreSQL 数据库配置
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# THS API 账户配置
THS_USER=your_ths_account
THS_PASSWORD=your_ths_password
```

### 3. 运行Notebook

```bash
jupyter notebook 重构.ipynb
```

## 文件结构

```
T01-每日数据获取任务/
├── 重构.ipynb        # 主重构Notebook
├── config.py         # 配置文件
├── requirements.txt  # 依赖列表
├── .env              # 环境变量（敏感信息）
├── README.md         # 本文件
├── src/              # 原始代码备份
│   ├── ths_bond.py
│   ├── hzcurve.py
│   ├── 可转债取数.py
│   └── ...
├── data/             # 数据文件
├── assets/           # 图片等资源
└── output/           # 输出目录
```

## 核心功能模块

### 1. THS数据获取
- 期货债券数据获取 (`ths_bond.py`)
- 可转债数据获取 (`可转债取数.py`)
- 债券基础信息获取 (`ths_bond_basicinfo.py`)

### 2. 收益率曲线计算
- HZ收益率曲线计算 (`hzcurve.py`)
- 长期收益率曲线 (`hzcurve_long.py`)
- 基础曲线构建 (`hzcurve_基础曲线构建.py`)

### 3. 数据库操作
- MySQL数据操作
- PostgreSQL数据迁移 (`basicinfo_postgres.py`)

### 4. 债券指数更新
- 每日债券指数更新 (`2_daily_bond_index_update.py`)

## 数据源

| 数据源 | 类型 | 说明 |
|--------|------|------|
| THS API | 金融数据 | 同花顺iFinD接口，提供债券行情、基础信息等 |
| MySQL | 数据库 | 主数据库，存储债券行情和基础信息 |
| PostgreSQL | 数据库 | 时序数据库，存储分析结果 |

## 数据库表

### 主要表结构

- `bond.marketinfo_curve` - 债券曲线收盘价数据
- `bond.marketinfo_equity` - 可转债行情数据
- `bond.bond_basicinfo` - 债券基础信息
- `bond.hzcurve_*` - HZ收益率曲线计算结果

## 执行流程

1. **环境检查** (8:00-8:10)
   - 检查数据库连接
   - 检查THS API凭证

2. **THS债券数据获取** (8:10-9:00)
   - 获取期货债券数据
   - 获取可转债数据

3. **债券指数更新** (10:00-11:00)
   - 计算和更新债券指数

4. **收益率曲线计算** (11:00-12:00)
   - 计算各类收益率曲线

5. **数据入库** (13:00-14:00)
   - 数据迁移和存储

## 注意事项

1. **敏感信息保护**
   - 所有密码和密钥已移至 `.env` 文件
   - 请勿将 `.env` 提交到版本控制系统

2. **THS API依赖**
   - 需要安装同花顺iFinD客户端
   - 需要有效的THS账户

3. **大文件处理**
   - 大于10MB的数据文件未复制到 `data/` 目录
   - 请手动处理或使用数据库查询

## 原始脚本清单

| 序号 | 脚本名称 | 功能 |
|------|---------|------|
| 1 | ths_bond.py | THS期货债券数据获取 |
| 2 | 可转债取数.py | 可转债数据获取 |
| 3 | ths_bond_basicinfo.py | 债券基础信息获取 |
| 4 | hzcurve.py | 收益率曲线计算 |
| 5 | hzcurve_long.py | 长期收益率曲线计算 |
| 6 | basicinfo_postgres.py | 数据迁移到PostgreSQL |
| 7 | 2_daily_bond_index_update.py | 每日债券指数更新 |
| 8 | sql_conns_new.py | 数据库连接配置 |

---

*任务ID: T01*
*创建时间: 2026-02-14*
*本文档基于代码分析生成*
