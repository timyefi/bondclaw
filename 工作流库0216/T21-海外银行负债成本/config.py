# -*- coding: utf-8 -*-
"""
T21-海外银行负债成本 配置文件

该配置文件管理项目的所有配置参数，包括：
- 数据文件路径
- 研究对象国家配置
- 可视化配置
"""

import os

# =============================================================================
# 路径配置
# =============================================================================

# 数据文件路径（使用环境变量或默认值）
DATA_FILE = os.environ.get('T21_DATA_FILE', 'complete_liability_cost_analysis_with_raw_data.xlsx')

# 输出目录
OUTPUT_DIR = os.environ.get('T21_OUTPUT_DIR', './output')

# =============================================================================
# 研究对象配置
# =============================================================================

# 国家/地区配置
COUNTRIES = {
    'US': {
        'name': '美国',
        'sheet_name': '美国完整原始数据',
        'policy_rate_col': '联邦基金利率(%)',
        'liability_cost_col': '负债成本_总负债口径(%)',
        'bond_yield_col': '美国10年国债收益率(%)'
    },
    'EU': {
        'name': '欧元区',
        'sheet_name': '欧元区完整原始数据',
        'policy_rate_col': 'ECB主要再融资利率(%)',
        'liability_cost_col': '负债成本_总负债口径(%)',
        'bond_yield_col': '德国10年国债收益率(%)'
    },
    'JP': {
        'name': '日本',
        'sheet_name': '日本完整原始数据',
        'policy_rate_col': 'BOJ政策利率(%)',
        'liability_cost_col': '负债成本_总负债口径(%)',
        'bond_yield_col': '日本10年国债收益率(%)'
    },
    'SG': {
        'name': '新加坡',
        'sheet_name': '新加坡完整原始数据',
        'policy_rate_col': 'MAS政策利率(%)',
        'liability_cost_col': '负债成本_总负债口径(%)',
        'bond_yield_col': '新加坡10年国债收益率(%)'
    }
}

# =============================================================================
# 分析参数配置
# =============================================================================

# 利率变化阈值（用于识别上行/下行周期）
RATE_CHANGE_THRESHOLD = 0.1  # 0.1%变化视为趋势变化

# 最大滞后期数
MAX_LAG_PERIODS = 3

# =============================================================================
# 可视化配置
# =============================================================================

# 图表配置
FIGURE_CONFIG = {
    'dpi': 300,
    'bbox_inches': 'tight',
    'facecolor': 'white'
}

# 颜色配置
COLORS = {
    'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
    'upward_policy': 'blue',
    'upward_liability': 'lightblue',
    'downward_policy': 'red',
    'downward_liability': 'lightcoral',
    'normal_period': 'steelblue',
    'low_rate_period': 'lightcoral'
}

# 中文字体配置
FONT_CONFIG = {
    'sans-serif': ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS'],
    'axes.unicode_minus': False
}

# =============================================================================
# 输出文件名配置
# =============================================================================

OUTPUT_FILES = {
    'cross_country_analysis': '图表1_跨国负债成本对比分析.png',
    'policy_bond_comparison': '图表2_跨国政策利率与国债收益率对比.png',
    'time_series_comparison': '各国政策利率与负债成本时间序列对比.png',
    'cycle_analysis': '上行下行周期分析对比.png',
    'lag_correlation': '滞后性分析汇总_相关性对比.png',
    'lag_conclusions': '银行负债成本滞后性分析结论.txt'
}

# =============================================================================
# 工具函数
# =============================================================================

def get_country_config(country_code):
    """获取指定国家的配置"""
    return COUNTRIES.get(country_code)

def get_all_sheet_names():
    """获取所有工作表名称"""
    return [cfg['sheet_name'] for cfg in COUNTRIES.values()]

def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    return OUTPUT_DIR

def get_output_path(filename):
    """获取输出文件的完整路径"""
    return os.path.join(OUTPUT_DIR, filename)
