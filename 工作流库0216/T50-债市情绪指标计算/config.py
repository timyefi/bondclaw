#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T50 - 债市情绪指标计算 配置文件

该配置文件包含所有可配置的参数，敏感信息通过环境变量获取。
"""

import os
from typing import Dict, Any


class Config:
    """债市情绪指标计算配置类"""

    # ==================== 滚动窗口配置 ====================
    # 近N个交易日用于计算增长率（默认20天，约1个月）
    WINDOW_SIZE: int = 20

    # ==================== 情绪指标权重配置 ====================
    # 收益率增长率的权重（默认0.5，表示收益率和成交金额同等重要）
    YIELD_WEIGHT: float = 0.5

    # ==================== 10年国债代码配置 ====================
    # 10年国债收益率曲线代码
    YIELD_CURVE_CODE: str = 'L001619604'

    # ==================== 数据库表配置 ====================
    # 目标表名
    TARGET_TABLE: str = 'bond_market_sentiment'

    # ==================== 数据源配置 ====================
    # 收益率数据源表
    YIELD_SOURCE_TABLE: str = 'bond.marketinfo_curve'

    # 成交金额数据源表
    TRADING_SOURCE_TABLE: str = 'bond.dealtinfo'

    @property
    def window_size(self) -> int:
        """获取滚动窗口大小"""
        return int(os.environ.get('BOND_SENTIMENT_WINDOW_SIZE', self.WINDOW_SIZE))

    @property
    def yield_weight(self) -> float:
        """获取收益率权重"""
        return float(os.environ.get('BOND_SENTIMENT_YIELD_WEIGHT', self.YIELD_WEIGHT))

    @property
    def yield_curve_code(self) -> str:
        """获取10年国债代码"""
        return os.environ.get('BOND_SENTIMENT_YIELD_CODE', self.YIELD_CURVE_CODE)

    @property
    def target_table(self) -> str:
        """获取目标表名"""
        return os.environ.get('BOND_SENTIMENT_TARGET_TABLE', self.TARGET_TABLE)

    @staticmethod
    def get_yq_db_config() -> Dict[str, Any]:
        """
        获取YQ数据库配置

        所有敏感信息从环境变量获取
        """
        return {
            'host': os.environ.get('YQ_DB_HOST', 'localhost'),
            'port': int(os.environ.get('YQ_DB_PORT', 3306)),
            'user': os.environ.get('YQ_DB_USER', 'root'),
            'password': os.environ.get('YQ_DB_PASSWORD', ''),
            'database': os.environ.get('YQ_DB_NAME', 'yq'),
        }

    @staticmethod
    def get_bond_db_config() -> Dict[str, Any]:
        """
        获取Bond数据库配置

        所有敏感信息从环境变量获取
        """
        return {
            'host': os.environ.get('BOND_DB_HOST', 'localhost'),
            'port': int(os.environ.get('BOND_DB_PORT', 3306)),
            'user': os.environ.get('BOND_DB_USER', 'root'),
            'password': os.environ.get('BOND_DB_PASSWORD', ''),
            'database': os.environ.get('BOND_DB_NAME', 'bond'),
        }

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'window_size': self.window_size,
            'yield_weight': self.yield_weight,
            'yield_curve_code': self.yield_curve_code,
            'target_table': self.target_table,
            'yield_source_table': self.YIELD_SOURCE_TABLE,
            'trading_source_table': self.TRADING_SOURCE_TABLE,
        }

    def __repr__(self) -> str:
        """配置的字符串表示"""
        return (
            f"Config("
            f"window_size={self.window_size}, "
            f"yield_weight={self.yield_weight}, "
            f"yield_curve_code='{self.yield_curve_code}', "
            f"target_table='{self.target_table}'"
            f")"
        )


# 创建全局配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    print("=" * 50)
    print("T50 - 债市情绪指标计算 配置信息")
    print("=" * 50)
    print(f"滚动窗口大小: {config.window_size} 天")
    print(f"收益率权重: {config.yield_weight}")
    print(f"10年国债代码: {config.yield_curve_code}")
    print(f"目标表名: {config.target_table}")
    print("=" * 50)
    print("\n数据库配置（YQ）:")
    yq_config = Config.get_yq_db_config()
    print(f"  Host: {yq_config['host']}")
    print(f"  Port: {yq_config['port']}")
    print(f"  User: {yq_config['user']}")
    print(f"  Database: {yq_config['database']}")
    print("  Password: [HIDDEN]")

    print("\n数据库配置（Bond）:")
    bond_config = Config.get_bond_db_config()
    print(f"  Host: {bond_config['host']}")
    print(f"  Port: {bond_config['port']}")
    print(f"  User: {bond_config['user']}")
    print(f"  Database: {bond_config['database']}")
    print("  Password: [HIDDEN]")

    print("\n" + "=" * 50)
    print("环境变量配置说明:")
    print("=" * 50)
    print("可设置以下环境变量来覆盖默认配置:")
    print("")
    print("算法参数:")
    print("  BOND_SENTIMENT_WINDOW_SIZE    - 滚动窗口大小（默认20）")
    print("  BOND_SENTIMENT_YIELD_WEIGHT   - 收益率权重（默认0.5）")
    print("  BOND_SENTIMENT_YIELD_CODE     - 10年国债代码（默认L001619604）")
    print("  BOND_SENTIMENT_TARGET_TABLE   - 目标表名（默认bond_market_sentiment）")
    print("")
    print("YQ数据库:")
    print("  YQ_DB_HOST     - 数据库主机")
    print("  YQ_DB_PORT     - 数据库端口")
    print("  YQ_DB_USER     - 数据库用户名")
    print("  YQ_DB_PASSWORD - 数据库密码")
    print("  YQ_DB_NAME     - 数据库名称")
    print("")
    print("Bond数据库:")
    print("  BOND_DB_HOST     - 数据库主机")
    print("  BOND_DB_PORT     - 数据库端口")
    print("  BOND_DB_USER     - 数据库用户名")
    print("  BOND_DB_PASSWORD - 数据库密码")
    print("  BOND_DB_NAME     - 数据库名称")
