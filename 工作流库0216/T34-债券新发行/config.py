# -*- coding: utf-8 -*-
"""
T34 - 债券新发行配置文件

使用环境变量获取敏感配置，避免硬编码密码
"""

import os
from pathlib import Path

# =============================================================================
# 项目路径配置
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
LOG_DIR = PROJECT_ROOT / 'logs'

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 数据库配置 - 从环境变量获取
# =============================================================================
# MySQL配置 (yq数据库)
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
MYSQL_USER = os.environ.get('MYSQL_USER', 'hz_work')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # 必须从环境变量获取
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'yq')

# =============================================================================
# API配置 - 从环境变量获取
# =============================================================================
# Wind API配置
WIND_USERNAME = os.environ.get('WIND_USERNAME', '')
WIND_PASSWORD = os.environ.get('WIND_PASSWORD', '')

# 同花顺iFinD API配置
IFIND_USERNAME = os.environ.get('IFIND_USERNAME', '')
IFIND_PASSWORD = os.environ.get('IFIND_PASSWORD', '')

# =============================================================================
# 业务参数配置
# =============================================================================
# 债券到期数据采集配置
BOND_MATURITY_CONFIG = {
    'days_ahead': 7,  # 获取未来7天的数据
    'table_name': '债券到期',
    'database': 'yq'
}

# 债券新发行数据采集配置
BOND_ISSUE_CONFIG = {
    'days_start': 1,   # 从明天开始
    'days_end': 30,    # 到未来30天
    'table_name': '债券新发行1',
    'database': 'yq'
}

# 债券类型配置 (Wind API)
BOND_TYPES = [
    # (Wind类型代码, 中文名称, 是否城投债)
    ('governmentbonds', '国债', '否'),
    ('centralbankbills', '央行票据', '否'),
    ('cds', '存单', '否'),
    ('commercialbankbonds', '普通金融债', '否'),
    ('policybankbonds', '政策银行债', '否'),
    ('commercialbanksubordinatedbonds', '商业银行次级债券', '否'),
    ('insurancecompanybonds', '保险债', '否'),
    ('corporatebondsofsecuritiescompany', '证券公司债', '否'),
    ('securitiescompanycps', '证券公司短融债', '否'),
    ('otherfinancialagencybonds', '其他金融机构债', '否'),
    ('enterprisebonds', '企业债', '否'),
    ('enterprisebonds', '企业债', '是'),  # 城投
    ('corporatebonds', '公司债', '否'),
    ('corporatebonds', '公司债', '是'),   # 城投
    ('medium-termnotes', '中期票据', '否'),
    ('medium-termnotes', '中期票据', '是'),  # 城投
    ('cps', '短期融资券', '否'),
    ('cps', '短期融资券', '是'),  # 城投
    ('projectrevenuenotes', '项目收益票据', '否'),
    ('ppn', 'PPN', '否'),
    ('ppn', 'PPN', '是'),  # 城投
    ('supranationalbonds', '国际机构债', '否'),
    ('agencybonds', '政府支持机构债', '否'),
    ('standardizednotes', '标准化票据', '否'),
    ('abs', 'ABS', '否'),
    ('convertiblebonds', '可转债', '否'),
    ('exchangeablebonds', '可交换债', '否'),
    ('detachableconvertiblebonds', '可分离转债', '否'),
]

# 同花顺债券类型代码
IFIND_BOND_TYPES = '640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024'

# =============================================================================
# 日志配置
# =============================================================================
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# =============================================================================
# 辅助函数
# =============================================================================
def get_mysql_connection_string():
    """生成MySQL连接字符串"""
    return f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'


def validate_config():
    """验证配置是否完整"""
    errors = []

    if not MYSQL_PASSWORD:
        errors.append('MYSQL_PASSWORD 环境变量未设置')

    if not IFIND_USERNAME or not IFIND_PASSWORD:
        errors.append('IFIND_USERNAME 或 IFIND_PASSWORD 环境变量未设置')

    if errors:
        print('配置警告:')
        for error in errors:
            print(f'  - {error}')
        print('部分功能可能无法正常工作')
        return False

    return True


# 打印配置摘要
def print_config_summary():
    """打印配置摘要（不包含敏感信息）"""
    print('=== T34 债券新发行 配置摘要 ===')
    print(f'项目根目录: {PROJECT_ROOT}')
    print(f'数据目录: {DATA_DIR}')
    print(f'输出目录: {OUTPUT_DIR}')
    print(f'日志目录: {LOG_DIR}')
    print(f'MySQL主机: {MYSQL_HOST}:{MYSQL_PORT}')
    print(f'MySQL数据库: {MYSQL_DATABASE}')
    print(f'债券类型数量: {len(BOND_TYPES)}')
    print(f'Wind API配置: {"已配置" if WIND_USERNAME else "未配置"}')
    print(f'iFinD API配置: {"已配置" if IFIND_USERNAME else "未配置"}')
    print('=' * 40)


if __name__ == '__main__':
    print_config_summary()
    validate_config()
