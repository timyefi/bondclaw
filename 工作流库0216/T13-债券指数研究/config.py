# -*- coding: utf-8 -*-
"""
T13 - 债券指数研究配置文件
配置项均使用环境变量，无硬编码密码
"""

import os
from pathlib import Path

# ============================================================================
# 基础路径配置
# ============================================================================
# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"

# 静态资源目录
ASSETS_DIR = PROJECT_ROOT / "assets"

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 数据库配置 (使用环境变量)
# ============================================================================
DB_USER = os.environ.get("BOND_DB_USER", "")
DB_PASSWORD = os.environ.get("BOND_DB_PASSWORD", "")
DB_HOST = os.environ.get("BOND_DB_HOST", "rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com")
DB_PORT = os.environ.get("BOND_DB_PORT", "3306")
DB_NAME = os.environ.get("BOND_DB_NAME", "bond")


def get_database_url():
    """获取数据库连接URL"""
    if not DB_USER or not DB_PASSWORD:
        raise ValueError("请设置环境变量 BOND_DB_USER 和 BOND_DB_PASSWORD")
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ============================================================================
# 分析参数配置
# ============================================================================
# 收益率分组间隔大小 (%)
RETURN_BIN_SIZE = float(os.environ.get("RETURN_BIN_SIZE", "0.5"))

# 久期分组间隔大小 (年)
DURATION_BIN_SIZE = float(os.environ.get("DURATION_BIN_SIZE", "0.5"))

# 最大回撤分组间隔大小 (%)
DRAWDOWN_BIN_SIZE = float(os.environ.get("DRAWDOWN_BIN_SIZE", "0.5"))

# 展示的指数数量
TOP_N_INDICES = int(os.environ.get("TOP_N_INDICES", "20"))

# 投资组合优化参数
MIN_COMBO_SIZE = int(os.environ.get("MIN_COMBO_SIZE", "3"))
MAX_COMBO_SIZE = int(os.environ.get("MAX_COMBO_SIZE", "10"))
SAMPLE_SIZE = int(os.environ.get("SAMPLE_SIZE", "1000"))

# ============================================================================
# 时间周期配置
# ============================================================================
PERIODS = {
    "30天": 30,
    "3个月": 90,
    "半年": 180,
    "1年": 365,
}

DEFAULT_PERIOD = "1年"

# ============================================================================
# 可视化配置
# ============================================================================
# 图表样式
PLOT_STYLE = "whitegrid"
COLOR_PALETTE = "viridis"

# 图表尺寸
FIGURE_WIDTH = 12
FIGURE_HEIGHT = 8
DPI = 100

# Plotly配置
PLOTLY_THEME = "plotly_white"

# Dash配置
DASH_THEME = "dbc.themes.BOOTSTRAP"
DASH_PORT = int(os.environ.get("DASH_PORT", "8050"))

# ============================================================================
# 中文字体配置
# ============================================================================
# 支持的中文字体列表 (按优先级排序)
CHINESE_FONTS = [
    "WenQuanYi Zen Hei",
    "SimHei",
    "Microsoft YaHei",
    "STHeiti",
    "sans-serif",
]

# ============================================================================
# 指数筛选条件配置
# ============================================================================
# 筛选条件: 指数名称必须包含的关键词
INDEX_NAME_KEYWORDS = ["财富"]

# 筛选条件: 久期范围 (年)
DURATION_FILTER = {
    "min": None,  # None表示不限制
    "max": None,
}

# 筛选条件: 久期区间关键词
DURATION_RANGES = ["1-3年", "3-5年"]

# ============================================================================
# 日志配置
# ============================================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# 辅助函数
# ============================================================================
def get_period_days(period_name):
    """根据周期名称获取天数"""
    return PERIODS.get(period_name, 365)


def get_period_start_date(period_name, end_date=None):
    """根据周期名称获取开始日期"""
    import datetime

    if end_date is None:
        end_date = datetime.datetime.now()
    elif isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    days = get_period_days(period_name)
    start_date = end_date - datetime.timedelta(days=days)
    return start_date.strftime("%Y-%m-%d")


def validate_config():
    """验证配置是否完整"""
    errors = []

    # 检查数据库配置
    if not DB_USER:
        errors.append("缺少环境变量: BOND_DB_USER")
    if not DB_PASSWORD:
        errors.append("缺少环境变量: BOND_DB_PASSWORD")

    # 检查数值参数
    if RETURN_BIN_SIZE <= 0:
        errors.append("RETURN_BIN_SIZE 必须大于 0")
    if DURATION_BIN_SIZE <= 0:
        errors.append("DURATION_BIN_SIZE 必须大于 0")
    if TOP_N_INDICES <= 0:
        errors.append("TOP_N_INDICES 必须大于 0")

    return errors


if __name__ == "__main__":
    # 打印当前配置
    print("=" * 60)
    print("T13 - 债券指数研究配置")
    print("=" * 60)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"数据目录: {DATA_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"数据库主机: {DB_HOST}")
    print(f"数据库端口: {DB_PORT}")
    print(f"数据库名称: {DB_NAME}")
    print(f"数据库用户: {'已配置' if DB_USER else '未配置'}")
    print(f"数据库密码: {'已配置' if DB_PASSWORD else '未配置'}")
    print(f"收益率分组间隔: {RETURN_BIN_SIZE}%")
    print(f"久期分组间隔: {DURATION_BIN_SIZE}年")
    print(f"最大回撤分组间隔: {DRAWDOWN_BIN_SIZE}%")
    print(f"展示指数数量: {TOP_N_INDICES}")
    print(f"默认周期: {DEFAULT_PERIOD}")
    print("=" * 60)

    # 验证配置
    errors = validate_config()
    if errors:
        print("\n配置警告:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n配置验证通过!")
