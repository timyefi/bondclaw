# T53-yy区域数据整理

## 任务概述

本工具用于从企业预警通(Ratingdog)平台获取区域经济数据，主要功能包括：

1. **区域数据采集**：从企业预警通API获取各级行政区域的经济数据
2. **多维度指标**：涵盖GDP、财政收支、债务限额、土地成交等50+指标
3. **行政区域归整**：将复杂的区域名称标准化为省-市-区县三级结构
4. **数据自动更新**：支持增量更新，自动添加新字段

## 目录结构

```
T53-yy区域数据整理/
|-- 重构.ipynb          # 重构后的Jupyter Notebook
|-- config.py           # 配置文件（敏感信息通过环境变量获取）
|-- requirements.txt    # Python依赖包
|-- README.md           # 说明文档
|-- src/                # 源代码
|   |-- yy区域数据.py   # 原始源代码
|-- data/               # 数据文件
|   |-- 行政区域归整.txt
|-- assets/             # 资源文件
|-- output/             # 输出文件
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

请设置以下环境变量：

```bash
# 企业预警通账号
export RATINGDOG_USERNAME="your_username"
export RATINGDOG_PASSWORD="your_password"
export RATINGDOG_PHONE_CODE="86"

# 数据库配置
export DB_HOST="your_db_host"
export DB_PORT="3306"
export DB_USER="your_db_user"
export DB_PASSWORD="your_db_password"
export DB_NAME="yq"
```

## 使用方法

### 方式1：运行Jupyter Notebook

```bash
jupyter notebook 重构.ipynb
```

### 方式2：直接运行源代码

```bash
python src/yy区域数据.py
```

## 数据指标

### 经济指标（7个）
- GDP、GDP增长率、人均GDP、固定资产投资等

### 财政指标（21个）
- 一般预算收入、税收收入、债务限额等

### 金融指标（6个）
- 存款余额、贷款余额、不良贷款率等

### 隐性债务指标（11个）
- 隐性债务化解、隐债比率、有息债务等

### 房地产指标（6个）
- 房价指数、住宅交易面积、成交均价等

### 基础设施指标（19个）
- 道路长度、供水能力、污水处理等

## 数据流程

```
企业预警通API --> 认证登录 --> 分页获取数据 --> 解析响应
    --> 动态更新表结构 --> 保存到MySQL --> 行政区域标准化
```

## 注意事项

1. **敏感信息**：所有账号密码通过环境变量配置，请勿硬编码
2. **分页处理**：每页150条记录，自动循环获取全部数据
3. **动态字段**：API新增指标时自动添加数据库列
4. **区域标准化**：直辖市、省直辖县级市等特殊情况需特殊处理

## 改进建议

1. 添加错误重试机制
2. 实现数据验证
3. 支持增量更新
4. 添加日志记录
5. 性能优化（批量插入、并发请求）

## 更新日志

- 2026-02-15: 初始版本，完成重构
