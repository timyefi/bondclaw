# -*- coding: utf-8 -*-
"""
T15-国债收益率走势阶段分析 配置文件

该模块包含数据库连接配置和分析参数设置。
所有敏感信息通过环境变量获取，无硬编码密码。
"""

import os
from datetime import datetime

# =============================================================================
# 数据库配置
# =============================================================================

# 从环境变量获取数据库配置
DB_USER = os.getenv('DB_USER', 'hz_work')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'yq')

# 数据库连接URL
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# =============================================================================
# 分析参数配置
# =============================================================================

# 数据查询日期范围
START_DATE = os.getenv('START_DATE', '2014-01-01')
END_DATE = os.getenv('END_DATE', datetime.now().strftime('%Y-%m-%d'))

# 移动平均线窗口
MA_SHORT_WINDOW = int(os.getenv('MA_SHORT_WINDOW', '20'))  # 短期均线（20日）
MA_LONG_WINDOW = int(os.getenv('MA_LONG_WINDOW', '60'))    # 长期均线（60日）

# 债券类型筛选条件
BOND_CLASSIFY2 = '中债国债到期收益率'
BOND_NAME_PATTERN = '%10年%'  # 10年期国债

# =============================================================================
# 输出配置
# =============================================================================

# 输出文件名
OUTPUT_FILENAME = '收益率下行周期标注.csv'

# 图表配置
CHART_CONFIG = {
    'figsize': (15, 8),
    'title': '10年期国债收益率走势图 (点击标注起点和终点)',
    'xlabel': '日期',
    'ylabel': '收益率(%)',
    'line_width_raw': 1.5,
    'line_width_ma': 2,
    'alpha_raw': 0.6,
    'grid_alpha': 0.6,
}

# 颜色配置
COLORS = {
    'yield_line': 'gray',
    'ma20': 'orange',
    'ma60': 'blue',
    'marker': 'red',
    'marker_edge': 'white',
    'annotation_bg': 'yellow',
    'annotation_edge': 'blue',
}

# =============================================================================
# SQL查询模板
# =============================================================================

def get_yield_query(start_date: str, end_date: str) -> str:
    """
    生成10年期国债收益率查询SQL

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        SQL查询字符串
    """
    query = f"""
    SELECT
        A.dt,
        A.CLOSE AS 收益率
    FROM bond.marketinfo_curve A
    INNER JOIN bond.basicinfo_curve B
    ON A.trade_code = B.TRADE_CODE
    WHERE A.dt BETWEEN '{start_date}' AND '{end_date}'
        AND B.classify2 = '{BOND_CLASSIFY2}'
        AND B.SEC_NAME LIKE '{BOND_NAME_PATTERN}'
    ORDER BY A.dt
    """
    return query
