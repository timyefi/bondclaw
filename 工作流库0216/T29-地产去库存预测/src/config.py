#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地产去库存预测分析配置文件
"""

# EDB数据代码映射
TRADE_CODE_MAPPING = {
    'S0029674': '中国:商品房待售面积:住宅:累计值',
    'S0049264': '商品房销售面积:住宅:现房:累计值', 
    'S0049296': '商品房销售面积:住宅:期房:累计值',
    'S0049585': '中国:房屋竣工面积:住宅:累计值',
    'S0029669': '中国:房屋新开工面积:住宅:累计值'
}

# 预测参数
FORECAST_CONFIG = {
    'start_date': '2024-10-01',  # 趋势分析起始日期
    'end_date': '2027-12-31',    # 预测结束日期
    'rolling_window': 12,        # 滚动窗口（月）
    'min_train_points': 6        # 最小训练数据点数
}

# 输出配置
OUTPUT_CONFIG = {
    'excel_filename': 'real_estate_destocking_forecast.xlsx',
    'plot_filename': 'real_estate_destocking_forecast.png',
    'plot_dpi': 300,
    'figure_size': (15, 12)
}