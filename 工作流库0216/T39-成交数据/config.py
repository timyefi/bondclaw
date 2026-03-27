# -*- coding: utf-8 -*-
"""
T39 - 成交数据 配置模块
评级狗债券成交数据采集系统配置

使用环境变量进行敏感信息配置，避免硬编码密码
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # MySQL数据库配置 - 从环境变量读取
    mysql_host: str = field(default_factory=lambda: os.getenv('MYSQL_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'))
    mysql_port: int = field(default_factory=lambda: int(os.getenv('MYSQL_PORT', '3306')))
    mysql_user: str = field(default_factory=lambda: os.getenv('MYSQL_USER', 'hz_work'))
    mysql_password: str = field(default_factory=lambda: os.getenv('MYSQL_PASSWORD', ''))
    mysql_database_yq: str = field(default_factory=lambda: os.getenv('MYSQL_DATABASE_YQ', 'yq'))
    mysql_database_bond: str = field(default_factory=lambda: os.getenv('MYSQL_DATABASE_BOND', 'bond'))

    # PostgreSQL数据库配置
    pg_host: str = field(default_factory=lambda: os.getenv('PG_HOST', '139.224.107.113'))
    pg_port: int = field(default_factory=lambda: int(os.getenv('PG_PORT', '18032')))
    pg_user: str = field(default_factory=lambda: os.getenv('PG_USER', 'postgres'))
    pg_password: str = field(default_factory=lambda: os.getenv('PG_PASSWORD', ''))
    pg_database: str = field(default_factory=lambda: os.getenv('PG_DATABASE', 'tsdb'))

    def get_mysql_yq_connection_string(self) -> str:
        """获取MySQL yq数据库连接字符串"""
        return f'mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database_yq}'

    def get_mysql_bond_connection_string(self) -> str:
        """获取MySQL bond数据库连接字符串"""
        return f'mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database_bond}'

    def get_pg_connection_string(self) -> str:
        """获取PostgreSQL连接字符串"""
        return f'postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}'


@dataclass
class RatingDogAPIConfig:
    """评级狗API配置"""
    # 登录API地址
    login_url: str = 'https://auth.ratingdog.cn/api/TokenAuth/Authenticate'

    # 成交数据API地址
    trade_data_url: str = 'https://host.ratingdog.cn/api/services/app/Bond/QueryTradedHistoricalOfFrontDeskTenants'

    # 用户凭证 - 从环境变量读取
    username: str = field(default_factory=lambda: os.getenv('RATINGDOG_USERNAME', ''))
    phone_code: str = field(default_factory=lambda: os.getenv('RATINGDOG_PHONE_CODE', '86'))
    password: str = field(default_factory=lambda: os.getenv('RATINGDOG_PASSWORD', ''))

    # 租户ID
    tenant_id: str = '114'

    # 请求超时时间（秒）
    timeout: int = 30

    # 每页最大结果数
    max_result_count: int = 150

    # 最大重试次数
    max_retries: int = 5

    # 重试间隔（秒）
    retry_interval: float = 1.0

    def get_login_headers(self) -> Dict[str, str]:
        """获取登录请求头"""
        return {
            '.Aspnetcore.Culture': 'zh-Hans',
            'authority': 'auth.ratingdog.cn',
            'method': 'POST',
            'path': '/api/TokenAuth/Authenticate',
            'scheme': 'https',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Devicechannel': 'gclife_bmp_pc',
            'Origin': 'https://www.ratingdog.cn',
            'Ratingdog.Tenantid': self.tenant_id,
            'Referer': 'https://www.ratingdog.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

    def get_api_headers(self, access_token: str) -> Dict[str, str]:
        """获取API请求头"""
        return {
            '.Aspnetcore.Culture': 'zh-Hans',
            'Host': 'host.ratingdog.cn',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json;charset=UTF-8',
            'Devicechannel': 'gclife_bmp_pc',
            'Origin': 'https://www.ratingdog.cn',
            'Ratingdog.Tenantid': self.tenant_id,
            'Referer': 'https://www.ratingdog.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

    def get_login_data(self) -> Dict[str, str]:
        """获取登录请求数据"""
        return {
            'UserNameOrEmailAddressOrPhone': self.username,
            'internationalPhoneCode': self.phone_code,
            'password': self.password
        }


@dataclass
class TradeDataConfig:
    """成交数据配置"""
    # 数据源类型
    data_sources: List[str] = field(default_factory=lambda: ['银行间', '交易所', '柜台'])

    # 时间粒度
    time_frames: List[str] = field(default_factory=lambda: ['分钟', '小时', '日', '周', '月'])

    # 聚合级别
    aggregation_levels: List[str] = field(default_factory=lambda: ['分钟', '小时', '日', '周', '月'])

    # 流动性阈值
    liquidity_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'high': 0.7,
        'medium': 0.4,
        'low': 0.0
    })

    # 成交量阈值（元）
    volume_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'large': 100000000,      # 1亿
        'medium': 10000000,      # 1000万
        'small': 1000000          # 100万
    })

    # 价格范围限制
    price_min: float = 0.0
    price_max: float = 200.0

    # 成交金额最小值
    amount_min: float = 0.0


@dataclass
class ProcessConfig:
    """处理流程配置"""
    # 批量处理日期范围时的日期步长（天）
    date_step: int = 1

    # 数据采集开始日期（None表示从数据库查询）
    start_date: str = None

    # 数据采集结束日期（None表示到今天）
    end_date: str = None

    # 是否启用增量更新
    incremental_update: bool = True

    # 输出表名
    output_table: str = 'cjqb'

    # 日期查询源表
    date_source_table: str = 'bond.marketinfo_abs'

    # 数据去重字段
    dedup_fields: List[str] = field(default_factory=lambda: ['dt'])


class Config:
    """主配置类"""

    def __init__(self):
        self.database = DatabaseConfig()
        self.ratingdog_api = RatingDogAPIConfig()
        self.trade_data = TradeDataConfig()
        self.process = ProcessConfig()

        # 验证必要的环境变量
        self._validate_config()

    def _validate_config(self):
        """验证配置是否完整"""
        warnings = []

        # 检查MySQL密码
        if not self.database.mysql_password:
            warnings.append('MYSQL_PASSWORD环境变量未设置')

        # 检查评级狗凭证
        if not self.ratingdog_api.username:
            warnings.append('RATINGDOG_USERNAME环境变量未设置')
        if not self.ratingdog_api.password:
            warnings.append('RATINGDOG_PASSWORD环境变量未设置')

        if warnings:
            logger.warning('配置警告:\n' + '\n'.join(f'  - {w}' for w in warnings))
            logger.warning('请设置相应的环境变量以确保程序正常运行')


# 创建全局配置实例
config = Config()


# 便捷访问函数
def get_mysql_yq_engine():
    """获取MySQL yq数据库引擎"""
    import sqlalchemy
    return sqlalchemy.create_engine(
        config.database.get_mysql_yq_connection_string(),
        poolclass=sqlalchemy.pool.NullPool
    )


def get_mysql_bond_engine():
    """获取MySQL bond数据库引擎"""
    import sqlalchemy
    return sqlalchemy.create_engine(
        config.database.get_mysql_bond_connection_string(),
        poolclass=sqlalchemy.pool.NullPool
    )


def get_pg_connection():
    """获取PostgreSQL连接"""
    import psycopg2
    return psycopg2.connect(
        host=config.database.pg_host,
        port=config.database.pg_port,
        user=config.database.pg_user,
        password=config.database.pg_password,
        database=config.database.pg_database
    )


if __name__ == '__main__':
    # 测试配置
    print('=== T39-成交数据 配置信息 ===')
    print(f'MySQL Host: {config.database.mysql_host}')
    print(f'MySQL Port: {config.database.mysql_port}')
    print(f'MySQL User: {config.database.mysql_user}')
    print(f'MySQL Database YQ: {config.database.mysql_database_yq}')
    print(f'MySQL Database Bond: {config.database.mysql_database_bond}')
    print(f'PostgreSQL Host: {config.database.pg_host}')
    print(f'RatingDog Username: {config.ratingdog_api.username}')
    print(f'Max Result Count: {config.ratingdog_api.max_result_count}')
    print(f'Output Table: {config.process.output_table}')
