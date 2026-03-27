# 图表复制工作流

本项目是一个图表数据提取与处理工作流，主要用于从图表图像中提取数据点，计算商品指数与金融资产的比率，并将结果写入数据库。

## 功能特性

### 1. 图表数据提取
- 通过OpenCV图像处理技术，从图表图片中识别曲线并提取数据点
- 支持交互式选择数据区域和样本点
- 支持多种日期格式（YYYY/MM, YYYY-MM-DD）
- 支持不同频率的数据点（周度、月度、年度）

### 2. 商品比率计算
- 从EDB数据库获取指标数据
- 计算CRB商品指数与金融资产比率
- 计算公式：`CRB CMDT Index / (0.5 * (FLOT US Equity + .EARNREV G Index))`
- 基准日期：2020-11-12
- 输出周度数据

## 项目结构

```
T28-图表复制工作流/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件
│   ├── calculate_commodity_ratio.py
│   ├── 提取图片虚线数据.py
│   └── verify_results.py
├── data/              # 数据文件
│   └── sample_points_cache.json
├── assets/            # 图片等资源
│   ├── detected_points.png
│   ├── 农商行.png
│   └── 实物资产比金融资产.png
└── output/            # 输出目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

在运行之前，请设置以下环境变量：

```bash
# Linux/macOS
export DB_PASSWORD=your_password

# Windows PowerShell
$env:DB_PASSWORD="your_password"
```

或者直接在代码中修改 `config.py` 文件。

## 使用方法

### 运行完整工作流

1. 打开 `重构.ipynb` Notebook
2. 按顺序执行各个单元格

### 运行原始脚本

```bash
# 计算商品比率
python src/calculate_commodity_ratio.py

# 验证结果
python src/verify_results.py
```

### 提取图表数据

```python
from 提取图片虚线数据 import extract_data_from_graph

# 从本地图片提取数据
value_points, result_img = extract_data_from_graph(
    "assets/实物资产比金融资产.png",
    is_url=False,
    frequency='week'
)

# 从URL提取数据
value_points, result_img = extract_data_from_graph(
    "https://example.com/chart.png",
    is_url=True,
    frequency='week'
)
```

## 数据源

- **数据库**：EDB数据库 (edb.edbdata表)
- **指标数据**：
  - CRB CMDT Index：CRB商品指数
  - FLOT US Equity：美国股票指数
  - .EARNREV G Index：盈利修正指数

## 输出结果

- **商品比率数据**：写入`全球实物资产比金融资产`表
- **图像提取数据**：
  - 控制台输出检测点列表
  - 保存标注图像到`output/detected_points.png`
  - 缓存样本点到`data/sample_points_cache.json`

## 注意事项

1. **图像处理**：
   - 需要交互式操作选择数据区域和样本点
   - 确保图像质量清晰

2. **数据库操作**：
   - 确保数据库连接正常
   - 密码通过环境变量设置，避免硬编码
   - 周度数据转换使用resample('W').last()

3. **颜色识别**：
   - 动态计算颜色容差
   - 使用形态学操作清理噪点
   - 支持断点续传（通过缓存文件）

## 许可证

MIT License
