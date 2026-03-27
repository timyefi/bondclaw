# T02-每日脚本任务

## 概述

每日脚本是债券研究的基础设施，包含定时数据获取、指标计算、报告生成等核心功能。共包含20+个脚本，按功能分为数据获取、指标计算、行为分析、工具脚本四大类。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 数据库配置
export DB_HOST=your_host
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=bond

# THS API配置
export THS_USERNAME=your_ths_username
export THS_PASSWORD=your_ths_password
```

### 3. 运行Notebook

```bash
jupyter notebook 重构.ipynb
```

## 文件结构

```
T02-每日脚本任务/
├── 重构.ipynb        # 主重构Notebook
├── config.py         # 配置文件
├── requirements.txt  # 依赖列表
├── README.md         # 本文件
├── src/              # 原始代码备份
├── data/             # 数据文件
└── output/           # 输出目录
```

## 脚本分类

### 数据获取脚本（7个）

| 脚本 | 功能 | 执行时间 |
|------|------|---------|
| td.py | 土地数据获取 | 01:00 |
| thslc.py | THS理财数据获取 | 09:00, 19:30 |
| tzzxw.py | THS资讯数据获取 | 19:30, 23:30 |
| xyzgm.py | THS公告数据获取 | 02:00, 20:00 |
| yyxt.py | THS研报数据获取 | 06:00 |
| zhaishiguimo.py | 实时资讯获取 | 06:00, 20:00, 21:00 |
| zqdq.py | 定向数据获取 | 20:30, 21:00 |

### 指标计算脚本（7个）

| 脚本 | 功能 | 执行时间 |
|------|------|---------|
| cind.py | 行业数据计算 | 11:00 |
| cyhs.py | 宏观数据处理 | 03:30 |
| cyzgz.py | 中观数据处理 | 按需 |
| jrzyq.py | 金融市场数据计算 | 23:30, 24:00 |
| qxqyb.py | 债券指数计算 | 06:00 |
| yhzf.py | 宏观趋势分析 | 18:00, 19:00 |
| yjfxct.py | 金融衍生品分析 | 17:00, 18:30, 20:00, 21:00 |

### 行为分析脚本（4个）

| 脚本 | 功能 | 执行时间 |
|------|------|---------|
| yuqing.py | 投资者情绪分析 | 05:30, 20:00, 21:00, 21:30 |
| yycjqb.py | 每小时行为分析 | 22:00-23:00 每10分钟 |
| licaishouyi.py | 离岸资金分析 | 09:00, 15:00, 19:00, 20:00, 21:00 |
| zqfx.py | 资金流向分析 | 20:30, 21:00 |

### 工具脚本（2个）

| 脚本 | 功能 |
|------|------|
| sample_index.py | 样本指数计算 |
| 理财更新.py | 理财产品数据更新 |

## 数据源

- **THS API**: 同花顺数据接口（股票、债券、基金、理财等）
- **土地数据API**: landchina.com土地交易数据
- **MySQL数据库**: 本地数据存储

## 自动化执行

### 方式1: Python调度器

```python
import schedule
import time

def run_td():
    # 执行td.py
    pass

schedule.every().day.at("01:00").do(run_td)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 方式2: Crontab

```bash
0 1 * * * cd /path/to/scripts && python td.py
0 9 * * * cd /path/to/scripts && python thslc.py
```

## 注意事项

1. 运行前确保数据库连接配置正确
2. THS API需要有效的账号密码
3. 部分脚本需要代理支持
4. 敏感信息请使用环境变量
5. 建议使用日志监控脚本执行状态

---

*任务ID: T02*
*创建时间: 2026-02-14*
