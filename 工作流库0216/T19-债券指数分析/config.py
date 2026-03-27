# -*- coding: utf-8 -*-
"""
T19 - 债券指数分析配置文件

该配置文件包含债券指数分析项目所需的所有配置参数。
所有敏感信息通过环境变量获取。
"""

import os
from typing import Dict, List

# ===================== 数据库配置 =====================
# 通过环境变量获取敏感信息，避免硬编码

DB_CONFIG = {
    'user': os.environ.get('DB_USER', ''),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': os.environ.get('DB_PORT', '3306'),
    'database': os.environ.get('DB_NAME', 'bond'),
}


def get_connection_string() -> str:
    """
    生成数据库连接字符串

    Returns:
        str: 数据库连接字符串
    """
    return f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"


# ===================== 分析参数配置 =====================

ANALYSIS_CONFIG = {
    # 时间周期定义（天）
    'periods': {
        '30天': 30,
        '3个月': 90,
        '半年': 180,
        '1年': 365
    },

    # 默认分析周期
    'default_period': '1年',

    # 分组参数
    'return_bin_size': 0.5,      # 收益率分组区间大小 (%)
    'duration_bin_size': 0.5,    # 久期分组区间大小 (年)
    'drawdown_bin_size': 0.5,    # 最大回撤分组区间大小 (%)

    # 组合优化参数
    'max_portfolio_size': 10,    # 最大组合规模
    'max_combinations': 10000,   # 最大组合数
    'min_combo_size': 3,         # 最小组合规模

    # 指标显示配置
    'top_n_indices': 10,         # Top N 显示数量
}


# ===================== 可视化配置 =====================

VISUALIZATION_CONFIG = {
    # 图表尺寸
    'figure_width': 12,
    'figure_height': 8,
    'dpi': 100,

    # 样式配置
    'plot_style': 'whitegrid',       # seaborn 样式
    'color_palette': 'viridis',      # 调色板

    # 字体配置
    'chinese_fonts': ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'sans-serif'],

    # Plotly配置
    'plotly_theme': 'plotly_white',

    # 图表标签映射
    'metric_labels': {
        'return': '收益率 (%)',
        'max_drawdown': '最大回撤 (%)',
        'volatility': '年化波动率 (%)',
        'duration': '久期 (年)'
    },
}


# ===================== 输出配置 =====================

OUTPUT_CONFIG = {
    # 输出目录
    'output_dir': './output',
    'plot_dir': './output/portfolio_plots',

    # 文件命名
    'results_file': 'bond_indices_results.csv',
    'return_group_file': 'return_group_analysis.csv',
    'duration_group_file': 'duration_group_analysis.csv',
    'portfolio_prefix': 'portfolio_optimization_',
    'three_dim_prefix': 'three_dim_analysis_',
    'summary_html': 'summary_table_styled.html',

    # 编码
    'encoding': 'utf-8-sig',
}


# ===================== SQL查询配置 =====================

SQL_CONFIG = {
    # 获取债券指数信息
    'get_indices': """
        SELECT trade_code, index_name, duration
        FROM bond.indexcode
        WHERE index_name LIKE '%%财富%%'
        AND duration IS NOT NULL
    """,

    # 获取价格数据模板
    'get_price_template': """
        SELECT DT AS date, CLOSE AS price
        FROM bond.indexcloseprice
        WHERE TRADE_CODE = '{trade_code}'
        AND DT <= '{end_date}'
        AND DT >= '{start_date}'
        ORDER BY DT
    """,
}


# ===================== 完整配置对象 =====================

class Config:
    """配置类，整合所有配置"""

    def __init__(self):
        self.db = DB_CONFIG
        self.analysis = ANALYSIS_CONFIG
        self.visualization = VISUALIZATION_CONFIG
        self.output = OUTPUT_CONFIG
        self.sql = SQL_CONFIG

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return get_connection_string()

    def ensure_output_dirs(self):
        """确保输出目录存在"""
        os.makedirs(self.output['output_dir'], exist_ok=True)
        os.makedirs(self.output['plot_dir'], exist_ok=True)


# 创建全局配置实例
config = Config()


# ===================== 使用示例 =====================

if __name__ == "__main__":
    print("=" * 50)
    print("T19 - 债券指数分析配置")
    print("=" * 50)

    print("\n数据库配置:")
    print(f"  主机: {config.db['host']}")
    print(f"  端口: {config.db['port']}")
    print(f"  数据库: {config.db['database']}")

    print("\n分析周期:")
    for period, days in config.analysis['periods'].items():
        print(f"  {period}: {days}天")

    print("\n输出目录:")
    print(f"  输出目录: {config.output['output_dir']}")
    print(f"  图表目录: {config.output['plot_dir']}")

    print("\n" + "=" * 50)
    print("提示: 请确保已设置必要的环境变量")
    print("  - DB_USER: 数据库用户名")
    print("  - DB_PASSWORD: 数据库密码")
    print("=" * 50)
