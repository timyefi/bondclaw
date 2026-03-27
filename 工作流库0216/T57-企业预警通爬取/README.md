# T57-企业预警通爬取

## 项目简介

本项目是一个用于爬取企业预警通(www.qyyjt.cn)网站数据的爬虫框架，支持API和Selenium两种方式。

## 功能特性

- 支持API方式爬取
- 支持Selenium方式爬取
- 内置登录和token管理
- 自动处理请求重试
- 随机延时避免反爬
- 完整的日志记录
- 数据导出功能

## 目录结构

```
T57-企业预警通爬取/
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

1. 配置环境变量设置登录凭据
2. 运行 `重构.ipynb` 中的各章节

## 环境变量

- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `QYYJT_USERNAME`: 企业预警通用户名
- `QYYJT_PASSWORD`: 企业预警通密码

## 支持的数据模块

- 市场化经营主体
- 退出平台
- 市场化经营

## 注意事项

1. 请合理控制爬取频率
2. 建议使用代理IP池
3. 定期检查token有效性
4. 遵守网站的robots.txt规则

## 更新日志

- 2024-03: 初始版本
