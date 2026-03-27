#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T11 - 机构行为分析配置文件

配置说明：
- 数据库连接配置使用环境变量，请确保设置以下环境变量：
  - DB_HOST: 数据库主机地址
  - DB_PORT: 数据库端口
  - DB_USER: 数据库用户名
  - DB_PASSWORD: 数据库密码
  - DB_NAME: 数据库名称
"""

import os


class Config:
    """机构行为分析配置类"""

    def __init__(self):
        """初始化配置"""
        # =====================
        # 目录配置
        # =====================
        self.data_dir = os.environ.get('DATA_DIR', '/data/项目/2025/机构行为')
        self.output_dir = os.environ.get('OUTPUT_DIR', './output')
        self.charts_dir = os.environ.get('CHARTS_DIR', './charts')
        self.report_dir = os.environ.get('REPORT_DIR', './report')

        # =====================
        # 数据文件配置
        # =====================
        self.repo_data_file = os.environ.get(
            'REPO_DATA_FILE',
            '分机构日资金流向分析（质押）20250514-20250613-日度.xlsx'
        )
        self.bond_data_file = os.environ.get(
            'BOND_DATA_FILE',
            '现券成交分机构统计20250601-20250710-日度.xlsx'
        )

        # =====================
        # 数据库配置（使用环境变量）
        # =====================
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = os.environ.get('DB_PORT', '3306')
        self.db_user = os.environ.get('DB_USER', 'root')
        self.db_password = os.environ.get('DB_PASSWORD', '')
        self.db_name = os.environ.get('DB_NAME', 'bond_market')

        # =====================
        # 机构配置
        # =====================
        self.target_institutions = [
            'Monetary Market Fund',                      # 货币市场基金
            'Wealth Management Subsidiary & Products',   # 理财子公司及理财类产品
            'Fund Company & Products'                    # 基金公司及产品
        ]

        # 所有机构类型
        self.all_institution_types = [
            'Large Commercial/Policy Bank',              # 大型商业银行/政策性银行
            'Joint-stock Commercial Bank',               # 股份制商业银行
            'City Commercial Bank',                      # 城市商业银行
            'Rural Financial Institution',               # 农村金融机构
            'Foreign Bank',                              # 外资银行
            'Securities Company',                        # 证券公司
            'Insurance Company',                         # 保险公司
            'Fund Company & Products',                   # 基金公司及产品
            'Monetary Market Fund',                      # 货币市场基金
            'Wealth Management Subsidiary & Products',   # 理财子公司及理财类产品
            'Other Products',                            # 其他产品类
            'Others'                                     # 其他
        ]

        # =====================
        # 分析参数配置
        # =====================
        self.analysis_split_date = os.environ.get('ANALYSIS_SPLIT_DATE', '2025-05-25')
        self.min_holding_value = int(os.environ.get('MIN_HOLDING_VALUE', 10000000))  # 最小持仓金额
        self.top_institutions = int(os.environ.get('TOP_INSTITUTIONS', 20))          # 重点机构数量
        self.tracking_period = int(os.environ.get('TRACKING_PERIOD', 30))            # 跟踪周期（天）

        # =====================
        # 可视化配置
        # =====================
        self.chart_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        self.chart_template = 'plotly_white'
        self.chart_font_family = 'Arial, sans-serif'
        self.chart_font_size = 12

    def get_database_url(self):
        """
        获取数据库连接URL

        Returns:
        --------
        str
            数据库连接URL
        """
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def ensure_directories(self):
        """确保所有输出目录存在"""
        for dir_path in [self.output_dir, self.charts_dir, self.report_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"已创建目录: {dir_path}")

    def validate_config(self):
        """
        验证配置是否有效

        Returns:
        --------
        bool
            配置是否有效
        """
        errors = []

        # 检查数据目录
        if not os.path.exists(self.data_dir):
            errors.append(f"数据目录不存在: {self.data_dir}")

        # 检查必要的环境变量
        required_env_vars = ['DB_HOST', 'DB_USER', 'DB_NAME']
        for var in required_env_vars:
            if not os.environ.get(var):
                errors.append(f"环境变量未设置: {var}")

        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("配置验证通过")
        return True

    def display_config(self):
        """显示当前配置"""
        print("=== 机构行为分析配置 ===")
        print(f"数据目录: {self.data_dir}")
        print(f"输出目录: {self.output_dir}")
        print(f"分析分割日期: {self.analysis_split_date}")
        print(f"目标机构: {self.target_institutions}")
        print(f"数据库主机: {self.db_host}:{self.db_port}")
        print(f"数据库名称: {self.db_name}")


# 机构类型映射配置
INSTITUTION_CONFIG = {
    'types': ['bank', 'insurance', 'fund', 'securities'],
    'min_holding_value': 10000000,  # 最小持仓金额（1000万）
    'top_institutions': 20,         # 重点机构数量
    'tracking_period': 30           # 跟踪周期（天）
}

# 债券分类配置
BOND_CATEGORY_CONFIG = {
    'interest_rate_bonds': [
        '国债-新债', '国债-老债',
        '政策性金融债-新债', '政策性金融债-老债',
        '地方政府债'
    ],
    'credit_bonds': [
        '中期票据', '短期/超短期融资券', '企业债'
    ]
}

# 期限映射配置
MATURITY_CONFIG = {
    '≦1Y': '<=1Y',
    '1-3Y': '1-3Y',
    '3-5Y': '3-5Y',
    '5-7Y': '5-7Y',
    '7-10Y': '7-10Y',
    '10-15Y': '10-15Y',
    '15-20Y': '15-20Y',
    '20-30Y': '20-30Y',
    '>30Y': '>30Y'
}


if __name__ == "__main__":
    # 测试配置
    config = Config()
    config.display_config()
    config.ensure_directories()
