# T33 - 信用债规模

信用债规模数据ETL处理系统，专注于统计和分析债券市场的存续规模数据。

## 项目概述

本项目实现债券市场规模数据的ETL（Extract-Transform-Load）处理，包括：
- 债券分类重建（信用债、金融债、ABS）
- 评级补全
- 久期补全
- 多维度汇总统计

## 目录结构

```
T33-信用债规模/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── xyzgm.py       # 原始Python脚本
│   └── 1.ipynb        # 原始Notebook
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

在使用前，需要设置以下环境变量：

```bash
# MySQL数据库配置
export MYSQL_HOST=your_mysql_host
export MYSQL_PORT=3306
export MYSQL_USER=your_username
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=bond

# PostgreSQL数据库配置
export PG_HOST=your_pg_host
export PG_PORT=5432
export PG_USER=postgres
export PG_PASSWORD=your_password
export PG_DATABASE=tsdb
```

## 使用方法

### 运行Jupyter Notebook

```bash
cd 重构/T33-信用债规模
jupyter notebook 重构.ipynb
```

### 运行Python脚本

```bash
cd 重构/T33-信用债规模
python src/xyzgm.py
```

## 核心功能

### 1. 债券分类重建

将债券按大类分类：
- **城投债**：地方融资平台发行的债券
- **产业债**：企业发行的信用债券
- **金融债**：银行、证券、保险等金融机构发行的债券
- **ABS**：资产证券化产品

### 2. 评级补全

从市场行情表中获取每个债券最新日期的隐含评级，更新到债券分类表。

### 3. 久期补全

计算债券久期：
- 优先使用市场久期数据
- 缺失时从基础信息表计算剩余年限
- 特殊处理永续债

### 4. 多维度规模汇总

按以下维度汇总债券规模：

| 分类方式 | 说明 |
|---------|------|
| 大类 | 全部、城投、产业、金融、ABS |
| 省 | 城投债按省份分类 |
| 市 | 城投债按城市分类 |
| 申万行业 | 产业债按申万行业分类 |
| 金融机构 | 金融债按机构类型分类 |
| 资产类型 | ABS按基础资产类型分类 |
| 评级 | AAA、AA+、AA等 |
| 久期 | 0.5年、1年、2年、3年、4年、5年、7年、10年 |

## 数据流向

```
基础信息表 → 债券分类表 → 市场信息3表 → 信用债规模表
```

**输入表：**
- `bond.basicinfo_credit` - 信用债基础信息
- `bond.basicinfo_finance` - 金融债基础信息
- `bond.basicinfo_abs` - ABS基础信息
- `bond.marketinfo_credit` - 信用债市场信息
- `bond.marketinfo_finance` - 金融债市场信息
- `bond.marketinfo_abs` - ABS市场信息

**输出表：**
- `bond.债券分类` - 债券分类汇总表
- `bond.marketinfo3` - 市场信息汇总表
- `bond.信用债规模` - 规模汇总表

## 配置参数

主要配置参数见 `config.py`：

```python
# 债券大类类型
MAJOR_TYPES = ['信用债', '金融债', 'ABS', '城投', '产业']

# 评级等级
RATING_LEVELS = ['AAA', 'AA+', 'AA', 'AA-', 'A', '其他', '无评级']

# 久期分段阈值
DURATION_THRESHOLDS = {
    0.5: 0.75,   # 久期 < 0.75年 -> 0.5年
    1: 1.5,      # 久期 < 1.5年 -> 1年
    2: 2.5,      # 久期 < 2.5年 -> 2年
    ...
}
```

## 注意事项

1. **敏感信息**：所有数据库密码必须通过环境变量设置，禁止硬编码
2. **数据质量**：确保输入数据完整性 >= 95%
3. **执行频率**：建议每周执行一次
4. **执行时间**：完整ETL流程约需10-30分钟

## 维护信息

- **创建日期**：2026-02-15
- **最后更新**：2026-02-15
- **负责人**：数据分析师/量化研究员
