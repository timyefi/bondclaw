"""
区域基本面 - 配置文件
任务ID: T40
创建时间: 2026-02-15
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / 'data'

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / 'output'

# 数据库配置（使用环境变量）
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# 区域配置
FISCAL_WEIGHTS = {
    'general_budget': 0.7,
    'gov_fund': 0.3
}

DEBT_WARNING_LEVELS = {
    'debt_to_gdp': 0.6,
    'debt_to_fiscal': 2.0,
    'debt_growth': 0.2
}

GROWTH_TARGETS = {
    'high_growth': 8.0,
    'medium_growth': 6.0,
    'low_growth': 4.0
}

# 城投债务估算系数（当数据缺失时使用）
LGD_DEBT_MULTIPLIER = 2.0

# 风险评级阈值
RISK_RATING_THRESHOLDS = {
    'AAA': {'min_score': 80, 'max_debt_to_fiscal': 1.0},
    'AA+': {'min_score': 70, 'max_debt_to_fiscal': 1.5},
    'AA': {'min_score': 60, 'max_debt_to_fiscal': 2.0},
    'AA-': {'min_score': 50, 'max_debt_to_fiscal': 3.0},
    'A': {'min_score': 40, 'max_debt_to_fiscal': float('inf')},
    'BBB': {'min_score': 30, 'max_debt_to_fiscal': float('inf')},
    'BB': {'min_score': 0, 'max_debt_to_fiscal': float('inf')}
}

# 评分权重
SCORE_WEIGHTS = {
    'fiscal': 0.4,
    'economy': 0.3,
    'potential': 0.3
}
