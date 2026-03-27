# -*- coding: utf-8 -*-
"""
T04-可转债研究 配置文件

配置说明:
- 数据库和API配置使用环境变量存储敏感信息
- 请在环境变量中设置相应的值，或修改默认值
"""

import os

# ============================================================
# 数据库配置
# ============================================================

DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'hz_work'),
    'password': os.environ.get('DB_PASSWORD', ''),  # 请设置环境变量 DB_PASSWORD
    'host': os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_DATABASE', 'yq'),
    'charset': 'utf8mb4',
    'cursorclass': 'DictCursor'  # 可选: DictCursor, SSCursor
}

# 备用数据库配置
DB_CONFIG_BACKUP = {
    'user': os.environ.get('DB_BACKUP_USER', ''),
    'password': os.environ.get('DB_BACKUP_PASSWORD', ''),
    'host': os.environ.get('DB_BACKUP_HOST', ''),
    'port': int(os.environ.get('DB_BACKUP_PORT', '3306')),
    'database': os.environ.get('DB_BACKUP_DATABASE', ''),
    'charset': 'utf8mb4'
}

# ============================================================
# 同花顺iFinD配置
# ============================================================

THS_CONFIG = {
    'username': os.environ.get('THS_USERNAME', ''),  # 请设置环境变量 THS_USERNAME
    'password': os.environ.get('THS_PASSWORD', '')   # 请设置环境变量 THS_PASSWORD
}

# ============================================================
# 数据采集配置
# ============================================================

COLLECTOR_CONFIG = {
    'retry_times': 3,           # 重试次数
    'retry_interval': 5,        # 重试间隔(秒)
    'batch_size': 100,          # 批处理大小
    'sleep_interval': 1,        # 请求间隔(秒)
    'cache_expire_days': 7      # 缓存过期天数
}

# ============================================================
# 指数配置
# ============================================================

INDEX_CONFIG = {
    # 债性分类指数配置（基于纯债溢价率）
    'nature': {
        '偏债型': {
            'threshold': -10,    # 纯债溢价率 < -10%
            'target': 50,        # 目标样本数
            'minimum': 30        # 最低样本数
        },
        '平衡型': {
            'threshold': [-10, 10],  # -10% <= 纯债溢价率 <= 10%
            'target': 50,
            'minimum': 30
        },
        '偏股型': {
            'threshold': 10,     # 纯债溢价率 > 10%
            'target': 50,
            'minimum': 30
        }
    },

    # 溢价分类指数配置（基于价格和转股溢价率）
    'premium': {
        '双低': {
            'price': 110,        # 价格 <= 110
            'premium': 20,       # 转股溢价率 <= 20%
            'target': 10,
            'minimum': 5
        },
        '低价高溢': {
            'price': 110,        # 价格 <= 110
            'premium': 20,       # 转股溢价率 > 20%
            'target': 10,
            'minimum': 5
        },
        '高价低溢': {
            'price': 110,        # 价格 > 110
            'premium': 20,       # 转股溢价率 <= 20%
            'target': 20,
            'minimum': 10
        },
        '双高': {
            'price': 110,        # 价格 > 110
            'premium': 20,       # 转股溢价率 > 20%
            'target': 10,
            'minimum': 5
        },
        '普通型': {
            'target': 100,
            'minimum': 50
        }
    },

    # 行业指数配置
    'industry': {
        'target': 10,            # 每个行业目标样本数
        'minimum': 5             # 每个行业最低样本数
    }
}

# ============================================================
# 样本筛选配置
# ============================================================

SAMPLE_CONFIG = {
    'ma_window': 60,             # 移动平均窗口(交易日)
    'min_continuous_days': 20,   # 入池要求连续达标天数
    'min_turnover_rate': 0.5,    # 最低日均换手率(%)
    'weight_cap': 0.10,          # 单只债券权重上限

    # 样本补充策略（按顺序尝试）
    'adjustment_steps': [
        {'premium_range': 2},    # 第一步：放宽溢价率±2%
        {'premium_range': 5},    # 第二步：放宽溢价率±5%
        {'turnover_rate': 0.3},  # 第三步：降低换手率要求到0.3%
        {'turnover_rate': 0.1},  # 第四步：进一步降低换手率到0.1%
        {'dynamic_minimum': True} # 最后：完全放开条件
    ]
}

# ============================================================
# 数据存储配置
# ============================================================

DATA_CONFIG = {
    'cache_dir': './cache',      # 缓存目录
    'backup_dir': './backup',    # 备份目录
    'log_dir': './logs',         # 日志目录
    'output_dir': './output',    # 输出目录
    'raw_data_dir': './data/raw',          # 原始数据目录
    'processed_data_dir': './data/processed'  # 处理后数据目录
}

# ============================================================
# 数据库表结构
# ============================================================

TABLE_SCHEMA = """
-- 可转债行情数据表
CREATE TABLE IF NOT EXISTS marketinfo_equity1 (
    dt DATE NOT NULL,
    trade_code VARCHAR(20) NOT NULL,
    close DECIMAL(10,4),
    amount DECIMAL(20,4),
    pure_premium DECIMAL(10,4),
    ytm DECIMAL(10,4),
    conv_premium DECIMAL(10,4),
    conv_pe DECIMAL(10,4),
    stock_pe DECIMAL(10,4),
    stock_pb DECIMAL(10,4),
    conv_pb DECIMAL(10,4),
    un_conversion_balance DECIMAL(20,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (dt, trade_code),
    INDEX idx_dt (dt),
    INDEX idx_trade_code (trade_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 指数基本信息表
CREATE TABLE IF NOT EXISTS basicinfo_ebindex (
    trade_code VARCHAR(20) PRIMARY KEY,
    index_name VARCHAR(100),
    index_type VARCHAR(20),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_index_type (index_type),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 指数行情数据表
CREATE TABLE IF NOT EXISTS marketinfo_ebindex (
    trade_code VARCHAR(20) NOT NULL,
    dt DATE NOT NULL,
    close DECIMAL(10,4),
    total_balance DECIMAL(20,4),
    component_count INT,
    turnover_rate DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (trade_code, dt),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# ============================================================
# 日志配置
# ============================================================

LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'file_prefix': 'bond_research',
    'console_output': True
}


def get_db_connection_string(database: str = None) -> str:
    """
    获取数据库连接字符串

    Args:
        database: 数据库名，默认使用配置中的数据库

    Returns:
        SQLAlchemy连接字符串
    """
    db = database or DB_CONFIG['database']
    return f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db}"


def validate_config():
    """验证配置是否完整"""
    warnings = []

    if not DB_CONFIG.get('password'):
        warnings.append("数据库密码未设置，请设置环境变量 DB_PASSWORD")

    if not THS_CONFIG.get('username') or not THS_CONFIG.get('password'):
        warnings.append("同花顺账号或密码未设置，请设置环境变量 THS_USERNAME 和 THS_PASSWORD")

    return warnings


if __name__ == '__main__':
    # 验证配置
    warnings = validate_config()
    if warnings:
        print("配置警告:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("配置验证通过")

    # 显示配置摘要
    print(f"\n配置摘要:")
    print(f"  数据库主机: {DB_CONFIG['host']}")
    print(f"  数据库端口: {DB_CONFIG['port']}")
    print(f"  数据库名称: {DB_CONFIG['database']}")
    print(f"  同花顺用户: {THS_CONFIG.get('username', '未设置')}")
