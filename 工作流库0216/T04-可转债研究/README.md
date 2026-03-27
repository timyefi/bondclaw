# T04 - 可转债研究

可转债研究是一个综合性的债券分析项目，专注于可转债的数据采集、分析和策略研究。

## 项目概述

本项目提供以下功能：
- 从同花顺iFinD采集可转债实时行情数据
- 构建多维度指数体系（Nature、Premium、Industry）
- 进行可转债投资策略研究
- 生成可视化分析报告

## 目录结构

```
T04-可转债研究/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   ├── 可转债计算.py
│   ├── 可转债取数.py
│   ├── bond_data_collector.py
│   ├── db_pool.py
│   └── ...
├── data/              # 数据文件
│   ├── raw/           # 原始数据
│   └── processed/     # 处理后数据
├── assets/            # 图片等资源
├── output/            # 输出目录
└── cache/             # 缓存目录
```

## 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果遇到权限问题，使用以下命令
pip install --user -r requirements.txt
```

## 配置说明

### 环境变量配置

在运行前，请设置以下环境变量：

```bash
# Linux/macOS
export DB_PASSWORD="your_db_password"
export THS_USERNAME="your_ths_username"
export THS_PASSWORD="your_ths_password"

# Windows
set DB_PASSWORD=your_db_password
set THS_USERNAME=your_ths_username
set THS_PASSWORD=your_ths_password
```

或者直接修改 `config.py` 中的默认值。

### 数据库配置

项目默认连接以下数据库：
- 主机: `rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com`
- 端口: `3306`
- 数据库: `yq`

### 同花顺iFinD配置

如需使用同花顺数据采集功能，需要：
1. 安装同花顺iFinD客户端
2. 安装iFinDPy Python接口
3. 配置有效的账号密码

## 使用方法

### 1. 运行Jupyter Notebook

```bash
cd T04-可转债研究
jupyter notebook 重构.ipynb
```

### 2. 主要功能模块

#### 数据采集
```python
from src.bond_data_collector import THSBondDataCollector

collector = THSBondDataCollector()
collector.collect_historical_data(days=365)
```

#### 指数计算
```python
# 生成历史指数
results = generate_historical_index('2020-01-01', '2024-12-31')
```

## 指数体系说明

### 1. Nature类指数（债性分类）

基于纯债溢价率分类：
- **偏债型**: 纯债溢价率 < -10%
- **平衡型**: -10% <= 纯债溢价率 <= 10%
- **偏股型**: 纯债溢价率 > 10%

### 2. Premium类指数（溢价分类）

基于价格和转股溢价率分类：
- **双低**: 价格 <= 110 且 转股溢价率 <= 20%
- **低价高溢**: 价格 <= 110 且 转股溢价率 > 20%
- **高价低溢**: 价格 > 110 且 转股溢价率 <= 20%
- **双高**: 价格 > 110 且 转股溢价率 > 20%

### 3. Industry类指数（行业分类）

按照正股所属的申万一级行业分类构建指数。

## 数据库表结构

### marketinfo_equity1（可转债行情）
| 字段 | 类型 | 说明 |
|------|------|------|
| dt | DATE | 日期 |
| trade_code | VARCHAR(20) | 转债代码 |
| close | DECIMAL(10,4) | 收盘价 |
| amount | DECIMAL(20,4) | 成交额 |
| pure_premium | DECIMAL(10,4) | 纯债溢价率 |
| conv_premium | DECIMAL(10,4) | 转股溢价率 |

### marketinfo_ebindex（指数行情）
| 字段 | 类型 | 说明 |
|------|------|------|
| trade_code | VARCHAR(20) | 指数代码 |
| dt | DATE | 日期 |
| close | DECIMAL(10,4) | 指数收盘价 |
| component_count | INT | 样本数量 |

## 常用命令

```bash
# 运行数据采集
python src/bond_data_collector.py

# 运行指数计算
python src/可转债计算.py

# 导出数据
python -c "from 重构 import export_to_parquet; export_to_parquet(df, 'output.parquet')"
```

## 依赖项目

- Python 3.8+
- pandas
- numpy
- pymysql
- SQLAlchemy
- matplotlib
- tqdm

## 注意事项

1. **数据安全**: 请勿在代码中硬编码密码，使用环境变量或配置文件
2. **API限制**: 同花顺API有请求频率限制，请注意控制请求速度
3. **数据完整性**: 建议定期备份数据到本地Parquet文件

## 更新日志

- 2026-02-14: 初始版本，完成项目重构

## 联系方式

如有问题，请联系项目负责人。
