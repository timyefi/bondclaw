# 银行数据库 (T49)

## 项目概述

银行数据库是一个包含银行财务数据的Excel文件库，主要用于存储和管理各家银行的财务指标数据，为银行债定价模型、信用风险评估等分析提供数据支持。

## 功能特性

- **数据存储**：存储和管理各家银行的财务指标数据
- **数据导入**：将Excel数据导入到MySQL数据库
- **增量更新**：支持数据的增量更新机制
- **数据验证**：自动验证数据完整性和合理性
- **财务指标计算**：计算财务指标的期间变化

## 数据字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| dt1 | DATE | 日期 |
| 发行人 | VARCHAR(100) | 银行发行人名称 |
| 总资产 | DECIMAL(20,4) | 银行总资产（亿元） |
| 资本充足率 | DECIMAL(10,4) | 资本充足率（%） |
| 净息差 | DECIMAL(10,4) | 净利息收入与平均生息资产的比率（%） |
| 不良率 | DECIMAL(10,4) | 不良贷款率（%） |
| ROE | DECIMAL(10,4) | 净资产收益率（%） |
| 存款占比 | DECIMAL(10,4) | 存款占总负债的比例（%） |
| 拨备覆盖率 | DECIMAL(10,4) | 贷款损失准备金与不良贷款的比率（%） |

## 目录结构

```
T49-银行数据库/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── data/              # 数据文件
│   ├── 银行数据库2024.xlsx
│   ├── 银行.xlsx
│   └── 副本银行数据库2024 - 副本.xlsx
├── src/               # 原始代码文件备份（空）
├── assets/            # 图片等资源（空）
└── output/            # 输出目录（空）
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在运行前，需要配置以下环境变量：

```bash
# Linux/Mac
export DB_HOST=your_database_host
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=yq

# Windows PowerShell
$env:DB_HOST="your_database_host"
$env:DB_PORT="3306"
$env:DB_USER="your_username"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="yq"
```

### 3. 运行Notebook

使用Jupyter Notebook或JupyterLab打开`重构.ipynb`，逐单元格执行。

## 使用方法

### 数据导入

```python
from config import *
from sqlalchemy import create_engine

# 创建数据库连接
engine = create_engine(get_database_url())

# 读取Excel数据
import pandas as pd
df = pd.read_excel('data/银行数据库2024.xlsx')

# 导入到数据库
df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
```

### 数据查询

```python
# 查询银行数据
query = f"SELECT * FROM {TABLE_NAME} WHERE 发行人 = '工商银行'"
df = pd.read_sql_query(query, engine)
```

### 计算财务指标变化

```python
# 计算近1年变化
df['近1年总资产变化'] = df.groupby('发行人')['总资产'].transform(
    lambda x: x - x.shift(365)
)
```

## 数据更新频率

| 任务 | 建议频率 | 说明 |
|------|---------|------|
| 数据收集 | 每季度 | 银行财报季度更新 |
| 数据验证 | 每季度 | 收集数据后立即验证 |
| 数据库同步 | 每季度 | Excel更新后同步 |
| 备份 | 每次更新前 | 保存旧版本备份 |

## 数据质量保障

### 完整性检查
- 每家银行每个季度的数据是否完整
- 关键字段是否有缺失

### 合理性检查
- 资本充足率范围：0-50%
- 不良率范围：0-20%
- ROE范围：-50%到50%

## 相关任务

- **T48-银行回验**：使用银行数据库数据进行银行债定价模型训练

## 更新日志

- 2026-02-15：完成重构，创建Notebook和配置文件

---

**任务编号**: T49

**任务名称**: 银行数据库

**创建时间**: 2026-02-15
