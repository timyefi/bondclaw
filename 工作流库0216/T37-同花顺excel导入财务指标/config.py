# -*- coding: utf-8 -*-
"""
T37 - 同花顺Excel导入财务指标 配置文件

配置项通过环境变量加载，避免硬编码敏感信息。
使用 .env 文件或系统环境变量设置以下变量：
"""

import os
from pathlib import Path

# ============================================================
# 项目基础配置
# ============================================================

# 项目名称
PROJECT_NAME = "同花顺Excel导入财务指标"

# 项目版本
PROJECT_VERSION = "1.0.0"

# 基础路径
BASE_DIR = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 输出目录
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 数据库配置 - MySQL (债券基础信息)
# ============================================================

MYSQL_BOND_HOST = os.getenv("MYSQL_BOND_HOST", "rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com")
MYSQL_BOND_PORT = int(os.getenv("MYSQL_BOND_PORT", "3306"))
MYSQL_BOND_USER = os.getenv("MYSQL_BOND_USER", "hz_work")
MYSQL_BOND_PASSWORD = os.getenv("MYSQL_BOND_PASSWORD", "")
MYSQL_BOND_DATABASE = os.getenv("MYSQL_BOND_DATABASE", "bond")

# MySQL连接字符串
MYSQL_BOND_URL = f"mysql+pymysql://{MYSQL_BOND_USER}:{MYSQL_BOND_PASSWORD}@{MYSQL_BOND_HOST}:{MYSQL_BOND_PORT}/{MYSQL_BOND_DATABASE}"

# ============================================================
# 数据库配置 - MySQL (舆情库)
# ============================================================

MYSQL_YQ_HOST = os.getenv("MYSQL_YQ_HOST", "rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com")
MYSQL_YQ_PORT = int(os.getenv("MYSQL_YQ_PORT", "3306"))
MYSQL_YQ_USER = os.getenv("MYSQL_YQ_USER", "hz_work")
MYSQL_YQ_PASSWORD = os.getenv("MYSQL_YQ_PASSWORD", "")
MYSQL_YQ_DATABASE = os.getenv("MYSQL_YQ_DATABASE", "yq")

# MySQL YQ连接字符串
MYSQL_YQ_URL = f"mysql+pymysql://{MYSQL_YQ_USER}:{MYSQL_YQ_PASSWORD}@{MYSQL_YQ_HOST}:{MYSQL_YQ_PORT}/{MYSQL_YQ_DATABASE}"

# ============================================================
# 数据库配置 - PostgreSQL (财务指标存储)
# ============================================================

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "139.224.107.113")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "18032"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "tsdb")

# PostgreSQL连接字符串
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

# ============================================================
# 同花顺API配置
# ============================================================

# 同花顺API账号列表（按优先级排序）
THS_ACCOUNTS = [
    {"username": os.getenv("THS_USERNAME_1", ""), "password": os.getenv("THS_PASSWORD_1", "")},
    {"username": os.getenv("THS_USERNAME_2", ""), "password": os.getenv("THS_PASSWORD_2", "")},
    {"username": os.getenv("THS_USERNAME_3", ""), "password": os.getenv("THS_PASSWORD_3", "")},
    {"username": os.getenv("THS_USERNAME_4", ""), "password": os.getenv("THS_PASSWORD_4", "")},
]

# 当前使用的账号索引
CURRENT_THS_ACCOUNT_INDEX = 0

# ============================================================
# Excel处理配置
# ============================================================

# Excel文件默认输入目录
EXCEL_INPUT_DIR = os.getenv("EXCEL_INPUT_DIR", str(BASE_DIR / "excel_input"))

# Excel文件默认输出目录
EXCEL_OUTPUT_DIR = os.getenv("EXCEL_OUTPUT_DIR", str(BASE_DIR / "excel_output"))

