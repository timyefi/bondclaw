# -*- coding: utf-8 -*-
"""
T36 - 同花顺Excel导入债券估值 配置文件

此配置文件使用环境变量管理所有敏感信息，避免硬编码密码。
请确保在运行前设置好相应的环境变量。
"""

import os
from pathlib import Path

# ============================================
# 项目路径配置
# ============================================
PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# 数据库配置（从环境变量读取）
# ============================================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 必须通过环境变量设置
DB_NAME = os.getenv("DB_NAME", "bond")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

# 构建数据库连接字符串
DB_CONNECTION_STRING = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"

# ============================================
# Excel处理配置
# ============================================
# 每个Excel文件的最大行数（避免超出Excel限制）
MAX_ROWS_PER_FILE = int(os.getenv("MAX_ROWS_PER_FILE", "300000"))

# iFinD数据加载等待时间（秒）
IFIND_WAIT_TIME = int(os.getenv("IFIND_WAIT_TIME", "60"))

# Excel操作重试配置
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "5"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "30"))

# ============================================
# iFinD指标配置
# ============================================
# iFinD指标定义
IFIND_INDICATORS = {
    "ths_bond_balance_bond": {
        "column": "C",
        "description": "债券余额",
        "params": None
    },
    "ths_evaluate_yield_yy_bond": {
        "column": "D",
        "description": "银行间收益率",
        "params": None
    },
    "ths_cb_market_implicit_rating_bond": {
        "column": "E",
        "description": "隐含评级",
        "params": None
    },
    "ths_evaluate_yield_cb_bond_exercise": {
        "column": "F",
        "description": "交易所收益率",
        "params": 102  # 交易所参数
    },
    "ths_evaluate_modified_dur_cb_bond_exercise": {
        "column": "G",
        "description": "修正久期",
        "params": 102  # 交易所参数
    }
}

# ============================================
# 债券类型配置
# ============================================
BOND_TYPES = {
    "credit": {
        "table": "basicinfo_credit",
        "temp_table": "temp_credit",
        "description": "信用债"
    },
    "finance": {
        "table": "basicinfo_finance",
        "temp_table": "temp_finance",
        "description": "金融债"
    },
    "abs": {
        "table": "basicinfo_abs",
        "temp_table": None,  # ABS类型没有临时去重表
        "description": "ABS"
    }
}

# ============================================
# 数据验证配置
# ============================================
# 估值收益率范围（百分比）
YIELD_MIN = 0
YIELD_MAX = 50

# 必需的数据列
REQUIRED_COLUMNS = ["dt", "trade_code", "ths_bond_balance_bond",
                    "ths_evaluate_yield_yy_bond", "ths_cb_market_implicit_rating_bond"]

# ============================================
# 日志配置
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================
# 配置验证函数
# ============================================
def validate_config():
    """验证配置是否完整"""
    errors = []

    if not DB_PASSWORD:
        errors.append("DB_PASSWORD 环境变量未设置")

    if not DB_HOST:
        errors.append("DB_HOST 环境变量未设置")

    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("配置验证通过")
    return True


if __name__ == "__main__":
    # 测试配置
    print("=" * 50)
    print("T36 配置测试")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"数据目录: {DATA_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"数据库主机: {DB_HOST}:{DB_PORT}")
    print(f"数据库名称: {DB_NAME}")
    print(f"每文件最大行数: {MAX_ROWS_PER_FILE}")
    print(f"iFinD等待时间: {IFIND_WAIT_TIME}秒")
    print(f"重试次数: {RETRY_ATTEMPTS}")
    print("=" * 50)
    validate_config()
