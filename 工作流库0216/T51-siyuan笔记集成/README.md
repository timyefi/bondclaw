# siyuan笔记集成

将思源笔记（SiYuan Note）与AI模型结合的自动化工具。

## 功能概述

1. **AI问答集成**：在思源笔记中调用通义千问长上下文模型（qwen-long）
2. **文档智能分析**：上传文档到AI模型并提问
3. **自动追加内容**：将AI回答自动追加到思源笔记块中
4. **财报文件OCR处理**：批量下载财报PDF并进行OCR识别

## 目录结构

```
T51-siyuan笔记集成/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   ├── 1.js          # JavaScript版本AI问答脚本
│   └── siyuan笔记.ipynb  # 原始Notebook
├── data/              # 数据文件
├── assets/            # 图片等资源
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
# 通义千问API
DASHSCOPE_API_KEY=your_api_key_here

# 数据库配置
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=yq

# 思源笔记API
SIYUAN_API_BASE=http://127.0.0.1:6806

# 企业预警通API
QYWYT_TOKEN=your_token_here

# 文件路径
FOLDER_PATH=D:\2024年\财报文件
```

## 数据源

### 通义千问API

- **API地址**：`https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- **模型**：qwen-long（长上下文模型，支持文件上传）

### 思源笔记API

- **API端点**：`http://127.0.0.1:6806`
- **主要功能**：
  - `api/notebook/lsNotebooks`：获取笔记本列表
  - `api/filetree/createDocWithMd`：使用Markdown创建文档
  - `api/block/appendBlock`：追加内容块

### MySQL数据库

- **数据库**：yq
- **表**：23年财报文件
- **字段**：
  - `trade_code`：债券代码
  - `fileName`：文件名
  - `公司名称`：公司名称
  - `ocr`：OCR识别结果

## 使用方法

### 运行Notebook

1. 打开 `重构.ipynb`
2. 按顺序执行各个单元格
3. 确保思源笔记服务正在运行

### AI问答示例

```python
from config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL

# 简单问答
question = "请解释什么是特殊新增专项债"
answer = ask_model(question)

# 文档问答
file_id = "file-fe-1LuMGonfgr3qgC48dm40uBCU"
answer = ask_model(question, file_id=file_id)
```

### 追加到思源笔记

```python
# 将AI回答追加到思源笔记
parent_id = "your_block_id"
ask_and_append_to_siyuan(question, parent_id)
```

## 核心功能模块

### 1. AI问答模块

- `ask_model()`：调用通义千问API
- `ask_with_retry()`：带重试机制的问答
- `ask_about_document()`：针对文档提问

### 2. 思源笔记模块

- `get_siyuan_notebooks()`：获取笔记本列表
- `create_doc_with_md()`：创建文档
- `append_block()`：追加内容块
- `ask_and_append_to_siyuan()`：问答并追加

### 3. 财报处理模块

- `download_pdf()`：下载PDF文件
- `sanitize_filename()`：清理文件名
- `update_ocr_status()`：更新OCR状态

### 4. 舆情处理模块

- `get_public_opinion_detail()`：获取舆情详情
- `save_sentiment_to_db()`：保存舆情到数据库

## 安全注意事项

1. **不要将API密钥硬编码在代码中**
2. 使用环境变量或 `.env` 文件管理敏感信息
3. `.env` 文件应添加到 `.gitignore`

## 改进建议

1. 添加重试机制和错误处理
2. 实现响应缓存
3. 添加Token使用统计
4. 支持Markdown渲染

## 版本信息

- **任务编号**：T51
- **任务名称**：siyuan笔记集成
- **创建日期**：2025-02-13
- **文档质量等级**：A
