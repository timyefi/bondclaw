# -*- coding: utf-8 -*-
"""
T12 - 理财产品权益配置 - 配置文件

本配置文件包含理财产品权益配置分析所需的所有配置参数。
重要：所有敏感信息必须通过环境变量配置。
"""

import os

# ============================================================
# 数据库连接配置
# 使用环境变量配置敏感信息，确保安全性
# ============================================================

DB_HOST = os.environ.get('WEALTH_DB_HOST', 'localhost')
DB_PORT = os.environ.get('WEALTH_DB_PORT', '3306')
DB_USER = os.environ.get('WEALTH_DB_USER', 'root')
DB_PASSWORD = os.environ.get('WEALTH_DB_PASSWORD', '')
DB_NAME = os.environ.get('WEALTH_DB_NAME', 'wealth_products')

# 数据库连接字符串模板
DB_CONNECTION_STRING = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ============================================================
# 产品风险等级配置
# R1-R5 风险等级定义
# ============================================================

RISK_CLASSES = {
    'R1': '低风险',
    'R2': '中低风险',
    'R3': '中等风险',
    'R4': '中高风险',
    'R5': '高风险'
}

# 各风险等级的权益配置建议范围
RISK_EQUITY_LIMITS = {
    'R1': {'min': 0.00, 'max': 0.10, 'description': '低风险产品，权益配置不超过10%'},
    'R2': {'min': 0.00, 'max': 0.20, 'description': '中低风险产品，权益配置不超过20%'},
    'R3': {'min': 0.10, 'max': 0.40, 'description': '中等风险产品，权益配置10%-40%'},
    'R4': {'min': 0.20, 'max': 0.60, 'description': '中高风险产品，权益配置20%-60%'},
    'R5': {'min': 0.40, 'max': 0.80, 'description': '高风险产品，权益配置40%-80%'}
}


# ============================================================
# 投资类型配置
# ============================================================

INVESTMENT_TYPES = {
    'fixed_income': '固定收益类',
    'equity': '权益类',
    'mixed': '混合类',
    'money_market': '货币市场类',
    'commodity': '商品类'
}


# ============================================================
# 期限分类配置
# ============================================================

MATURITY_TYPES = {
    'short': {
        'name': '短期',
        'name_full': '短期（<3个月）',
        'days_min': 0,
        'days_max': 90
    },
    'medium': {
        'name': '中期',
        'name_full': '中期（3-12个月）',
        'days_min': 91,
        'days_max': 365
    },
    'long': {
        'name': '长期',
        'name_full': '长期（>12个月）',
        'days_min': 366,
        'days_max': 99999
    }
}


# ============================================================
# 权益资产类型配置
# ============================================================

EQUITY_TYPES = {
    'stock': {
        'name': '股票',
        'risk_weight': 0.50,
        'liquidity': 'high'
    },
    'stock_index': {
        'name': '股票指数',
        'risk_weight': 0.30,
        'liquidity': 'high'
    },
    'equity_fund': {
        'name': '股票基金',
        'risk_weight': 0.20,
        'liquidity': 'medium'
    },
    'stock_option': {
        'name': '股票期权',
        'risk_weight': 0.80,
        'liquidity': 'medium'
    },
    'equity_derivatives': {
        'name': '权益衍生品',
        'risk_weight': 0.90,
        'liquidity': 'low'
    }
}


# ============================================================
# 权益配置比例限制
# 理财产品核心配置参数
# ============================================================

WEALTH_PRODUCT_CONFIG = {
    # 权益比例限制
    'min_equity_ratio': 0.00,      # 最小权益比例（0%）
    'max_equity_ratio': 0.80,      # 最大权益比例（80%）

    # 风险权重（用于计算加权风险暴露）
    'risk_weight': {
        'stock': 0.50,
        'stock_index': 0.30,
        'equity_fund': 0.20,
        'stock_option': 0.80,
        'equity_derivatives': 0.90
    },

    # 流动性要求
    'liquidity_requirement': 0.10,  # 最低流动性资产比例（10%）

    # 杠杆限制
    'leverage_limit': 1.40,         # 最大杠杆倍数（140%）

    # 单一资产集中度限制
    'single_asset_limit': 0.10,     # 单一资产最大占比（10%）

    # 行业集中度限制
    'single_industry_limit': 0.30,  # 单一行业最大占比（30%）
}


# ============================================================
# 风险分析参数配置
# ============================================================

RISK_ANALYSIS_CONFIG = {
    # VaR置信水平
    'var_confidence_levels': [0.95, 0.99],

    # 夏普比率计算参数
    'risk_free_rate': 0.02,         # 无风险利率（2%）
    'trading_days_per_year': 252,   # 年交易日数

    # 回撤分析参数
    'max_drawdown_window': 252,     # 最大回撤计算窗口（1年）

    # 压力测试参数
    'stress_test_scenarios': {
        'mild': {'equity_shock': -0.10, 'rate_shock': 0.005},
        'moderate': {'equity_shock': -0.20, 'rate_shock': 0.01},
        'severe': {'equity_shock': -0.30, 'rate_shock': 0.02}
    }
}