# 创建Excel目录
Path(EXCEL_INPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(EXCEL_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Excel处理重试次数
EXCEL_RETRY_ATTEMPTS = 5

# Excel处理重试延迟(秒)
EXCEL_RETRY_DELAY = 30

# Excel计算等待时间(秒)
EXCEL_CALCULATION_WAIT = 60

# ============================================================
# 数据处理配置
# ============================================================

# 数据分块大小
CHUNK_SIZE = 10000

# SQL重试次数
SQL_RETRY_ATTEMPTS = 3

# SQL重试延迟(秒)
SQL_RETRY_DELAY = 1

# ============================================================
# 数据库表名配置
# ============================================================

# 宽表名称（原始数据）
TABLE_WIDE_FORMAT = "financial_indicators_wide"

# 长表名称（转换后数据）
TABLE_LONG_FORMAT = "financial_indicators_long"

# 临时表名称
TABLE_TEMP = "financial_indicators_temp"

# ============================================================
# 财务指标配置
# ============================================================

# 资产负债表指标
BALANCE_SHEET_INDICATORS = {
    "required_fields": ["总资产", "总负债", "流动资产", "流动负债", "所有者权益"],
    "calculated_fields": ["负债比率", "流动比率", "速动比率", "资产负债率"]
}

# 利润表指标
INCOME_STATEMENT_INDICATORS = {
    "required_fields": ["营业收入", "营业成本", "毛利润", "营业利润", "净利润"],
    "calculated_fields": ["销售毛利率", "营业利润率", "净利率", "利润增长率"]
}

# 现金流量表指标
CASH_FLOW_INDICATORS = {
    "required_fields": ["经营活动现金流量", "投资活动现金流量", "筹资活动现金流量", "现金及现金等价物净增加额"],
    "calculated_fields": ["经营性现金流比率", "自由现金流", "现金流覆盖率"]
}

# 风险阈值配置
RISK_THRESHOLDS = {
    "debt_ratio_warning": 0.6,      # 负债比率预警线
    "debt_ratio_danger": 0.8,       # 负债比率危险线
    "current_ratio_warning": 1.5,   # 流动比率预警线
    "current_ratio_danger": 1.0     # 流动比率危险线
}

# ============================================================
# 同花顺API指标列表
# ============================================================

# 核心财务指标列表（用于API调用）
THS_FINANCIAL_INDICATORS = [
    # 资产负债表指标
    "ths_total_assets_bond",                    # 总资产
    "ths_currency_fund_detail_sum_bond",        # 货币资金合计
    "ths_account_receivable_bond",              # 应收账款
    "ths_inventory_bond",                       # 存货
    "ths_fixed_asset_bond",                     # 固定资产
    "ths_st_borrow_bond",                       # 短期借款
    "ths_lt_loan_bond",                         # 长期借款
    "ths_bond_payable_bond",                    # 应付债券
    "ths_total_current_assets_bond",            # 流动资产合计
    "ths_total_current_liab_bond",              # 流动负债合计
    "ths_total_liab_bond",                      # 负债合计
    "ths_total_owner_equity_bond",              # 所有者权益合计

    # 利润表指标
    "ths_ebit_bond",                            # 息税前利润
    "ths_ebitda_bond",                          # 息税折旧摊销前利润
    "ths_ebit_ttm_bond",                        # EBIT TTM
    "ths_ebitda_ttm_bond",                      # EBITDA TTM

    # 现金流量表指标
    "ths_cash_received_of_borrowing_bond",      # 借款收到的现金
    "ths_cash_received_from_bond_issue_bond",   # 发行债券收到的现金
    "ths_invest_income_cash_received_bond",     # 投资收益收到的现金
    "ths_cash_received_of_sales_service_bond",  # 销售收到的现金

    # 财务比率指标
    "ths_annaul_net_asset_yield_bond",          # 年净资产收益率
    "ths_gross_selling_rate_bond",              # 销售毛利率
    "ths_roe_avg_by_ths_bond",                  # ROE
    "ths_asset_liab_ratio_bond",                # 资产负债率
]

# ============================================================
# 日志配置
# ============================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "logs" / "financial_indicators.log"

# 创建日志目录
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# 工具函数
# ============================================================

def get_mysql_bond_engine():
    """获取MySQL bond数据库连接引擎"""
    import sqlalchemy
    return sqlalchemy.create_engine(
        MYSQL_BOND_URL,
        poolclass=sqlalchemy.pool.NullPool
    )


def get_mysql_yq_engine():
    """获取MySQL yq数据库连接引擎"""
    import sqlalchemy
    return sqlalchemy.create_engine(
        MYSQL_YQ_URL,
        poolclass=sqlalchemy.pool.NullPool
    )


def get_postgres_engine():
    """获取PostgreSQL数据库连接引擎"""
    import sqlalchemy
    return sqlalchemy.create_engine(POSTGRES_URL)


def get_postgres_connection():
    """获取PostgreSQL原生连接"""
    import psycopg2
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DATABASE
    )


def get_ths_account():
    """获取当前可用的同花顺账号"""
    global CURRENT_THS_ACCOUNT_INDEX
    account = THS_ACCOUNTS[CURRENT_THS_ACCOUNT_INDEX]
    if account["username"] and account["password"]:
        return account
    # 尝试下一个账号
    for i, acc in enumerate(THS_ACCOUNTS):
        if acc["username"] and acc["password"]:
            CURRENT_THS_ACCOUNT_INDEX = i
            return acc
    return None


def validate_config():
    """验证配置是否完整"""
    errors = []

    if not MYSQL_BOND_PASSWORD:
        errors.append("MYSQL_BOND_PASSWORD 环境变量未设置")

    if not MYSQL_YQ_PASSWORD:
        errors.append("MYSQL_YQ_PASSWORD 环境变量未设置")

    if not POSTGRES_PASSWORD:
        errors.append("POSTGRES_PASSWORD 环境变量未设置")

    # 检查同花顺账号
    has_ths_account = any(
        acc["username"] and acc["password"]
        for acc in THS_ACCOUNTS
    )
    if not has_ths_account:
        errors.append("未配置有效的同花顺API账号")

    return errors


# 配置验证
if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        print("\n请设置相应的环境变量或创建.env文件")
    else:
        print("配置验证通过")
        print(f"项目名称: {PROJECT_NAME}")
        print(f"项目版本: {PROJECT_VERSION}")
        print(f"基础目录: {BASE_DIR}")
