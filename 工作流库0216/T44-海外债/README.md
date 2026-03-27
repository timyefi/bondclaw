# 海外债项目

## 项目概述

本项目用于海外债数据的获取、处理、存储和分析。

## 功能特性

- 海外债数据采集（支持Wind、iFinD数据源）
- 数据清洗与验证
- 数据库存储与更新
- 数据去重处理
- 数据导出功能

## 目录结构

```
T44-海外债/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
├── data/              # 数据文件
├── assets/            # 图片等资源
│   └── 模板海外债.xlsx # Excel模板文件
└── output/            # 输出目录
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

```bash
# 数据库配置
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=yq

# iFinD配置（如需要）
IFIND_USER=your_ifind_user
IFIND_PASSWORD=your_ifind_password
```

## 使用方法

### 运行Notebook

1. 打开 `重构.ipynb`
2. 按顺序执行各单元格
3. 根据实际需求配置数据源和业务逻辑

### 主要模块

1. **数据获取**: `fetch_overseas_bond_data()` - 从数据源获取海外债数据
2. **数据清洗**: `clean_bond_data()` - 清洗和验证数据
3. **数据存储**: `upsert_data_to_db()` - 将数据存储到数据库
4. **数据去重**: `remove_duplicates()` - 删除重复数据

## 数据源

- Wind金融终端 (WindPy)
- 同花顺iFinD

## 输出

- 数据库表: `海外债数据`
- Excel文件: 可通过工具函数导出

## 注意事项

1. 首次使用需要配置数据库连接信息
2. Wind/iFinD接口需要相应账号权限
3. 敏感信息请使用环境变量配置

## 更新日志

- 2026-02-15: 初始版本，重构完成
