# T47 - 央行及金融资产负债表数据采集系统

## 项目概述

本系统用于从Wind EDB（经济数据库）自动获取央行及金融机构资产负债表指标。支持增量更新、自动建表、动态加列和UPSERT策略。

## 核心功能

1. **增量更新**: 从数据库最大日期的下一天开始获取新数据，减少API调用
2. **自动建表**: 检测表是否存在，不存在则自动创建
3. **动态加列**: 如果新增指标，自动添加新列到数据库表
4. **UPSERT策略**: 使用 INSERT ... ON DUPLICATE KEY UPDATE 实现插入或更新

## 数据源

- **数据来源**: Wind EDB (Economic Database)
- **API接口**: WindPy的`w.edb()`方法
- **更新频率**: 日度更新

## 指标分组

系统采集约130个指标，分为3组：

### 第一组：央行资产负债表核心指标 (42个)
包含央行资产端和负债端的主要指标，如：
- 对存款性公司债权
- 对政府债权
- 货币发行
- 其他存款性公司存款

### 第二组：金融机构资产负债表指标 (42个)
包含各类金融机构的资产负债表指标，如：
- 大型商业银行资产负债表
- 中小型商业银行资产负债表
- 农村金融机构资产负债表

### 第三组：其他金融指标 (约88个)
包含货币供应量、社会融资规模等指标，如：
- M0、M1、M2货币供应量
- 各类贷款余额
- 社会融资规模

## 目录结构

```
T47-央行及金融资产负债表/
├── 重构.ipynb         # 主重构Notebook
├── README.md          # 项目说明
├── requirements.txt   # Python依赖列表
├── config.py          # 配置参数
├── src/               # 原始代码文件备份
│   └── yhzf.py        # 原始源代码
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

创建 `.env` 文件或设置环境变量：

```bash
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=3306
DB_NAME=yq
```

### 3. Wind API授权

确保Wind终端已启动并登录，或已配置Wind API授权。

## 使用方法

### 方式一：运行Notebook

```bash
jupyter notebook 重构.ipynb
```

逐单元格执行Notebook中的代码。

### 方式二：直接运行Python脚本

参考Notebook中的代码逻辑，编写独立的Python脚本运行。

## 核心逻辑

### 数据流程

```
Wind EDB → API调用 → DataFrame → 数据清洗 → 检查表结构 → UPSERT插入
```

### 增量更新逻辑

1. 查询数据库最大日期: `SELECT MAX(dt) FROM 金融资负`
2. 计算开始日期: `max_date + 1 day`
3. 调用Wind API获取数据
4. 清洗并插入数据

### UPSERT策略

```sql
INSERT INTO yq.金融资负 (dt, indicator1, indicator2, ...)
VALUES (:dt, :indicator1, :indicator2, ...)
ON DUPLICATE KEY UPDATE
    indicator1 = VALUES(indicator1),
    indicator2 = VALUES(indicator2), ...;
```

## 注意事项

1. **Wind授权**: 需要有效的Wind账号授权
2. **数据库权限**: 需要CREATE/ALTER/INSERT权限
3. **运行时间**: 建议在收盘后（16:00-18:00）运行
4. **错误处理**: 如果某组指标获取失败，不影响其他组

## 改进建议

1. 使用批量插入替代逐行插入，提升性能10-20倍
2. 添加数据质量验证和监控告警
3. 实现并发调用多组指标
4. 定期进行全量更新以获取历史数据修正

## 版本历史

- **v1.0** (2024-06): 初始版本
- **v2.0** (2025-02): 重构版本，增强可读性和可维护性

## 作者

- 任务编号: T47
- 生成时间: 2025-02
