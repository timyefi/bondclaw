# -*- coding: utf-8 -*-
"""
理财监测系统配置文件

所有敏感信息通过环境变量获取，避免硬编码
"""

import os


class Config:
    """配置类"""

    # ==================== 数据库配置 ====================
    DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'hz_work')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 请设置环境变量 DB_PASSWORD
    DB_NAME = os.environ.get('DB_NAME', 'yq')

    # ==================== 同花顺配置 ====================
    THS_USERNAME = os.environ.get('THS_USERNAME', '')  # 请设置环境变量 THS_USERNAME
    THS_PASSWORD = os.environ.get('THS_PASSWORD', '')  # 请设置环境变量 THS_PASSWORD

    # ==================== 爬虫配置 ====================
    SCALE_URL = os.environ.get('SCALE_URL', 'https://news.stockstar.com/author_list/张菁.shtml')

    # ==================== 其他配置 ====================
    # 请求超时时间（秒）
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))

    # 数据库连接池大小
    POOL_SIZE = int(os.environ.get('POOL_SIZE', 5))

    # 连接回收时间（秒）
    POOL_RECYCLE = int(os.environ.get('POOL_RECYCLE', 3600))

    @classmethod
    def get_db_connection_string(cls) -> str:
        """
        获取数据库连接字符串

        Returns:
            str: SQLAlchemy 连接字符串
        """
        return f'mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}'

    @classmethod
    def validate(cls) -> bool:
        """
        验证配置是否完整

        Returns:
            bool: 配置是否完整
        """
        required_vars = ['DB_PASSWORD', 'THS_USERNAME', 'THS_PASSWORD']
        missing = [var for var in required_vars if not os.environ.get(var)]

        if missing:
            print(f"警告: 以下环境变量未设置: {', '.join(missing)}")
            return False

        return True


# 配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    print("数据库配置:")
    print(f"  Host: {config.DB_HOST}")
    print(f"  Port: {config.DB_PORT}")
    print(f"  User: {config.DB_USER}")
    print(f"  Database: {config.DB_NAME}")
    print()
    print("同花顺配置:")
    print(f"  Username: {config.THS_USERNAME if config.THS_USERNAME else '(未设置)'}")
    print()
    print("爬虫配置:")
    print(f"  URL: {config.SCALE_URL}")
    print()
    print("配置验证:")
    if config.validate():
        print("  配置完整")
    else:
        print("  配置不完整，请设置环境变量")
