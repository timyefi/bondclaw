# -*- coding: utf-8 -*-
"""
T05 对冲策略配置文件

包含数据库配置、分析参数配置和可视化配置
"""

import os

# ============================================================
# 数据库配置
# ============================================================

# 使用环境变量获取敏感信息，提供默认值用于开发环境
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 从环境变量获取密码
DB_NAME = os.environ.get('DB_NAME', 'yq')
DB_CHARSET = 'utf8'

DB_CONFIG = {
    'host': DB_HOST,
    'port': DB_PORT,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'charset': DB_CHARSET
}


def get_database_url():
    """
    生成数据库连接URL

    返回:
        str: SQLAlchemy格式的数据库连接URL
    """
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


# ============================================================
# 分析参数配置
# ============================================================

ANALYSIS_CONFIG = {
    # 回测参数
    'backtest': {
        'start_date': '2023-01-14',
        'hedge_ratios': [0, 0.25, 0.5, 0.75, 1.0],
        'lookback_period': 20
    },

    # 异常值处理
    'outlier': {
        'max_return': 0.2,  # 单日最大收益率20%
        'method': 'remove'
    },

    # 风险计算
    'risk': {
        'var_confidence': [0.95, 0.99],
        'drawdown_window': 252,  # 一年交易日
        'downside_risk_threshold': 0
    },

    # 权重配置
    'weights': {
        'base_weight': 0.6,  # 基础权重
        'min_weight': 0.3,   # 最小权重
        'max_weight': 0.8,   # 最大权重
        'corr_adjust': -0.2, # 相关性调整系数
        'mom_adjust': 0.1,   # 动量调整系数
        'vol_adjust': -0.1   # 波动率调整系数
    }
}


# ============================================================
# 可视化配置
# ============================================================

VIZ_CONFIG = {
    # 图表样式
    'style': {
        'font': 'SimHei',
        'figsize': (16, 10),
        'dpi': 300
    },

    # 颜色配置
    'colors': {
        'asset1': '#1f77b4',  # 标的1颜色
        'asset2': '#ff7f0e',  # 标的2颜色
        'hedge': '#2ca02c',   # 对冲策略颜色
        'risk': '#d62728',    # 风险指标颜色
        'positive': '#27ae60', # 正值颜色
        'negative': '#e74c3c'  # 负值颜色
    },

    # 图表类型
    'chart_types': [
        'price_trend',         # 价格走势
        'return_comparison',   # 收益率对比
        'volatility_comparison', # 波动率对比
        'correlation_trend',   # 相关性走势
        'backtest_results',    # 策略回测
        'risk_metrics'         # 风险指标
    ],

    # Plotly配置
    'plotly': {
        'height': 600,
        'margin': dict(r=100, t=50, b=50),
        'hovermode': 'x unified'
    }
}


# ============================================================
# 默认标的配置
# ============================================================

DEFAULT_ASSETS = {
    '城投ETF_黄金ETF': {
        'trade_code1': '511220.SH',
        'trade_code2': '518880.SH',
        'name1': '城投ETF',
        'name2': '黄金ETF'
    },
    '国债ETF_黄金ETF': {
        'trade_code1': '511010.SH',
        'trade_code2': '518880.SH',
        'name1': '国债ETF',
        'name2': '黄金ETF'
    }
}


# ============================================================
# 路径配置
# ============================================================

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PATH_CONFIG = {
    'base_dir': BASE_DIR,
    'src_dir': os.path.join(BASE_DIR, 'src'),
    'data_dir': os.path.join(BASE_DIR, 'data'),
    'assets_dir': os.path.join(BASE_DIR, 'assets'),
    'output_dir': os.path.join(BASE_DIR, 'output')
}


# ============================================================
# 日志配置
# ============================================================

LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.path.join(PATH_CONFIG['output_dir'], 'hedge_strategy.log')
}


if __name__ == '__main__':
    print("数据库配置:", DB_CONFIG)
    print("数据库URL:", get_database_url())
    print("分析配置:", ANALYSIS_CONFIG)
