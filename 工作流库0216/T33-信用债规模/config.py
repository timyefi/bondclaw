# -*- coding: utf-8 -*-
"""
T33 - 信用债规模 配置文件

此配置文件使用环境变量管理敏感信息，避免硬编码密码。
使用前请设置以下环境变量：
- MYSQL_HOST: MySQL主机地址
- MYSQL_PORT: MySQL端口
- MYSQL_USER: MySQL用户名
- MYSQL_PASSWORD: MySQL密码
- PG_HOST: PostgreSQL主机地址
- PG_PORT: PostgreSQL端口
- PG_USER: PostgreSQL用户名
- PG_PASSWORD: PostgreSQL密码
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import sqlalchemy

# ============================================================
# 项目路径配置
# ============================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / 'data'

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / 'output'

# 源代码目录
SRC_DIR = PROJECT_ROOT / 'src'

# =============================================================================
# 数据库配置
# =============================================================================

# MySQL配置 - 从环境变量获取
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': int(os.environ.get('MYSQL_PORT', '3306')),
    'user': os.environ.get('MYSQL_USER', 'hz_work'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),  # 必须通过环境变量设置
    'database': os.environ.get('MYSQL_DATABASE', 'bond'),
}

# PostgreSQL配置 - 从环境变量获取
PG_CONFIG = {
    'host': os.environ.get('PG_HOST', '139.224.107.113'),
    'port': int(os.environ.get('PG_PORT', '18032')),
    'user': os.environ.get('PG_USER', 'postgres'),
    'password': os.environ.get('PG_PASSWORD', ''),  # 必须通过环境变量设置
    'database': os.environ.get('PG_DATABASE', 'tsdb'),
}


def get_mysql_connection_string() -> str:
    """获取MySQL连接字符串"""
    if not MYSQL_CONFIG['password']:
        raise ValueError("MYSQL_PASSWORD环境变量未设置，请先设置数据库密码")
    return (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
        f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )


def get_pg_connection_string() -> str:
    """获取PostgreSQL连接字符串"""
    if not PG_CONFIG['password']:
        raise ValueError("PG_PASSWORD环境变量未设置，请先设置数据库密码")
    return (
        f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}"
        f"@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
    )


def get_mysql_engine():
    """
    获取MySQL数据库引擎

    Returns:
        sqlalchemy.Engine: MySQL数据库引擎
    """
    connection_string = get_mysql_connection_string()
    engine = sqlalchemy.create_engine(
        connection_string,
        poolclass=sqlalchemy.pool.NullPool,
        pool_recycle=3600,
        echo=False
    )
    return engine


def get_postgres_engine():
    """
    获取PostgreSQL数据库引擎

    Returns:
        sqlalchemy.Engine: PostgreSQL数据库引擎
    """
    connection_string = get_pg_connection_string()
    engine = sqlalchemy.create_engine(
        connection_string,
        pool_recycle=3600,
        echo=False
    )
    return engine


# 导出配置常量供Notebook使用
MAJOR_TYPES = CLASSIFICATION_CONFIG['major_types']
RATING_LEVELS = CLASSIFICATION_CONFIG['rating_levels']
DURATION_THRESHOLDS = TERM_THRESHOLDS


# =============================================================================
# 分类配置
# =============================================================================

# 债券分类配置
CLASSIFICATION_CONFIG: Dict[str, Any] = {
    # 债券大类
    'major_types': ['城投', '产业', '金融', 'ABS'],

    # 金融机构子类
    'finance_subtypes': ['银行', '证券', '保险', '其他非银金融机构'],

    # 评级级别
    'rating_levels': ['AAA', 'AA+', 'AA', 'AA-', 'A', '其他', '无评级'],

    # 数据源表
    'data_sources': {
        'basicinfo': ['basicinfo_credit', 'basicinfo_finance', 'basicinfo_abs'],
        'marketinfo': ['marketinfo_credit', 'marketinfo_finance', 'marketinfo_abs']
    }
}

# 久期分段阈值配置
TERM_THRESHOLDS: Dict[float, float] = {
    0.5: 0.75,   # 久期 < 0.75年 -> 0.5年
    1: 1.5,      # 久期 < 1.5年 -> 1年
    2: 2.5,      # 久期 < 2.5年 -> 2年
    3: 3.5,      # 久期 < 3.5年 -> 3年
    4: 4.5,      # 久期 < 4.5年 -> 4年
    5: 6,        # 久期 < 6年 -> 5年
    7: 8,        # 久期 < 8年 -> 7年
    10: float('inf')  # 久期 >= 8年 -> 10年
}


def classify_term(duration: float) -> float:
    """
    根据久期分类期限

    Parameters:
    -----------
    duration : float
        久期值（年）

    Returns:
    --------
    float
        分类后的期限标签
    """
    if duration is None:
        return None
    for label, upper in TERM_THRESHOLDS.items():
        if duration < upper:
            return label
    return 10


# =============================================================================
# 集中度分析配置
# =============================================================================

CONCENTRATION_CONFIG: Dict[str, float] = {
    'high': 0.3,      # HHI > 0.3 为高度集中
    'medium': 0.2,    # HHI > 0.2 为中度集中
    'low': 0.1,       # HHI > 0.1 为低度集中
}


def get_concentration_level(hhi: float) -> str:
    """
    根据HHI指数判断集中度级别

    Parameters:
    -----------
    hhi : float
        HHI指数值

    Returns:
    --------
    str
        集中度级别
    """
    if hhi > CONCENTRATION_CONFIG['high']:
        return '高度集中'
    elif hhi > CONCENTRATION_CONFIG['medium']:
        return '中度集中'
    elif hhi > CONCENTRATION_CONFIG['low']:
        return '低度集中'
    else:
        return '分散'


# =============================================================================
# 邮件告警配置
# =============================================================================

ALERT_CONFIG: Dict[str, Any] = {
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.example.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', '25')),
    'smtp_user': os.environ.get('SMTP_USER', ''),
    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
    'alert_recipients': os.environ.get('ALERT_RECIPIENTS', '').split(',') if os.environ.get('ALERT_RECIPIENTS') else [],
    'webhook_url': os.environ.get('WEBHOOK_URL', ''),
}


# =============================================================================
# 日志配置
# =============================================================================

LOG_CONFIG: Dict[str, Any] = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'credit_scale_etl.log',
    'encoding': 'utf-8',
}


# =============================================================================
# 数据质量配置
# =============================================================================

DATA_QUALITY_CONFIG: Dict[str, Any] = {
    'max_delay_days': 1,        # 最大数据延迟天数
    'max_null_ratio': 0.1,      # 最大空值比例
    'min_completeness': 0.95,   # 最小数据完整性
}


# =============================================================================
# 规模统计查询配置
# =============================================================================

# 分类方式列表
CATEGORY_TYPES: List[str] = [
    '大类',      # 按债券大类分类
    '省',        # 城投债按省份分类
    '市',        # 城投债按城市分类
    '申万一级',  # 产业债按申万一级行业分类
    '申万行业',  # 产业债按申万行业分类
    '一级分类',  # 产业债按一级分类
    '二级分类',  # 产业债按二级分类
    '金融机构',  # 金融债按机构类型分类
    '资产',      # ABS按基础资产类型分类
    '评级',      # 按评级分类
    '久期',      # 按久期段分类
]


# =============================================================================
# 验证函数
# =============================================================================

def validate_config() -> bool:
    """
    验证配置是否完整

    Returns:
    --------
    bool
        配置是否有效
    """
    errors = []

    # 检查MySQL密码
    if not MYSQL_CONFIG['password']:
        errors.append("MYSQL_PASSWORD环境变量未设置")

    # 检查必要的配置
    if not MYSQL_CONFIG['host']:
        errors.append("MYSQL_HOST未设置")

    if not MYSQL_CONFIG['database']:
        errors.append("MYSQL_DATABASE未设置")

    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


# =============================================================================
# 示例使用
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("T33 - 信用债规模 配置文件")
    print("=" * 60)

    print("\n数据库配置:")
    print(f"  MySQL主机: {MYSQL_CONFIG['host']}")
    print(f"  MySQL端口: {MYSQL_CONFIG['port']}")
    print(f"  MySQL用户: {MYSQL_CONFIG['user']}")
    print(f"  MySQL数据库: {MYSQL_CONFIG['database']}")
    print(f"  MySQL密码: {'已设置' if MYSQL_CONFIG['password'] else '未设置'}")

    print("\n分类配置:")
    print(f"  债券大类: {CLASSIFICATION_CONFIG['major_types']}")
    print(f"  评级级别: {CLASSIFICATION_CONFIG['rating_levels']}")

    print("\n久期分段阈值:")
    for label, upper in TERM_THRESHOLDS.items():
        if upper == float('inf'):
            print(f"  {label}年: >= 8年")
        else:
            print(f"  {label}年: < {upper}年")

    print("\n配置验证:")
    if validate_config():
        print("  配置有效")
    else:
        print("  配置无效，请检查环境变量")
