# -*- coding: utf-8 -*-
"""
T48-银行回验 配置文件

本配置文件包含数据库连接参数、模糊匹配阈值和特征调整参数。
所有敏感信息从环境变量中读取。
"""

import os


class Config:
    """配置类，管理所有配置参数"""

    def __init__(self):
        # ============== MySQL 数据库配置（yq数据库） ==============
        self.mysql_yq_host = os.environ.get('MYSQL_YQ_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
        self.mysql_yq_port = os.environ.get('MYSQL_YQ_PORT', '3306')
        self.mysql_yq_user = os.environ.get('MYSQL_YQ_USER', 'hz_work')
        self.mysql_yq_password = os.environ.get('MYSQL_YQ_PASSWORD', 'Hzinsights2015')
        self.mysql_yq_database = os.environ.get('MYSQL_YQ_DATABASE', 'yq')

        # ============== PostgreSQL 数据库配置（tsdb数据库） ==============
        self.pg_tsdb_host = os.environ.get('PG_TSDB_HOST', '139.224.107.113')
        self.pg_tsdb_port = os.environ.get('PG_TSDB_PORT', '18032')
        self.pg_tsdb_user = os.environ.get('PG_TSDB_USER', 'postgres')
        self.pg_tsdb_password = os.environ.get('PG_TSDB_PASSWORD', 'hzinsights2015')
        self.pg_tsdb_database = os.environ.get('PG_TSDB_DATABASE', 'tsdb')

        # ============== 模糊匹配配置 ==============
        self.fuzzy_threshold = int(os.environ.get('FUZZY_THRESHOLD', '70'))

        # ============== 特征调整参数 ==============
        # 手动调整的特征重要性
        self.feature_adjustments = {
            '近1年拨备覆盖率变化_rank': -0.15,
            '近1年存款占比变化_rank': -0.05
        }

        # ============== 数据处理参数 ==============
        # 变化量计算周期
        self.yearly_change_periods = int(os.environ.get('YEARLY_CHANGE_PERIODS', '365'))
        self.quarterly_change_periods = int(os.environ.get('QUARTERLY_CHANGE_PERIODS', '90'))

        # ============== 模型参数 ==============
        # 初始参数值
        self.initial_param_value = float(os.environ.get('INITIAL_PARAM_VALUE', '0.1'))
        # 参数范围
        self.param_bound_min = float(os.environ.get('PARAM_BOUND_MIN', '-1.0'))
        self.param_bound_max = float(os.environ.get('PARAM_BOUND_MAX', '1.0'))

        # ============== 可视化配置 ==============
        self.chart_title = '银行债90天表现 - 特征重要性分析'
        self.chart_dpi = int(os.environ.get('CHART_DPI', '150'))

        # ============== 数据库表名配置 ==============
        self.tables = {
            'yq': {
                '舆情监控': 'yq.金融债舆情监控',
                '金融债成交': 'yq.temp_金融债成交',
                '银行数据库': 'yq.银行数据库'
            },
            'pg': {
                '银行债成交占比': 'temp_银行债成交占比',
                '金融债近期收益率变化': 'temp_金融债近期收益率变化'
            }
        }

    def get_mysql_connection_string(self):
        """获取MySQL连接字符串"""
        return 'mysql+pymysql://%s:%s@%s:%s/%s' % (
            self.mysql_yq_user,
            self.mysql_yq_password,
            self.mysql_yq_host,
            self.mysql_yq_port,
            self.mysql_yq_database
        )

    def get_postgres_connection_string(self):
        """获取PostgreSQL连接字符串"""
        return 'postgresql://%s:%s@%s:%s/%s' % (
            self.pg_tsdb_user,
            self.pg_tsdb_password,
            self.pg_tsdb_host,
            self.pg_tsdb_port,
            self.pg_tsdb_database
        )

    def get_param_bounds(self, n_features):
        """获取参数边界列表"""
        return [(self.param_bound_min, self.param_bound_max)] * n_features

    def get_initial_params(self, n_features):
        """获取初始参数数组"""
        import numpy as np
        return np.full(n_features, self.initial_param_value)

    def validate(self):
        """验证必要的配置是否完整"""
        required_vars = [
            ('MYSQL_YQ_HOST', self.mysql_yq_host),
            ('MYSQL_YQ_USER', self.mysql_yq_user),
            ('MYSQL_YQ_PASSWORD', self.mysql_yq_password),
            ('PG_TSDB_HOST', self.pg_tsdb_host),
            ('PG_TSDB_USER', self.pg_tsdb_user),
            ('PG_TSDB_PASSWORD', self.pg_tsdb_password)
        ]

        missing = [name for name, value in required_vars if not value]

        if missing:
            print(f"警告: 以下环境变量未设置，将使用默认值: {', '.join(missing)}")
            return False

        return True

    def print_config(self):
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 60)
        print("T48-银行回验 配置信息")
        print("=" * 60)
        print(f"MySQL (yq): {self.mysql_yq_host}:{self.mysql_yq_port}/{self.mysql_yq_database}")
        print(f"PostgreSQL (tsdb): {self.pg_tsdb_host}:{self.pg_tsdb_port}/{self.pg_tsdb_database}")
        print(f"模糊匹配阈值: {self.fuzzy_threshold}")
        print(f"参数范围: [{self.param_bound_min}, {self.param_bound_max}]")
        print("=" * 60)


# 环境变量设置示例（供参考）
"""
# Linux/Mac
export MYSQL_YQ_HOST="your_host"
export MYSQL_YQ_PORT="3306"
export MYSQL_YQ_USER="your_user"
export MYSQL_YQ_PASSWORD="your_password"
export MYSQL_YQ_DATABASE="yq"

export PG_TSDB_HOST="your_host"
export PG_TSDB_PORT="5432"
export PG_TSDB_USER="your_user"
export PG_TSDB_PASSWORD="your_password"
export PG_TSDB_DATABASE="tsdb"

export FUZZY_THRESHOLD="70"
"""

# Windows PowerShell 示例
"""
$env:MYSQL_YQ_HOST="your_host"
$env:MYSQL_YQ_PORT="3306"
$env:MYSQL_YQ_USER="your_user"
$env:MYSQL_YQ_PASSWORD="your_password"
$env:MYSQL_YQ_DATABASE="yq"

$env:PG_TSDB_HOST="your_host"
$env:PG_TSDB_PORT="5432"
$env:PG_TSDB_USER="your_user"
$env:PG_TSDB_PASSWORD="your_password"
$env:PG_TSDB_DATABASE="tsdb"

$env:FUZZY_THRESHOLD="70"
"""


if __name__ == "__main__":
    # 测试配置
    config = Config()
    config.print_config()
    config.validate()

    print("\nMySQL连接字符串（隐藏密码）:")
    conn_str = config.get_mysql_connection_string()
    print(conn_str.replace(config.mysql_yq_password, '****'))

    print("\nPostgreSQL连接字符串（隐藏密码）:")
    conn_str = config.get_postgres_connection_string()
    print(conn_str.replace(config.pg_tsdb_password, '****'))
