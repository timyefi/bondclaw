# -*- coding: utf-8 -*-
"""
城投区域分析 - 配置文件

注意: 敏感信息请使用环境变量，不要在代码中硬编码密码
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# =============================================================================
# 数据库配置
# =============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),  # 请在环境变量中设置
    'database': os.getenv('DB_NAME', 'bond'),
    'charset': 'utf8'
}

# SQLAlchemy连接字符串
def get_db_connection_string():
    """获取数据库连接字符串"""
    return 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database']
    )


# =============================================================================
# Wind API配置
# =============================================================================

WIND_CONFIG = {
    'username': os.getenv('WIND_USERNAME', ''),
    'password': os.getenv('WIND_PASSWORD', '')
}


# =============================================================================
# 同花顺iFinD配置
# =============================================================================

THS_CONFIG = {
    'host': os.getenv('THS_HOST', ''),
    'port': int(os.getenv('THS_PORT', 8080)),
    'username': os.getenv('THS_USERNAME', ''),
    'password': os.getenv('THS_PASSWORD', '')
}


# =============================================================================
# 评级参数配置
# =============================================================================

RATING_CONFIG = {
    '区域评级': {
        'weights': {
            '财政实力': 0.30,
            '债务负担': 0.30,
            '经济活力': 0.20,
            '金融支持': 0.10,
            '政策环境': 0.10
        },
        'thresholds': {
            'AAA': 90,
            'AA+': 80,
            'AA': 70,
            'AA-': 60,
            'A': 0
        }
    },
    '平台评级': {
        'weights': {
            '股东背景': 0.25,
            '区域风险': 0.25,
            '财务状况': 0.25,
            '市场表现': 0.15,
            '增信情况': 0.10
        },
        'thresholds': {
            'AAA': 90,
            'AA+': 80,
            'AA': 70,
            'AA-': 60,
            'A': 0
        }
    }
}


# =============================================================================
# 可视化配置
# =============================================================================

VIZ_CONFIG = {
    'style': 'seaborn',
    'figsize': (16, 10),
    'dpi': 300,
    'font': 'SimHei',
    'color_palette': {
        'AAA': '#1f77b4',
        'AA+': '#ff7f0e',
        'AA': '#2ca02c',
        'AA-': '#d62728',
        'A': '#9467bd'
    }
}


# =============================================================================
# 数据质量配置
# =============================================================================

DATA_QUALITY_CONFIG = {
    'completeness_threshold': 0.95,  # 数据完整性阈值
    'accuracy_threshold': 0.99,      # 数据准确性阈值
    'update_days': 3,                # 数据更新天数阈值
}


# =============================================================================
# 路径配置
# =============================================================================

import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# 资源目录
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')


# =============================================================================
# 辅助函数
# =============================================================================

def ensure_directories():
    """确保所有必要的目录存在"""
    for dir_path in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
        os.makedirs(dir_path, exist_ok=True)


if __name__ == '__main__':
    # 测试配置
    print("数据库配置:", DB_CONFIG)
    print("评级配置:", RATING_CONFIG)
    print("项目根目录:", PROJECT_ROOT)
    ensure_directories()
    print("目录创建完成")
