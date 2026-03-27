# T62-文章润色

基于阿里云Qwen大模型的Markdown文章润色工具。

## 功能特点

- 逐段润色：保持文章原有结构和风格
- 模块化设计：核心功能封装在`ArticleRefiner`类中
- 环境变量管理：安全管理API密钥
- 易于扩展：可轻松添加新的润色策略

## 目录结构

```
T62-文章润色/
├── 重构.ipynb        # Jupyter Notebook主文件（7章节）
├── config.py         # 配置文件
├── requirements.txt  # 依赖包
├── README.md         # 说明文档
├── src/              # 源代码目录
│   ├── __init__.py
│   └── refiner.py    # 核心润色模块
├── data/             # 数据目录
├── assets/           # 资源目录
└── output/           # 输出目录
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置

在使用前，需要设置API密钥环境变量：

```bash
# Linux/macOS
export DASHSCOPE_API_KEY="your-api-key"

# Windows
set DASHSCOPE_API_KEY=your-api-key
```

或者在代码中临时设置：

```python
import os
os.environ["DASHSCOPE_API_KEY"] = "your-api-key"
```

## 使用方法

### 方式一：使用Notebook

1. 打开`重构.ipynb`
2. 按顺序执行各单元格

### 方式二：使用Python脚本

```python
from src.refiner import ArticleRefiner

# 初始化润色器
refiner = ArticleRefiner()

# 处理文件
refiner.process_file("input.md", "output.md")
```

## 可配置参数

| 参数 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| API密钥 | DASHSCOPE_API_KEY | - | 阿里云API密钥 |
| API地址 | DASHSCOPE_BASE_URL | https://dashscope.aliyuncs.com/compatible-mode/v1 | API基础URL |
| 模型名称 | MODEL_NAME | qwen-max | 使用的模型 |
| 最大Token | MAX_TOKENS | 2000 | 最大输出Token数 |
| 温度 | TEMPERATURE | 0.1 | 生成温度参数 |

## Notebook章节说明

1. **环境准备与依赖安装**: 安装必要依赖，导入模块
2. **配置管理**: 查看和设置API配置
3. **数据加载**: 准备和加载待润色的Markdown文件
4. **核心功能实现**: 展示文章润色的核心功能
5. **执行润色任务**: 对完整文章进行润色处理
6. **结果展示与分析**: 查看润色结果并对比分析
7. **总结与扩展**: 项目总结和扩展方向

## 扩展方向

1. 添加批量处理功能
2. 支持更多文档格式（Word、PDF等）
3. 添加润色风格选项（正式、口语化等）
4. 实现润色历史记录和版本对比
5. 添加进度显示和断点续传
