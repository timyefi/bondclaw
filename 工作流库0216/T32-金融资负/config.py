# -*- coding: utf-8 -*-
"""
T32 金融资负 配置文件

功能: 管理数据库连接、数据源配置等参数
"""

import os


class Config:
    """配置类"""

    # =====================
    # 数据库配置
    # =====================
    DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'hz_work')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 从环境变量获取密码
    DB_NAME = os.environ.get('DB_NAME', 'yq')

    # =====================
    # 数据源配置
    # =====================
    # Wind配置
    WIND_ENABLED = os.environ.get('WIND_ENABLED', 'false').lower() == 'true'

    # 同花顺配置
    THS_USER = os.environ.get('THS_USER', '')
    THS_PASSWORD = os.environ.get('THS_PASSWORD', '')
    THS_ENABLED = os.environ.get('THS_ENABLED', 'false').lower() == 'true'

    # =====================
    # 更新策略配置
    # =====================
    # 金融资负数据更新时间窗口（每月的几号到几号）
    UPDATE_START_DAY = int(os.environ.get('UPDATE_START_DAY', 20))
    UPDATE_END_DAY = int(os.environ.get('UPDATE_END_DAY', 30))

    # 基金净申购数据是否每天更新
    FUND_DAILY_UPDATE = os.environ.get('FUND_DAILY_UPDATE', 'true').lower() == 'true'

    # =====================
    # 表名配置
    # =====================
    TABLE_FINANCIAL = '金融资负'
    TABLE_FUND = '基金净申购'

    # =====================
    # 其他配置
    # =====================
    # API调用间隔（秒）
    API_CALL_INTERVAL = float(os.environ.get('API_CALL_INTERVAL', 0.1))

    # 日志级别
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @classmethod
    def get_database_config(cls):
        """
        获取数据库配置字典

        返回:
            dict: 数据库配置
        """
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME
        }

    @classmethod
    def get_connection_string(cls):
        """
        获取数据库连接字符串

        返回:
            str: SQLAlchemy连接字符串
        """
        return (
            f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    @classmethod
    def validate_config(cls):
        """
        验证配置是否完整

        返回:
            tuple: (is_valid, missing_configs)
        """
        missing = []

        if not cls.DB_PASSWORD:
            missing.append('DB_PASSWORD')

        if cls.WIND_ENABLED:
            # Wind不需要额外配置，只需要客户端安装
            pass

        if cls.THS_ENABLED:
            if not cls.THS_USER:
                missing.append('THS_USER')
            if not cls.THS_PASSWORD:
                missing.append('THS_PASSWORD')

        return len(missing) == 0, missing


# 配置验证示例
if __name__ == '__main__':
    is_valid, missing = Config.validate_config()
    if is_valid:
        print("配置验证通过")
    else:
        print(f"缺少以下配置项: {', '.join(missing)}")
        print("请设置相应的环境变量")
