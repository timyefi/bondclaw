# T54-产业高频跟踪

## 项目简介

本项目用于跟踪和分析各行业的高频指标，通过小波分析计算行业景气度分位点和趋势方向。

## 功能特性

- 多行业高频指标数据采集
- 小波分析计算周期分位点
- 行业景气度趋势判断
- 可视化展示和分析

## 目录结构

```
T54-产业高频跟踪/
├── 重构.ipynb          # 主Notebook
├── config.py           # 配置文件
├── requirements.txt    # 依赖包
├── README.md           # 说明文档
├── src/                # 源代码
├── data/               # 数据目录
├── assets/             # 资源文件
└── output/             # 输出目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 配置环境变量设置数据库连接信息
2. 运行 `重构.ipynb` 中的各章节

## 环境变量

- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `PG_HOST`: PostgreSQL主机
- `PG_PORT`: PostgreSQL端口
- `PG_USER`: PostgreSQL用户名
- `PG_PASSWORD`: PostgreSQL密码

## 更新日志

- 2024-01: 初始版本
