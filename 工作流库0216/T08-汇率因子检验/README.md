# T08 - 汇率因子检验

## 项目概述

汇率因子检验项目专注于研究汇率变化对债券市场的影响。通过分析人民币汇率与债券收益率、利差等指标的相关性，识别汇率因子对债券投资的影响机制，为投资决策提供参考。

## 功能特性

- **数据采集**：获取人民币兑美元汇率、资金利率、股指、债券收益率等金融数据
- **因子分析**：计算汇率与各因子的静态相关性和滚动相关性
- **高相关性识别**：识别汇率与各因子的高相关性时期
- **可视化报告**：生成交互式HTML报告，包含相关性分析图表

## 数据源

| 数据类型 | 数据表 | 代码 | 说明 |
|---------|--------|------|------|
| 汇率 | edb.edbdata | M0067855 | 人民币兑美元即期汇率 |
| 资金利率 | edb.edbdata | M1006337 | DR007 |
| 资金利率 | edb.edbdata | M1004515 | GC007 |
| 股指 | edb.edbdata | M0020209 | 沪深300指数 |
| 股指 | stock.indexcloseprice | 881001.WI | 万得全A指数 |
| 股指 | stock.indexcloseprice | 399101.SZ | 中小板指 |
| 股指 | stock.indexcloseprice | HSCI.HI | 恒生指数 |
| 债券 | bond.marketinfo_curve | L001619604 | 10年国债收益率 |
| 债券 | bond.marketinfo_curve | L001618296 | 1年国债收益率 |
| 债券 | bond.marketinfo_curve | L003759264 | 5年城投债收益率 |

## 项目结构

```
T08-汇率因子检验/
├── 重构.ipynb          # 主重构Notebook
├── config.py           # 配置参数
├── requirements.txt    # Python依赖列表
├── README.md           # 项目说明
├── src/                # 原始代码文件
│   ├── data_preparation.py
│   └── correlation_analysis.py
├── data/               # 数据文件
├── assets/             # 图片等资源
└── output/             # 输出目录
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 使用Jupyter Notebook

打开 `重构.ipynb` 并按顺序执行各单元格。

### 2. 使用Python脚本

```bash
# 数据准备
python src/data_preparation.py

# 相关性分析
python src/correlation_analysis.py
```

## 配置说明

编辑 `config.py` 文件进行配置：

```python
# 数据库配置（使用环境变量）
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '3306'),
    'user': os.environ.get('DB_USER', 'user'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_DATABASE', 'yq'),
}

# 分析参数
ANALYSIS_CONFIG = {
    'start_date': '2015-01-01',
    'end_date': '2026-02-14',
    'rolling_window': 60,
    'correlation_threshold': 0.5,
}
```

## 输出结果

- `output/processed_data.parquet` - 处理后的数据文件
- `output/correlation_analysis.html` - 相关性分析HTML报告

## 应用场景

1. **择时策略**：根据汇率变化调整债券配置
2. **风险管理**：对冲汇率风险，控制汇率敏感头寸
3. **投资决策**：根据汇率因子分析调整投资组合

## 维护信息

- **优先级**：中
- **执行频率**：每周/每月
- **负责人**：量化研究员/宏观分析师
- **最后更新**：2026-02-14
