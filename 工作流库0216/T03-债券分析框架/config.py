# -*- coding: utf-8 -*-
"""
T03 - 债券分析框架 配置文件

配置说明:
- 数据库连接信息通过环境变量获取，避免硬编码敏感信息
- 支持通过 .env 文件或系统环境变量配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""

    # ================================
    # 数据库配置
    # ================================

    DB_HOST = os.getenv('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'hz_work')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # 从环境变量获取，不硬编码
    DB_DATABASE = os.getenv('DB_DATABASE', 'bond')
    DB_CHARSET = os.getenv('DB_CHARSET', 'utf8')

    # ================================
    # 分析参数配置
    # ================================

    # 默认日期范围
    START_DATE = os.getenv('START_DATE', '2014-01-01')
    END_DATE = os.getenv('END_DATE', '2024-12-31')

    # 期限分类
    TERM_RANGES = {
        '0-1': [0, 1],
        '1-3': [1, 3],
        '3-5': [3, 5],
        '5-7': [5, 7],
        '7-10': [7, 10],
        '10-13': [10, 13],
        '13-17': [13, 17],
        '17-23': [17, 23],
        '23-27': [23, 27],
        '27-33': [27, 33],
        '33-50': [33, 50]
    }

    # 简化期限分类
    TERMS = {
        '短期': '0-1',
        '中短期': '1-3',
        '中长期': '3-5',
        '长期': '5-10'
    }

    # 债券类型
    BOND_TYPES = ['国债', '国开', '口行', '农发', '地方债', '城投', '产业', '普通金融债', '二永', '存单']
    RATE_BONDS = ['国债', '国开', '口行', '农发', '地方债']
    FINANCE_BONDS = ['存单', '普通金融债', '二永']
    CREDIT_BONDS = ['城投', '产业']

    # 评级分类
    RATINGS = ['AAA', 'AA+', 'AA', 'AA(2)', 'AA-']
    RATING_MAPPING = {
        '高资质': ['AAA', 'AA+'],
        '中资质': ['AA'],
        '弱资质': ['AA(2)', 'AA-']
    }

    # ================================
    # 可视化配置
    # ================================

    VIZ_CONFIG = {
        'style': 'seaborn',
        'figsize': (16, 10),
        'dpi': 300,
        'color_palette': 'husl'
    }

    # ================================
    # 输出配置
    # ================================

    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    CACHE_DIR = os.getenv('CACHE_DIR', 'data')

    # ================================
    # 策略配置
    # ================================

    # 初始投资金额（10亿）
    INITIAL_AMOUNT = 1_000_000_000

    # 久期映射
    DURATION_MAP = {
        '短期': 0.5,
        '中短期': 2.0,
        '中长期': 4.0,
        '长期': 7.0,
        '超长期': 15.0
    }

    # ================================
    # 方法
    # ================================

    def get_db_config(self):
        """
        获取数据库配置字典

        Returns:
            dict: 数据库配置
        """
        return {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'database': self.DB_DATABASE,
            'charset': self.DB_CHARSET
        }

    def get_connection_string(self):
        """
        获取数据库连接字符串

        Returns:
            str: SQLAlchemy连接字符串
        """
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

    def get_term_range(self, term_name):
        """
        获取期限范围

        Args:
            term_name: 期限名称

        Returns:
            list: [最小值, 最大值]
        """
        return self.TERM_RANGES.get(term_name, [0, 50])

    def get_duration(self, term_name):
        """
        获取久期

        Args:
            term_name: 期限名称

        Returns:
            float: 修正久期
        """
        return self.DURATION_MAP.get(term_name, 5.0)

    def get_ratings_by_level(self, level):
        """
        根据资质等级获取评级列表

        Args:
            level: 资质等级（高资质、中资质、弱资质）

        Returns:
            list: 评级列表
        """
        return self.RATING_MAPPING.get(level, [])


# 创建默认配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    print("=" * 50)
    print("T03 - 债券分析框架 配置测试")
    print("=" * 50)

    print("\n数据库配置:")
    db_config = config.get_db_config()
    for key, value in db_config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(value) if value else '(未设置)'}")
        else:
            print(f"  {key}: {value}")

    print("\n期限分类:")
    for term, range_val in config.TERM_RANGES.items():
        print(f"  {term}: {range_val}")

    print("\n债券类型:")
    print(f"  利率债: {config.RATE_BONDS}")
    print(f"  金融债: {config.FINANCE_BONDS}")
    print(f"  信用债: {config.CREDIT_BONDS}")

    print("\n评级分类:")
    for level, ratings in config.RATING_MAPPING.items():
        print(f"  {level}: {ratings}")

    print("\n配置测试完成!")
