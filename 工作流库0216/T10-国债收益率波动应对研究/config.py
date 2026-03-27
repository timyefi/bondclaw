# -*- coding: utf-8 -*-
"""
T10 - 国债收益率波动应对研究 配置文件

该配置文件管理项目的所有参数设置，包括数据库连接、债券代码、分析参数等。
敏感信息通过环境变量获取，避免硬编码。
"""

import os

# ============================================================
# 数据库配置 - 使用环境变量存储敏感信息
# ============================================================

# 数据库连接参数
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 从环境变量获取密码
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# 构建数据库连接字符串
def get_db_connection_string():
    """生成数据库连接字符串"""
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


# ============================================================
# 债券代码配置
# ============================================================

BOND_CODES = {
    '10年国债': 'L001619604',
    '1年国债': 'L001618296',  # 或 'L001619275' 根据数据源选择
}

# 默认使用的债券代码
DEFAULT_BOND_CODE = BOND_CODES['10年国债']


# ============================================================
# 数据文件配置
# ============================================================

# 数据文件路径（相对于项目根目录）
DATA_FILE_PATH = 'data/国债收益率数据.xlsx'

# 结果输出目录
OUTPUT_DIR = 'output'

# 图片输出目录
ASSETS_DIR = 'assets'


# ============================================================
# 分析参数配置
# ============================================================

# 90%行情集中度指标参数
LOOKBACK_DAYS = 90  # 回看天数
CONCENTRATION_TABLE_NAME = 'market_concentration_90pct'  # 结果保存表名

# 行情阶段划分参数
STAGE_PARAMS = {
    '10年国债': {
        'prominence_bp': 25,      # 25 BP 收益率变动作为峰谷识别阈值
        'min_distance_days': 80,  # 约4个月的交易日
    },
    '1年国债': {
        'prominence_bp': 15,      # 15 BP 收益率变动
        'min_distance_days': 60,  # 约3个月的交易日
    }
}

# 策略回测参数
STRATEGY_PARAMS = {
    'up_thresh_bp_values': [0.5, 1, 1.5, 2, 2.5, 3],      # 上涨阈值(BP)
    'down_thresh_bp_values': [0.5, 1, 1.5, 2, 2.5, 3],    # 下跌阈值(BP)
    'buy_increment_values': [0.10, 0.25, 0.50, 0.75, 1.0], # 买入仓位增量
    'sell_increment_values': [0.10, 0.25, 0.50, 0.75, 1.0], # 卖出仓位减量
}

# 年度分析简化参数网格（减少计算量）
ANNUAL_STRATEGY_PARAMS = {
    'up_thresh_bp_values': [1, 2, 3, 5],
    'down_thresh_bp_values': [1, 2, 3, 5],
    'buy_increment_values': [0.25, 0.50, 1.0],
    'sell_increment_values': [0.25, 0.50, 1.0],
}

# 优化期日期范围
OPTIMIZATION_PERIOD = {
    'start_date': '2025-01-01',
    'end_date': '2025-06-05',
}


# ============================================================
# 风险配置
# ============================================================

RISK_CONFIG = {
    'var_confidence_levels': [0.95, 0.99],  # VaR置信水平
    'stress_scenario': '+200bps',            # 压力测试情景
    'max_duration': 10,                      # 最大久期（年）
    'max_leverage': 1.5,                     # 最大杠杆
    'max_drawdown': 0.05,                    # 最大回撤限制
}


# ============================================================
# 可视化配置
# ============================================================

# Matplotlib中文字体设置
PLOT_CONFIG = {
    'font_sans-serif': ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS'],
    'axes_unicode_minus': False,
    'figure_size': (14, 7),
    'dpi': 100,
}


# ============================================================
# 辅助函数
# ============================================================

def get_bond_code(bond_name):
    """获取债券代码"""
    return BOND_CODES.get(bond_name, DEFAULT_BOND_CODE)


def get_stage_params(bond_name):
    """获取行情阶段划分参数"""
    return STAGE_PARAMS.get(bond_name, STAGE_PARAMS['10年国债'])


def get_tenor(bond_name):
    """获取债券久期"""
    if '10年' in bond_name:
        return 10
    elif '1年' in bond_name:
        return 1
    return 5  # 默认5年


def setup_plot_style():
    """设置绘图风格"""
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = PLOT_CONFIG['font_sans-serif']
    plt.rcParams['axes.unicode_minus'] = PLOT_CONFIG['axes_unicode_minus']
    return plt


# ============================================================
# 配置验证
# ============================================================

def validate_config():
    """验证配置完整性"""
    errors = []

    # 检查必要的环境变量
    if not DB_PASSWORD:
        errors.append("警告: DB_PASSWORD 环境变量未设置，数据库连接可能失败")

    # 检查债券代码
    for name, code in BOND_CODES.items():
        if not code.startswith('L'):
            errors.append(f"警告: {name} 的代码格式可能不正确: {code}")

    return errors


if __name__ == '__main__':
    # 打印当前配置信息
    print("=== T10 国债收益率波动应对研究 配置信息 ===")
    print(f"数据库主机: {DB_HOST}")
    print(f"数据库名称: {DB_NAME}")
    print(f"债券代码: {BOND_CODES}")
    print(f"回看天数: {LOOKBACK_DAYS}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 验证配置
    errors = validate_config()
    if errors:
        print("\n配置验证结果:")
        for error in errors:
            print(f"  - {error}")
