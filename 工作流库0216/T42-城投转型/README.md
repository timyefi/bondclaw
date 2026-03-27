# 城投转型

城投融资平台转型数据管理与分析项目。

## 项目功能

1. **城投融资平台转型数据管理** - 集中管理城投融资平台转型数据
2. **跟踪城投融资平台转型情况** - 记录市场化退出过程
3. **数据汇总与统计分析** - 多维度分析转型趋势和分布特征

## 目录结构

```
T42-城投转型/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

项目使用环境变量管理敏感信息。请在运行前设置以下环境变量：

```bash
# Linux/Mac
export DB_HOST='your_host'
export DB_PORT='3306'
export DB_NAME='yq'
export DB_USER='your_user'
export DB_PASSWORD='your_password'

# Windows PowerShell
$env:DB_HOST='your_host'
$env:DB_PORT='3306'
$env:DB_NAME='yq'
$env:DB_USER='your_user'
$env:DB_PASSWORD='your_password'
```

## 数据结构

### 核心字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| itName | 公司名称 | 桂林经开投资控股有限责任公司 |
| regionName | 区域名称 | 桂林市 |
| releaseDate | 发布日期 | 2025-04-02 |
| changeType | 变更类型 | 退出、市场化转型、隐性债务清零 |
| changeReason | 变更原因 | 市场化转型、隐性债务清零 |
| publishEntity | 发布主体 | 企业披露、官方披露 |
| subjectRating | 主体评级 | AAA、AA+、AA |
| bondStockSize | 债券库存规模 | 5.19 |
| province | 省份 | 广西壮族自治区 |
| city | 城市 | 桂林市 |

### 变更类型说明

- **退出**: 城投融资平台完全退出政府融资职能
- **市场化转型**: 按照市场化要求建立公司法人治理结构
- **隐性债务清零**: 隐性债务已清零，退出融资平台监管范畴

## 使用方法

### 运行Notebook

1. 启动Jupyter:
```bash
jupyter notebook
```

2. 打开 `重构.ipynb`

3. 按顺序执行各个单元格

### 输出结果

执行完成后，将在 `output/` 目录生成以下文件：

- `转型城投清单.json` - JSON格式数据
- `转型城投清单.csv` - CSV格式数据
- `变更类型.csv` - 变更类型统计
- `变更原因.csv` - 变更原因统计
- `省份分布.csv` - 省份分布统计
- `城市TOP20.csv` - 城市TOP20统计
- `发布主体.csv` - 发布主体统计
- `主体评级.csv` - 主体评级统计
- `月度趋势.csv` - 月度趋势统计

## 依赖说明

- pandas: 数据处理与分析
- numpy: 数值计算
- sqlalchemy: 数据库ORM
- pymysql: MySQL数据库驱动

## 任务信息

- **任务ID**: T42
- **任务名称**: 城投转型
- **文档质量等级**: A
