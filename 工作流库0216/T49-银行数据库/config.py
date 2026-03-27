# -*- coding: utf-8 -*-
"""
银行数据库配置文件
Configuration for Bank Database

任务编号: T49
任务名称: 银行数据库
"""

import os
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# ============================================================
# 数据文件配置
# ============================================================

# 主数据文件
MAIN_DATA_FILE = '银行数据库2024.xlsx'

# 备份数据文件
BACKUP_DATA_FILE = '副本银行数据库2024 - 副本.xlsx'

# 模板文件
TEMPLATE_FILE = '银行.xlsx'

# ============================================================
# 数据库配置
# ============================================================

# 数据库连接参数（使用环境变量，避免硬编码敏感信息）
DATABASE_HOST = os.environ.get('DB_HOST', 'localhost')
DATABASE_PORT = int(os.environ.get('DB_PORT', 3306))
DATABASE_USER = os.environ.get('DB_USER', 'root')
DATABASE_PASSWORD = os.environ.get('DB_PASSWORD', '')
DATABASE_NAME = os.environ.get('DB_NAME', 'yq')

# 目标表名
TABLE_NAME = '银行数据库'

# 数据库连接URL
def get_database_url():
    """
    获取数据库连接URL

    Returns
    -------
    str
        SQLAlchemy格式的数据库连接URL
    """
    return f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"

# ============================================================
# 数据字段配置
# ============================================================

# 必需字段
REQUIRED_COLUMNS = ['dt1', '发行人']

# 数值字段
NUMERIC_COLUMNS = [
    '总资产',
    '资本充足率',
    '净息差',
    '不良率',
    'ROE',
    '存款占比',
    '拨备覆盖率'
]

# 所有字段
ALL_COLUMNS = REQUIRED_COLUMNS + NUMERIC_COLUMNS

# ============================================================
# 数据验证配置
# ============================================================

# 数值范围验证规则
VALIDATION_RANGES = {
    '资本充足率': (0, 50),      # 资本充足率范围：0-50%
    '不良率': (0, 20),          # 不良贷款率范围：0-20%
    'ROE': (-50, 50),           # 净资产收益率范围：-50%到50%
    '净息差': (-5, 10),         # 净息差范围：-5%到10%
    '存款占比': (0, 100),       # 存款占比范围：0-100%
    '拨备覆盖率': (0, 1000),    # 拨备覆盖率范围：0-1000%
}

# ============================================================
# 日志配置
# ============================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================
# 其他配置
# ============================================================

# 数据导入批处理大小
BATCH_SIZE = 1000

# 日期格式
DATE_FORMAT = '%Y-%m-%d'

# 编码
ENCODING = 'utf-8'


def print_config():
    """打印当前配置信息（隐藏敏感信息）"""
    print("=" * 50)
    print("银行数据库配置信息")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"数据目录: {DATA_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"主数据文件: {MAIN_DATA_FILE}")
    print(f"数据库主机: {DATABASE_HOST}")
    print(f"数据库端口: {DATABASE_PORT}")
    print(f"数据库名称: {DATABASE_NAME}")
    print(f"目标表名: {TABLE_NAME}")
    print(f"日志级别: {LOG_LEVEL}")
    print("=" * 50)


if __name__ == '__main__':
    print_config()
