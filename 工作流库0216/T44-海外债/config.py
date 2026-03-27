# -*- coding: utf-8 -*-
"""
海外债项目配置文件

该配置文件管理数据库连接、API密钥和其他敏感信息。
所有敏感信息均通过环境变量获取，避免硬编码。
"""

import os
from typing import Dict, Any


class Config:
    """配置管理类"""

    def __init__(self):
        """初始化配置"""
        self._load_env()

    def _load_env(self):
        """加载环境变量（如果存在.env文件）"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

    @property
    def db_host(self) -> str:
        """数据库主机"""
        return os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')

    @property
    def db_port(self) -> str:
        """数据库端口"""
        return os.environ.get('DB_PORT', '3306')

    @property
    def db_user(self) -> str:
        """数据库用户名"""
        return os.environ.get('DB_USER', '')

    @property
    def db_password(self) -> str:
        """数据库密码"""
        return os.environ.get('DB_PASSWORD', '')

    @property
    def db_name(self) -> str:
        """数据库名称"""
        return os.environ.get('DB_NAME', 'yq')

    @property
    def ifind_user(self) -> str:
        """iFinD用户名"""
        return os.environ.get('IFIND_USER', '')

    @property
    def ifind_password(self) -> str:
        """iFinD密码"""
        return os.environ.get('IFIND_PASSWORD', '')

    @property
    def wind_enabled(self) -> bool:
        """是否启用Wind"""
        return os.environ.get('WIND_ENABLED', 'false').lower() == 'true'

    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置

        返回:
            Dict: 数据库配置字典
        """
        return {
            'host': self.db_host,
            'port': self.db_port,
            'user': self.db_user,
            'password': self.db_password,
            'database': self.db_name
        }

    def get_ifind_config(self) -> Dict[str, str]:
        """
        获取iFinD配置

        返回:
            Dict: iFinD配置字典
        """
        return {
            'user': self.ifind_user,
            'password': self.ifind_password
        }

    def get_output_dir(self) -> str:
        """
        获取输出目录

        返回:
            str: 输出目录路径
        """
        output_dir = os.environ.get('OUTPUT_DIR', 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir

    def get_data_dir(self) -> str:
        """
        获取数据目录

        返回:
            str: 数据目录路径
        """
        data_dir = os.environ.get('DATA_DIR', 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir


# 项目常量
TABLE_NAME = '海外债数据'
DEFAULT_DATE_RANGE_DAYS = 30


# 数据字段映射
FIELD_MAPPING = {
    'trade_code': '交易代码',
    'sec_name': '证券名称',
    'dt': '日期',
    'planissueamount': '计划发行量',
    'bondterm': '债券期限',
    'bondtype': '债券类型',
    'isurbanincestmentbonds': '城投债标识'
}


if __name__ == '__main__':
    config = Config()
    print("数据库配置:")
    db_config = config.get_database_config()
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {'*' * len(db_config['user']) if db_config['user'] else '未配置'}")
    print(f"  Password: {'*' * len(db_config['password']) if db_config['password'] else '未配置'}")
