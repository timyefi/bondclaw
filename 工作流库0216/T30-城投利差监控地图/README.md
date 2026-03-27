# 城投利差监控地图

## 项目概述

本项目用于监控和展示各地区城投债利差数据，支持省级和市级数据的获取、处理和可视化。

### 主要功能

- **城投利差数据获取**：从数据库获取各地区城投债利差数据
- **区域利差分析**：支持省级和市级两个层级的利差分析
- **利差变化监控**：计算7天和1个月的利差变化
- **地图可视化数据生成**：生成符合地图可视化要求的数据格式

### 应用场景

- 城投债投资分析
- 区域风险评估
- 利差套利策略

## 项目结构

```
T30-城投利差监控地图/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── main.py                    # 主程序
│   ├── regional_spread_chart.py   # 区域利差图表
│   ├── run_query.py               # 数据查询
│   └── 图表js代码.js               # 前端图表代码
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

```bash
# MySQL (bond) 数据库配置
export BOND_DB_HOST=localhost
export BOND_DB_PORT=3306
export BOND_DB_NAME=bond
export BOND_DB_USER=your_username
export BOND_DB_PASSWORD=your_password

# PostgreSQL (tsdb) 数据库配置
export TSDB_HOST=localhost
export TSDB_PORT=5432
export TSDB_NAME=tsdb
export TSDB_USER=your_username
export TSDB_PASSWORD=your_password

# 业务参数
export TARGET_TERM=2
export START_DATE=2025-06-22
export END_DATE=2025-07-22
```

### 3. 运行Notebook

```bash
jupyter notebook 重构.ipynb
```

## 数据流程

1. **数据获取**：从PostgreSQL (tsdb) 数据库获取城投债曲线数据
2. **数据处理**：
   - 清理省份名称（移除行政区划后缀）
   - 计算加权平均收益率
   - 格式化输出数据
3. **数据输出**：生成CSV和JSON格式的结果文件

## 输出数据格式

### 省级数据 (province_spread)

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 省份名称（2字简称） |
| dt | string | 数据日期 |
| value | float | 利差值 |

### 市级数据 (city_spread)

| 字段 | 类型 | 说明 |
|------|------|------|
| PROVINCE | string | 省份名称 |
| DT | string | 数据日期 |
| CITY | string | 城市名称（2字简称） |
| CLOSE | float | 利差值 |

## 数据库表说明

| 表名 | 数据库 | 说明 |
|------|--------|------|
| hzcurve_credit | tsdb_pg | 城投债曲线数据 |
| tc最新所属曲线 | tsdb_pg | 债券曲线归属信息 |
| 曲线代码 | tsdb_pg | 曲线代码映射表 |
| basicinfo_xzqh_ct | tsdb_pg | 城投区域行政区划信息 |
| stock.temp_5843 | bond | 省级利差临时表 |
| stock.temp_5857 | bond | 市级利差临时表 |

## 注意事项

1. **数据库连接**：需要确保能够访问MySQL (bond) 和 PostgreSQL (tsdb) 数据库
2. **省份名称处理**：内蒙古和黑龙江需要特殊处理（3字简称）
3. **日期排除**：某些特殊日期（如2023-01-03, 2023-05-10）需要从数据中排除

## 更新日志

- 2025-07-22: 初始版本，完成基本功能重构
- 2026-02-15: 项目重构，生成标准化Notebook结构

## 作者

工作台自动化团队
