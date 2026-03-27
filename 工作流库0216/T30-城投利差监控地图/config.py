# -*- coding: utf-8 -*-
"""
城投利差监控地图 - 配置文件

该模块包含项目的所有配置参数，包括：
- 数据库连接配置
- 日期参数
- 目标期限设置
- 路径配置
"""

import os
from datetime import datetime, timedelta
from pathlib import Path


class Config:
    """
    项目配置类

    使用环境变量处理敏感信息，提供默认值作为后备
    """

    def __init__(self):
        # ==================== 路径配置 ====================
        self.project_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.src_dir = self.project_dir / 'src'
        self.data_dir = self.project_dir / 'data'
        self.output_dir = self.project_dir / 'output'
        self.assets_dir = self.project_dir / 'assets'

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ==================== 数据库配置 ====================
        # MySQL (bond) 数据库配置
        self.bond_db_host = os.environ.get('BOND_DB_HOST', 'localhost')
        self.bond_db_port = int(os.environ.get('BOND_DB_PORT', '3306'))
        self.bond_db_name = os.environ.get('BOND_DB_NAME', 'bond')
        self.bond_db_user = os.environ.get('BOND_DB_USER', 'root')
        self.bond_db_password = os.environ.get('BOND_DB_PASSWORD', '')

        # PostgreSQL (tsdb) 数据库配置
        self.tsdb_host = os.environ.get('TSDB_HOST', 'localhost')
        self.tsdb_port = int(os.environ.get('TSDB_PORT', '5432'))
        self.tsdb_name = os.environ.get('TSDB_NAME', 'tsdb')
        self.tsdb_user = os.environ.get('TSDB_USER', 'postgres')
        self.tsdb_password = os.environ.get('TSDB_PASSWORD', '')

        # ==================== 日期配置 ====================
        self.end_date = os.environ.get('END_DATE', datetime.now().strftime('%Y-%m-%d'))
        self.start_date = os.environ.get(
            'START_DATE',
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )

        # ==================== 业务参数 ====================
        # 目标期限（默认为2年期）
        self.target_term = os.environ.get('TARGET_TERM', '2')

        # 特殊日期排除列表（用于某些数据源的异常日期处理）
        self.excluded_dates = ['2023-01-03', '2023-05-10']

    def get_bond_db_config(self):
        """
        获取MySQL (bond) 数据库配置字典

        Returns:
            dict: 数据库连接配置
        """
        return {
            'host': self.bond_db_host,
            'port': self.bond_db_port,
            'database': self.bond_db_name,
            'user': self.bond_db_user,
            'password': self.bond_db_password,
            'driver': 'mysql+pymysql',
            'pool_recycle': 3600
        }

    def get_tsdb_config(self):
        """
        获取PostgreSQL (tsdb) 数据库配置字典

        Returns:
            dict: 数据库连接配置
        """
        return {
            'host': self.tsdb_host,
            'port': self.tsdb_port,
            'database': self.tsdb_name,
            'user': self.tsdb_user,
            'password': self.tsdb_password,
            'driver': 'postgresql+psycopg2',
            'pool_recycle': 3600
        }

    def get_date_range(self):
        """
        获取日期范围配置

        Returns:
            dict: 包含startDT和endDT的字典
        """
        return {
            'startDT': self.start_date,
            'endDT': self.end_date
        }

    def __repr__(self):
        """返回配置信息（隐藏敏感信息）"""
        return (
            f"Config(\n"
            f"  target_term='{self.target_term}',\n"
            f"  start_date='{self.start_date}',\n"
            f"  end_date='{self.end_date}',\n"
            f"  bond_db_host='{self.bond_db_host}',\n"
            f"  tsdb_host='{self.tsdb_host}'\n"
            f")"
        )


# ==================== 常量定义 ====================

# 省份名称映射（用于特殊省份的名称转换）
PROVINCE_NAME_MAPPING = {
    '内蒙': '内蒙古',
    '黑龙': '黑龙江'
}

# 行政区划后缀（用于清理省份名称）
PROVINCE_SUFFIXES = [
    '省', '市', '自治区',
    '回族自治区', '维吾尔自治区', '壮族自治区'
]

# 数据库表名配置
TABLE_NAMES = {
    # PostgreSQL 表
    'hzcurve_credit': 'hzcurve_credit',          # 城投债曲线数据
    'tc_curve_mapping': 'tc最新所属曲线',          # 债券曲线归属
    'curve_code': '曲线代码',                     # 曲线代码映射
    'basicinfo_ct': 'basicinfo_xzqh_ct',         # 城投区域行政区划

    # MySQL 表
    'province_spread': 'stock.temp_5843',        # 省级利差临时表
    'city_spread': 'stock.temp_5857'             # 市级利差临时表
}

# 输出文件名配置
OUTPUT_FILES = {
    'province_spread': 'province_spread.csv',
    'province_spread_json': 'province_spread.json',
    'city_spread': 'city_spread.csv',
    'city_spread_json': 'city_spread.json',
    'province_7d_change': 'province_spread_change_7d.csv',
    'province_1m_change': 'province_spread_change_1m.csv',
    'city_7d_change': 'city_spread_change_7d.csv',
    'city_1m_change': 'city_spread_change_1m.csv'
}


# 创建默认配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    print("=" * 50)
    print("城投利差监控地图 - 配置信息")
    print("=" * 50)
    print(config)
    print("\n日期范围:", config.get_date_range())
    print("\nBond数据库配置:", config.get_bond_db_config())
    print("\nTSDB数据库配置:", config.get_tsdb_config())
