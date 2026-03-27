# 募集用途分析

债券募集用途文本分析系统，用于对比分析转型城投与普通城投的募集用途差异。

## 功能特性

- **数据获取**: 从数据库获取转型城投清单和募集用途数据
- **文本分析**: 使用jieba分词和关键词字典分析文本
- **聚类分析**: TF-IDF向量化与K-Means聚类
- **可视化展示**: 词云、热力图、雷达图、饼图等

## 项目结构

```
T41-募集用途分析/
├── 重构.ipynb         # 主重构Notebook
├── config.py          # 配置参数
├── requirements.txt   # Python依赖列表
├── README.md          # 项目说明
├── src/               # 原始代码文件备份
│   ├── analyze.py
│   ├── analyze_bond_usage.py
│   ├── analyze_text.py
│   ├── analyze_transform.py
│   ├── visualize_analysis.py
│   └── explore_data.py
├── data/              # 数据文件
├── assets/            # 图片等资源
└── output/            # 输出目录
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

设置环境变量：

```bash
# Windows
set DB_PASSWORD=your_password

# Linux/Mac
export DB_PASSWORD=your_password
```

## 使用方法

### 运行Notebook

1. 打开 `重构.ipynb`
2. 按顺序执行各个单元格

### 运行源代码

```bash
# 执行完整分析
python src/analyze_transform.py

# 仅执行文本分析
python src/analyze_text.py

# 数据探索
python src/explore_data.py
```

## 核心算法

### 关键词分析

使用jieba分词对文本进行切分，然后根据预定义的关键词字典统计各类别关键词的出现频率。

### 聚类分析

1. TF-IDF向量化（max_features=1000）
2. K-Means聚类（n_clusters=5）
3. 提取每个簇的top 10关键词

## 数据源

- `yq.城投平台市场化经营主体` - 城投平台市场化经营主体清单
- `yq.城投平台退出` - 城投平台退出记录
- `yq.城投募集资金用途` - 城投债募集用途数据
- `yq.产业债募集资金用途` - 产业债募集用途数据

## 输出结果

- 关键词频率分析结果（JSON）
- 各类可视化图表（PNG）
  - 关键词热力图
  - 词云图
  - 雷达图
  - 用途饼图
  - 月度趋势图
  - 关键词对比图

## 关键词类别

共14个类别：

1. 债务管理
2. 资金用途
3. 转型相关
4. 政府关系
5. 业务发展
6. 产业投资
7. 市场竞争
8. 创新发展
9. 公司治理
10. 财务状况
11. 转型效果
12. 市场化指标
13. 企业文化
14. 社会责任

## 注意事项

1. 数据库密码请通过环境变量设置，不要硬编码
2. 首次运行需要下载jieba分词词典
3. 可视化图表会自动保存到output目录

## 版本历史

- v1.0 - 初始版本，包含基础分析和可视化功能
