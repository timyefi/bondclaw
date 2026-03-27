# T09 - 利率预测

## 项目概述

利率预测项目使用多模型融合的方法，从多个维度预测债券收益率的走势和拐点。

## 核心功能

### 五个子模型

| 模型 | 预测维度 | 预测期限 | 核心算法 |
|------|----------|----------|----------|
| 子模型1 | 行情集中度 | 短期(1-3个月) | GradientBoosting |
| 子模型2 | 交易拥挤度 | 超短期(1个月) | LightGBM |
| 子模型3 | 资金供需 | 中长期(1-2年) | 多项式回归 |
| 子模型4 | 银行负债成本 | 中期(1-2年) | Prophet |
| 子模型5 | 基本面/自然利率 | 长期(3-12个月) | 状态空间模型 |

## 目录结构

```
T09-利率预测\
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖
├── README.md          # 项目说明
├── src\               # 原始代码文件备份
│   ├── run_all_predictions.py
│   ├── predict_yield_with_concentration.py
│   ├── predict_yield_with_congestion.py
│   ├── predict_yield_with_demand_supply.py
│   ├── run_prediction.py
│   └── naturalratecn.py
├── data\              # 数据文件
├── assets\            # 图片等资源
└── output\            # 输出目录
```

## 数据源

- **bond库**: 市场行情数据、交易数据
- **yq库**: 宏观数据、银行数据
- **edb库**: 经济指标数据

主要数据表:
- `marketinfo_curve`: 收益率曲线数据
- `market_concentration_90pct`: 市场集中度指标
- `dealtinfo`: 成交数据
- `理财业绩跟踪`: 理财产品收益率
- `存款成本`: 银行存款成本

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

编辑 `config.py` 或设置环境变量:

```bash
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_HOST=your_host
export DB_PORT=3306
```

## 使用方法

### 运行单个模型

```python
# 在Jupyter Notebook中打开 重构.ipynb
# 按顺序执行各单元格
```

### 运行所有模型

```bash
python src/run_all_predictions.py
```

## 输出结果

- **预测表**: 各模型预测结果存入对应数据库表
- **图表**: 预测对比图、拐点识别图
- **报告**: 综合预测报告

## 模型说明

### 子模型1: 行情集中度

基于市场交易集中度指标预测短期收益率变化。
- 特征: 集中度、滚动平均、变化率、去趋势值
- 目标: 未来3个月收益率变化

### 子模型2: 交易拥挤度

基于活跃券成交占比识别市场交易热度。
- 特征: 拥挤度、动量、波动率
- 目标: 未来1个月收益率变化

### 子模型3: 资金供需

基于债市资金供需平衡预测中长期走势。
- 特征: 需求供给差值、季节性
- 方法: 市场状态切换模型

### 子模型4: 银行负债成本

基于银行各渠道负债成本预测利率下限。
- 输入: 理财收益率、存款利率、存单利率
- 方法: Prophet时间序列预测

### 子模型5: 自然利率

基于状态空间模型估算均衡利率水平。
- 参考: 孙国峰与Rees(2021) BIS Working Paper 949
- 方法: 卡尔曼滤波、最大似然估计

## 注意事项

1. 数据库连接需要正确权限
2. 各模型对数据量有最低要求
3. 预测结果仅供参考，不构成投资建议

## 维护信息

- **最后更新**: 2026-02-14
- **负责人**: 量化研究员
- **执行频率**: 每日/每周
