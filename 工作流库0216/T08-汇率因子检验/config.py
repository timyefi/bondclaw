# -*- coding: utf-8 -*-
"""
T08 - 汇率因子检验 配置文件

配置数据库连接、分析参数和可视化设置
"""

import os
from datetime import datetime

# =============================================================================
# 数据库配置
# =============================================================================

# 使用环境变量存储敏感信息，如果环境变量不存在则使用默认值
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': os.environ.get('DB_PORT', '3306'),
    'user': os.environ.get('DB_USER', 'hz_work'),
    'password': os.environ.get('DB_PASSWORD', ''),  # 密码从环境变量获取
    'database': os.environ.get('DB_DATABASE', 'yq'),
}

# PostgreSQL连接配置（备用）
PG_CONFIG = {
    'host': os.environ.get('PG_HOST', '139.224.107.113'),
    'port': os.environ.get('PG_PORT', '18032'),
    'user': os.environ.get('PG_USER', 'postgres'),
    'password': os.environ.get('PG_PASSWORD', ''),
    'database': os.environ.get('PG_DATABASE', 'tsdb'),
}

# =============================================================================
# 分析配置
# =============================================================================

ANALYSIS_CONFIG = {
    # 时间范围
    'start_date': '2015-01-01',
    'end_date': datetime.now().strftime('%Y-%m-%d'),

    # 相关性分析参数
    'rolling_window': 60,  # 滚动窗口（交易日）
    'correlation_threshold': 0.5,  # 高相关性阈值

    # 相关性计算方法
    'correlation_methods': ['pearson', 'spearman', 'kendall'],

    # Granger因果检验
    'granger_max_lag': 5,  # 最大滞后阶数
    'significance_level': 0.05,  # 显著性水平
}

# =============================================================================
# 数据配置
# =============================================================================

DATA_CONFIG = {
    # 汇率数据（因变量）
    'exchange_rate': {
        'trade_code': 'M0067855',  # 人民币兑美元即期汇率
        'name': 'USD_CNY'
    },

    # 目标因子数据
    'factors': {
        'DR007': {
            'trade_code': 'M1006337',
            'table': 'edb.edbdata',
            'description': '银行间7天质押式回购利率'
        },
        'GC007': {
            'trade_code': 'M1004515',
            'table': 'edb.edbdata',
            'description': '上交所7天国债逆回购利率'
        },
        'CSI300': {
            'trade_code': 'M0020209',
            'table': 'edb.edbdata',
            'description': '沪深300指数'
        },
        'WIND_ALL_A': {
            'trade_code': '881001.WI',
            'table': 'stock.indexcloseprice',
            'description': '万得全A指数'
        },
        'SME_INDEX': {
            'trade_code': '399101.SZ',
            'table': 'stock.indexcloseprice',
            'description': '中小板指'
        },
        'HANG_SENG': {
            'trade_code': 'HSCI.HI',
            'table': 'stock.indexcloseprice',
            'description': '恒生指数'
        },
        'BOND_10Y': {
            'trade_code': 'L001619604',
            'table': 'bond.marketinfo_curve',
            'description': '10年国债收益率'
        },
        'BOND_1Y': {
            'trade_code': 'L001618296',
            'table': 'bond.marketinfo_curve',
            'description': '1年国债收益率'
        },
        'URBAN_BOND_5Y': {
            'trade_code': 'L003759264',
            'table': 'bond.marketinfo_curve',
            'description': '5年城投债收益率'
        }
    }
}

# =============================================================================
# 可视化配置
# =============================================================================

VIZ_CONFIG = {
    'style': 'plotly_white',
    'figsize': (14, 8),
    'height': 600,
    'template': 'plotly_white',
    'font_family': 'Microsoft YaHei',
    'color_palette': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ],
    'data_source_text': '数据来源：弘则研究，WIND，同花顺'
}

# =============================================================================
# 路径配置
# =============================================================================

PATH_CONFIG = {
    'output_dir': 'output',
    'data_dir': 'data',
    'assets_dir': 'assets',
    'cache_file': 'processed_data.parquet',
    'report_file': 'correlation_analysis.html'
}

# =============================================================================
# 辅助函数
# =============================================================================

def get_db_connection_string():
    """获取数据库连接字符串"""
    return 'mysql+pymysql://%s:%s@%s:%s/%s' % (
        DB_CONFIG['user'],
        DB_CONFIG['password'],
        DB_CONFIG['host'],
        DB_CONFIG['port'],
        DB_CONFIG['database']
    )

def get_pg_connection_string():
    """获取PostgreSQL连接字符串"""
    return 'postgresql://%s:%s@%s:%s/%s' % (
        PG_CONFIG['user'],
        PG_CONFIG['password'],
        PG_CONFIG['host'],
        PG_CONFIG['port'],
        PG_CONFIG['database']
    )

def ensure_output_dirs():
    """确保输出目录存在"""
    for dir_name in [PATH_CONFIG['output_dir'], PATH_CONFIG['data_dir'], PATH_CONFIG['assets_dir']]:
        os.makedirs(dir_name, exist_ok=True)

if __name__ == '__main__':
    print("T08 - 汇率因子检验 配置文件")
    print("="*50)
    print(f"数据时间范围: {ANALYSIS_CONFIG['start_date']} 至 {ANALYSIS_CONFIG['end_date']}")
    print(f"滚动窗口: {ANALYSIS_CONFIG['rolling_window']} 天")
    print(f"高相关性阈值: {ANALYSIS_CONFIG['correlation_threshold']}")
    print(f"因子数量: {len(DATA_CONFIG['factors'])}")
