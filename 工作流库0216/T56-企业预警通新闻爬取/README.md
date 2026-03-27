# T56-企业预警通新闻爬取

## 项目简介

本项目用于从企业预警通(www.qyyjt.cn)爬取新闻数据并存储到数据库。

## 功能特性

- 定时爬取新闻数据
- 支持多种新闻类型
- 自动去重和数据清洗
- 批量存储到数据库

## 目录结构

```
T56-企业预警通新闻爬取/
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

1. 配置环境变量设置登录token
2. 运行 `重构.ipynb` 中的各章节

## 环境变量

- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `QYYJT_PC_USS`: 企业预警通登录token

## API说明

新闻数据通过POST请求获取：
- URL: `https://www.qyyjt.cn/getData.action`
- 参数:
  - `bdate`: 开始时间
  - `edate`: 结束时间
  - `pagesize`: 每页数量
  - `skipParam`: 跳过数量
  - `subType`: 新闻子类型
  - `topicCode`: 主题代码

## 更新日志

- 2024-10: 初始版本
