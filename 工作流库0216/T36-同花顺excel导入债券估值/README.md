# T36 - 同花顺Excel导入债券估值数据

## 项目概述

本项目是一个**同花顺iFinD债券估值批量处理系统**，主要用于从同花顺Excel插件批量获取债券估值数据并导入数据库。

### 核心功能

1. **批量生成Excel模板**：从数据库查询日期+债券代码组合，生成Excel模板文件
2. **批量填充iFinD公式**：在Excel模板中批量插入同花顺iFinD数据提取公式
3. **批量计算并保存为值**：执行Excel公式计算，将结果保存为静态值
4. **数据验证与入库**：验证数据质量并回传数据库

### 数据指标

| 指标 | 说明 |
|------|------|
| ths_bond_balance_bond | 债券余额 |
| ths_evaluate_yield_yy_bond | 银行间估值收益率 |
| ths_cb_market_implicit_rating_bond | 隐含评级 |
| ths_evaluate_yield_cb_bond_exercise | 交易所估值收益率 |
| ths_evaluate_modified_dur_cb_bond_exercise | 修正久期 |

## 目录结构

```
T36-同花顺excel导入债券估值等/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── 批量获得excel表格所需dttradecode.txt
│   ├── 批量excel填充自定义公式.txt
│   └── 批量excel计算及保存为值.txt
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 环境要求

- Python 3.8+
- Microsoft Excel（用于公式计算，仅Windows）
- 同花顺iFinD Excel插件
- MySQL数据库

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 环境变量

在运行前，需要设置以下环境变量：

```bash
# 数据库配置
export DB_HOST=your_database_host
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=bond

# 同花顺配置
export IFIND_USERNAME=your_ifind_username
export IFIND_PASSWORD=your_ifind_password
```

或在项目根目录创建 `.env` 文件：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=bond
```

### 配置参数

主要配置参数位于 `config.py`：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| EXCEL_ROW_LIMIT | 每个Excel文件最大行数 | 300000 |
| IFIND_WAIT_TIME | iFinD数据加载等待时间(秒) | 60 |
| MAX_RETRIES | 最大重试次数 | 5 |
| RETRY_DELAY | 重试间隔(秒) | 30 |

## 使用方法

### 方式一：使用Jupyter Notebook

```bash
# 启动Jupyter
jupyter notebook 重构.ipynb
```

### 方式二：命令行执行

```python
from config import *
# 导入并执行主流程
```

## 执行流程

```
1. 查询债券数据
   └─ 从数据库查询指定日期内存续的债券代码

2. 生成Excel模板
   └─ 按日期+债券代码生成Excel文件（每30万行一个文件）

3. 填充iFinD公式
   └─ 在Excel中批量插入同花顺数据提取公式

4. Excel计算（仅Windows）
   └─ 打开Excel执行公式计算，等待数据加载
   └─ 将公式结果保存为静态值

5. 数据验证
   └─ 检查数据完整性和合理性

6. 数据入库
   └─ 将验证通过的数据写入数据库
```

## 数据筛选逻辑

债券存续期筛选条件：
- 起息日 < 当前日期（或为空/0000-00-00）
- 到期日 > 当前日期（或为空/0000-00-00）
- 退市日 > 当前日期（或为空/0000-00-00）
- 非发行失败债券

## 注意事项

1. **Windows环境**：Excel计算功能需要在Windows环境下运行，并安装Microsoft Excel
2. **iFinD插件**：需要预先安装同花顺iFinD Excel插件并登录
3. **等待时间**：iFinD数据加载需要时间，默认等待60秒
4. **大文件处理**：单文件超过30万行会自动分割为多个文件
5. **重试机制**：Excel COM接口可能不稳定，已内置重试机制

## 常见问题

### Q: Excel计算失败？
A: 检查是否正确安装了Microsoft Excel和iFinD插件，确保iFinD已登录

### Q: 数据库连接失败？
A: 检查环境变量配置是否正确，确保数据库服务正常运行

### Q: iFinD数据未加载？
A: 尝试增加 `IFIND_WAIT_TIME` 配置值

## 更新日志

- 2026-02-15: 初始版本，完成重构
