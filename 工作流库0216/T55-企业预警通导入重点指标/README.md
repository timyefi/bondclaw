# T55-企业预警通导入重点指标

## 项目简介

本项目用于将Excel中的重点指标数据导入到数据库中，支持trade_code替换和数据清洗。

## 功能特性

- Excel数据读取和解析
- trade_code自动匹配替换
- 数据清洗和验证
- 批量导入到数据库

## 目录结构

```
T55-企业预警通导入重点指标/
├── 重构.ipynb          # 主Notebook
├── config.py           # 配置文件
├── requirements.txt    # 依赖包
├── README.md           # 说明文档
├── src/                # 源代码
├── data/               # 数据目录
├── assets/             # 资源文件
└── output/             # 输出目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 将Excel文件放入data目录
2. 配置环境变量设置数据库连接信息
3. 运行 `重构.ipynb` 中的各章节

## SQL脚本说明

### trade_code替换
```sql
-- 通过发行人名称匹配trade_code
WITH trade_code_mapping AS (
    SELECT MAX(trade_code) AS trade_code, ths_issuer_name_cn_bond
    FROM (
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_credit
        UNION ALL
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_finance
        UNION ALL
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_abs
    ) SQ
    GROUP BY ths_issuer_name_cn_bond
)
UPDATE 指标数据1 A
SET trade_code = trade_code_mapping.trade_code
FROM trade_code_mapping
WHERE A.ths_issuer_name_cn_bond = trade_code_mapping.ths_issuer_name_cn_bond;
```

### 数据清洗
```sql
-- 删除trade_code列中有中文字符的行
DELETE FROM 指标数据1 WHERE trade_code ~ '[\u4e00-\u9fa5]';

-- 删除空值行
DELETE FROM 指标数据1 WHERE value IS NULL OR value = '';
```

## 更新日志

- 2024-03: 初始版本
