# T34 - 债券新发行

## 项目概述

债券新发行系统是一个综合性的债券一级市场数据采集和分析工具，主要功能包括：

1. **债券到期数据采集**：从Wind API获取各种类型债券的发行和到期数据
2. **债券新发行分析**：从同花顺iFinD API获取新发债券的详细信息
3. **数据存储与管理**：将数据存储到MySQL数据库，支持动态列管理
4. **数据去重与清洗**：自动识别和删除重复数据

## 数据源

| 数据源 | API | 用途 | 数据表 |
|--------|-----|------|--------|
| Wind | `w.wset()` | 债券发行和到期数据 | 债券到期 |
| 同花顺iFinD | `THS_DR()` | 债券新发行详情 | 债券新发行1 |

## 项目结构

```
T34-债券新发行/
├── 重构.ipynb              # 主重构Notebook
├── config.py               # 配置参数
├── requirements.txt        # Python依赖列表
├── README.md               # 项目说明
├── main.py                 # 主执行脚本
├── src/                    # 原始代码文件备份
│   ├── zqdq.py            # 债券到期数据采集
│   ├── zqfx.py            # 债券新发行数据采集
│   └── SELECT.sql         # SQL查询语句
├── data/                   # 数据文件
├── assets/                 # 图片等资源
└── output/                 # 输出目录
```

## 核心功能模块

### 模块一：债券到期数据采集 (zqdq.py)

- **数据源**: Wind API
- **时间范围**: 未来7天
- **债券类型**: 27种（国债、央行票据、存单、企业债、公司债等）
- **输出字段**: dt(日期), totalredemption(总兑付金额), bondtype(债券类型), isurbanincestmentbonds(是否城投)

### 模块二：债券新发行数据采集 (zqfx.py)

- **数据源**: 同花顺iFinD API (接口: p04524)
- **时间范围**: 未来1-30天
- **输出字段**: trade_code(债券代码), sec_name(债券名称), dt(发行日期), planissueamount(计划发行量), bondterm(期限), bondtype(债券类型), isurbanincestmentbonds(是否城投)
- **特殊处理**: 债券名称去重（保留非S开头代码）

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 数据库配置
export MYSQL_HOST=your_host
export MYSQL_PORT=3306
export MYSQL_USER=your_username
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=yq

# API配置
export IFIND_USERNAME=your_ifind_username
export IFIND_PASSWORD=your_ifind_password
```

### 3. Wind API

确保已安装Wind金融终端，并正确配置WindPy。

## 使用方法

### 方式一：直接运行主脚本

```bash
python main.py
```

### 方式二：使用Jupyter Notebook

```bash
jupyter notebook 重构.ipynb
```

### 方式三：分别运行各模块

```python
# 债券到期数据采集
python src/zqdq.py

# 债券新发行数据采集
python src/zqfx.py
```

## 核心工具函数

### generate_column_mapping(columns)
生成列名映射，将中文列名映射为col_0, col_1...用于数据库操作

### change_column_names(table_name, column_mapping, to_english=True)
动态修改表列名（中文<->英文）

### pro_data(wsd_data, table_name)
数据处理+动态表结构+批量插入

## 债券类型列表

| # | Wind类型 | 中文名称 | 是否城投 |
|---|----------|----------|----------|
| 1 | governmentbonds | 国债 | 否 |
| 2 | centralbankbills | 央行票据 | 否 |
| 3 | cds | 存单 | 否 |
| 4 | commercialbankbonds | 普通金融债 | 否 |
| 5 | policybankbonds | 政策银行债 | 否 |
| 6 | commercialbanksubordinatedbonds | 商业银行次级债券 | 否 |
| 7 | insurancecompanybonds | 保险债 | 否 |
| 8 | corporatebondsofsecuritiescompany | 证券公司债 | 否 |
| 9 | securitiescompanycps | 证券公司短融债 | 否 |
| 10 | otherfinancialagencybonds | 其他金融机构债 | 否 |
| 11 | enterprisebonds | 企业债 | 是/否 |
| 12 | corporatebonds | 公司债 | 是/否 |
| 13 | medium-termnotes | 中期票据 | 是/否 |
| 14 | cps | 短期融资券 | 是/否 |
| 15 | projectrevenuenotes | 项目收益票据 | 否 |
| 16 | ppn | PPN | 是/否 |
| 17 | supranationalbonds | 国际机构债 | 否 |
| 18 | agencybonds | 政府支持机构债 | 否 |
| 19 | standardizednotes | 标准化票据 | 否 |
| 20 | abs | ABS | 否 |
| 21 | convertiblebonds | 可转债 | 否 |
| 22 | exchangeablebonds | 可交换债 | 否 |
| 23 | detachableconvertiblebonds | 可分离转债 | 否 |

## 数据流程

```
zqdq.py:
  Wind API -> 27次调用/天 -> 列名转换 -> 入库 -> 表: 债券到期

zqfx.py:
  同花顺API -> 单次调用 -> 列名转换 -> 入库 -> 去重 -> 表: 债券新发行1
```

## 运行建议

| 脚本 | 建议频率 | 运行时间 |
|------|---------|---------|
| zqdq.py | 每日 | 16:00-18:00 |
| zqfx.py | 每日 | 16:00-18:00 |

## 注意事项

1. **API依赖**: 需要安装Wind终端和同花顺iFinD客户端
2. **密码安全**: 所有敏感信息通过环境变量配置，禁止硬编码
3. **数据去重**: zqfx.py执行后自动进行债券名称去重
4. **列名转换**: 数据库操作时进行中英文列名转换以保证兼容性

## 更新日志

- 2025-02-15: 初始重构版本
