#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地产去库存预测分析配置文件

注意: 敏感信息应通过环境变量配置
"""

import os

# EDB数据代码映射
TRADE_CODE_MAPPING = {
    'S0029674': '中国:商品房待售面积:住宅:累计值',
    'S0049264': '商品房销售面积:住宅:现房:累计值',
    'S0049296': '商品房销售面积:住宅:期房:累计值',
    'S0049585': '中国:房屋竣工面积:住宅:累计值',
    'S0029669': '中国:房屋新开工面积:住宅:累计值'
}

# 数据代码列表
TRADE_CODES = list(TRADE_CODE_MAPPING.keys())

# 预测参数
FORECAST_CONFIG = {
    'start_date': '2024-10-01',  # 趋势分析起始日期
    'end_date': '2027-12-31',    # 预测结束日期
    'rolling_window': 12,        # 滚动窗口（月）
    'min_train_points': 6        # 最小训练数据点数
}

# 数据库配置（从环境变量获取）
DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'hz_work'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': os.environ.get('DB_PORT', '3306'),
    'database': os.environ.get('DB_DATABASE', 'edb'),
    'charset': 'utf8mb4'
}

# 输出配置
OUTPUT_CONFIG = {
    'excel_filename': 'real_estate_destocking_forecast.xlsx',
    'plot_filename': 'real_estate_destocking_forecast.png',
    'plot_dpi': 300,
    'figure_size': (15, 12)
}
