# T37 - 同花顺Excel导入财务指标

## 项目概述

本项目专注于从同花顺iFinD API批量提取债券发行人财务指标数据，通过Excel模板生成、数据填充和批量计算，最终将数据导入PostgreSQL数据库并转换格式。

## 核心功能

1. **同花顺API批量提取**：从iFinD API提取150+个债券发行人财务指标
2. **Excel模板处理**：生成模板、填充日期、自动计算
3. **数据导入PostgreSQL**：批量导入数据并进行格式转换
4. **宽表转长表**：使用pandas melt函数转换数据格式

## 项目结构

```
T37-同花顺excel导入财务指标/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   ├── 1.ipynb
│   ├── 同花顺api批量提取.txt
│   ├── 批量excel自动填充内容.txt
│   ├── 批量excel计算及保存为值.txt
│   ├── excel数据批量导入到postgres.txt
│   └── 批量excel填充自定义公式.txt
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 数据源

- **同花顺iFinD API**：通过`THS_BD()`函数提取财务指标
- **MySQL数据库**：bond、yq库（债券基础信息）
- **PostgreSQL数据库**：tsdb库（财务指标存储）

## 输出结果

- **指标数据3表**：宽表格式（thscode, dt, 指标1, 指标2, ..., 指标150+）
- **指标数据4表**：长表格式（dt, trade_code, 指标, value）

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

```bash
# MySQL配置
MYSQL_BOND_PASSWORD=your_password
MYSQL_YQ_PASSWORD=your_password

# PostgreSQL配置
POSTGRES_PASSWORD=your_password

# 同花顺API配置
THS_USERNAME_1=your_username
THS_PASSWORD_1=your_password
```

### 3. 安装同花顺iFinD客户端

iFinDPy库需要从同花顺官方安装，不在PyPI上。

## 使用方法

### 方法一：使用Notebook

打开 `重构.ipynb` 并按顺序执行各单元格。

### 方法二：模块化调用

```python
from config import *
from 重构 import *

# 1. 初始化数据库连接
db_tsdb = DatabaseManager(
    db_type='postgresql',
    host=PG_HOST,
    port=PG_PORT,
    user=PG_USER,
    password=PG_PASSWORD,
    database=PG_DB
)

# 2. 获取发行人代码
trade_codes = get_issuer_trade_codes(db_tsdb)

# 3. 批量提取财务指标
dates = [('20230630', '2023-06-30'), ('20221231', '2022-12-31')]
batch_extract_financial_indicators(trade_codes, dates, INDICATORS_STR, db_tsdb)

# 4. 宽表转长表
wide_to_long_table(db_tsdb, '指标数据3', '指标数据4')
```

## 核心模块说明

### 模块一：同花顺API批量提取

- 从MySQL数据库查询债券发行人代码
- 调用iFinD API提取150+个财务指标
- 将数据写入PostgreSQL宽表

### 模块二：Excel批量自动填充

- 从文件名提取日期（格式：YYYYMMDD.xlsx）
- 自动填充日期列
- 自动填充公式

### 模块三：Excel数据批量导入PostgreSQL

- 批量读取Excel文件
- 导入到PostgreSQL表
- 列类型转换（VARCHAR -> FLOAT）
- 宽表转长表（melt操作）

### 模块四：Excel计算及保存为值

- 打开Excel文件执行公式计算
- 将公式结果保存为静态值

## 财务指标说明

项目支持150+个财务指标，主要包括：

### 资产负债表指标
- 总资产、流动资产、非流动资产
- 总负债、流动负债、非流动负债
- 所有者权益
- 负债比率、流动比率、速动比率

### 利润表指标
- 营业收入、营业成本、毛利润
- 营业利润、净利润
- EBIT、EBITDA
- 销售毛利率、营业利润率、净利率

### 现金流量表指标
- 经营活动现金流量
- 投资活动现金流量
- 筹资活动现金流量
- 自由现金流

### 财务比率指标
- ROE（净资产收益率）
- 资产负债率
- 经营性现金流比率

## 注意事项

1. **Windows环境**：Excel自动化功能（win32com）仅在Windows环境下可用
2. **iFinD账号**：需要有效的同花顺iFinD账号才能使用API功能
3. **数据库权限**：需要MySQL和PostgreSQL的读写权限
4. **大数据处理**：使用chunksize参数避免内存溢出

## 更新日志

- 2026-02-15: 初始版本，重构自原始代码库

## 维护者

数据工程师