# ============================================================
# 数据分析参数配置
# ============================================================

ANALYSIS_CONFIG = {
    # 波动率计算窗口
    'volatility_window': 20,        # 日波动率计算窗口

    # 分组统计参数
    'histogram_bins_method': 'auto', # 直方图分组方法
    'min_samples_for_analysis': 30,  # 最小分析样本数

    # 数据清洗参数
    'outlier_method': 'iqr',         # 异常值检测方法
    'outlier_threshold': 3.0,        # 异常值阈值
}


# ============================================================
# 可视化配置
# ============================================================

VISUALIZATION_CONFIG = {
    # 图表默认配置
    'figure_size': (14, 10),
    'dpi': 300,
    'font_size': 12,

    # 颜色配置
    'color_palette': 'Set2',
    'risk_colors': {
        'R1': '#2ecc71',  # 绿色
        'R2': '#27ae60',  # 深绿
        'R3': '#f39c12',  # 橙色
        'R4': '#e74c3c',  # 红色
        'R5': '#c0392b'   # 深红
    },

    # 输出格式
    'export_format': 'png',
    'export_quality': 95
}


# ============================================================
# 报告生成配置
# ============================================================

REPORT_CONFIG = {
    # 报告模板路径
    'template_path': './templates/',

    # 报告输出路径
    'output_path': './reports/',

    # 报告格式
    'formats': ['excel', 'pdf', 'html'],

    # 报告内容配置
    'sections': [
        '产品概述',
        '权益配置分析',
        '收益分析',
        '风险分析',
        '监管合规检查',
        '建议与结论'
    ]
}


# ============================================================
# 日志配置
# ============================================================

LOG_CONFIG = {
    'level': os.environ.get('WEALTH_LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './logs/wealth_analysis.log',
    'console': True
}


# ============================================================
# 辅助函数
# ============================================================

def get_risk_class_name(risk_level):
    """获取风险等级中文名称"""
    return RISK_CLASSES.get(risk_level, '未知')


def get_investment_type_name(investment_type):
    """获取投资类型中文名称"""
    return INVESTMENT_TYPES.get(investment_type, '未知')


def validate_equity_ratio(ratio, risk_level):
    """
    验证权益比例是否符合风险等级要求

    Args:
        ratio: 权益配置比例（0-1之间）
        risk_level: 风险等级（R1-R5）

    Returns:
        tuple: (is_valid, warning_message)
    """
    if risk_level not in RISK_EQUITY_LIMITS:
        return False, f"未知的风险等级: {risk_level}"

    limits = RISK_EQUITY_LIMITS[risk_level]

    if ratio < limits['min']:
        return False, f"权益比例 {ratio:.2%} 低于 {risk_level} 最小限制 {limits['min']:.2%}"

    if ratio > limits['max']:
        return False, f"权益比例 {ratio:.2%} 超过 {risk_level} 最大限制 {limits['max']:.2%}"

    return True, "配置比例符合要求"


def get_maturity_type(days):
    """
        根据天数获取期限类型

    Args:
        days: 投资期限天数

    Returns:
        str: 期限类型代码
    """
    if days <= MATURITY_TYPES['short']['days_max']:
        return 'short'
    elif days <= MATURITY_TYPES['medium']['days_max']:
        return 'medium'
    else:
        return 'long'


def calculate_weighted_risk(allocation_dict):
    """
    计算加权风险暴露

    Args:
        allocation_dict: 资产配置字典，key为资产类型，value为配置比例

    Returns:
        float: 加权风险暴露值
    """
    total_risk = 0
    for asset_type, ratio in allocation_dict.items():
        if asset_type in WEALTH_PRODUCT_CONFIG['risk_weight']:
            total_risk += ratio * WEALTH_PRODUCT_CONFIG['risk_weight'][asset_type]
    return total_risk


# ============================================================
# 配置验证
# ============================================================

def validate_config():
    """验证配置完整性"""
    errors = []

    # 检查数据库配置
    if not DB_HOST:
        errors.append("数据库主机地址未配置")

    # 检查风险等级配置
    if len(RISK_CLASSES) != 5:
        errors.append("风险等级配置不完整")

    # 检查权益配置限制
    if WEALTH_PRODUCT_CONFIG['max_equity_ratio'] > 1:
        errors.append("最大权益比例配置错误")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # 验证配置
    is_valid, errors = validate_config()
    if is_valid:
        print("配置验证通过")
    else:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")

    # 打印关键配置
    print("\n关键配置摘要:")
    print(f"数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"风险等级: {list(RISK_CLASSES.keys())}")
    print(f"最大权益比例: {WEALTH_PRODUCT_CONFIG['max_equity_ratio']:.0%}")
