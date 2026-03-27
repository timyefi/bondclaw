# T38 - 年报处理

## 项目概述

年报处理项目专注于收集、解析和分析企业年度报告，包括财务报表、管理层讨论与分析、公司治理等信息，为基本面分析、信用评估和投资决策提供重要参考。

### 核心功能

1. **年报PDF下载** - 从企业预警通网站爬取企业年报PDF文件
2. **OCR处理** - 批量OCR处理PDF文件，转换为文本
3. **大模型提取** - 使用通义千问大模型从OCR结果中提取关键财务信息
4. **数据库存储** - 将提取结果存储到MySQL数据库

## 目录结构

```
T38-年报处理/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   ├── 企业预警通爬取年报.ipynb
│   ├── 批量处理年报pdf.ipynb
│   ├── 结合大模型提取.ipynb
│   ├── 检查文件是否已经全部ocr.ipynb
│   └── 提取年报url.ipynb
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 数据流

```
数据库查询公司信息 -> 企业预警通API -> 下载PDF -> OCR处理 -> 通义千问API -> 数据库
     ↓                  ↓            ↓         ↓           ↓          ↓
  公司列表          年报URL列表    PDF文件    文本文件    财务数据    提取结果
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件:

```env
# 数据库配置
DB_YQ_USER=your_username
DB_YQ_PASSWORD=your_password
DB_YQ_HOST=rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com
DB_YQ_PORT=3306
DB_YQ_DATABASE=yq

# 通义千问API
QWEN_API_KEY=your_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 百度OCR (可选)
BAIDU_OCR_API_KEY=your_api_key
BAIDU_OCR_SECRET_KEY=your_secret_key
```

## 使用方法

### 方式一：运行Notebook

1. 打开 `重构.ipynb`
2. 按顺序执行各个单元格
3. 修改配置参数后执行主流程

### 方式二：使用原始模块

```bash
# 批量下载年报
python -c "from src.企业预警通爬取年报 import *; main()"

# OCR处理
python -c "from src.批量处理年报pdf import *; process_pdfs(folder_path)"

# 大模型提取
python -c "from src.结合大模型提取 import *; main()"
```

## 数据库表结构

### 输入表

| 表名 | 说明 |
|------|------|
| `yq.23年财报文件` | 年报文件记录 |
| `financialinfo.trade_code_temp1` | 债券代码临时表 |
| `bond.basicinfo_credit` | 债券基础信息 |

### 输出表

| 表名 | 说明 |
|------|------|
| `yq.23年财报挖掘` | 财务信息提取结果 |
| `yq.资本公积` | 资本公积信息 |
| `yq.年报提取结果` | 年报提取结果 |

## 提取的财务指标

- **股东分红**: 现金股利、永续债利息、可续期公司债利息等
- **资本公积增加**: 政府现金拨款、股权无偿划转、资产评估增值、项目移交等

## API参考

### 企业预警通API

- **地址**: `https://www.qyyjt.cn/getData.action`
- **请求方式**: POST
- **参数**:
  - `root_type`: 资源类型 (securities)
  - `skip`: 跳过条数
  - `pagesize`: 每页条数
  - `text`: 公司名称

### 通义千问API

- **地址**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **模型**: `qwen-long`
- **功能**: 文件上传、内容提取、文本生成

## 注意事项

1. **API限流**: 企业预警通和通义千问API可能有限流，代码中已添加随机延迟
2. **敏感信息**: 所有密码和密钥通过环境变量管理，请勿硬编码
3. **大文件处理**: 大文件OCR可能占用大量内存，建议分批处理
4. **错误恢复**: 单个文件失败不影响整体，支持断点续传

## 更新日志

- 2026-02-15: 初始重构版本

## 维护信息

- **任务ID**: T38
- **优先级**: 最高
- **执行频率**: 按季/每年
- **负责人**: 基本面分析师/信用分析师
