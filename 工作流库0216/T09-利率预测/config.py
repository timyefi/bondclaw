"""
T09 - 利率预测 配置文件

本配置文件包含数据库连接、模型参数和路径配置。
敏感信息应通过环境变量设置。
"""

import os

# =============================================================================
# 数据库配置
# =============================================================================

DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'your_user'),
    'password': os.environ.get('DB_PASSWORD', 'your_password'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '3306'),
    'db': 'bond'
}

# 各数据库配置
DB_CONFIG_BOND = DB_CONFIG.copy()
DB_CONFIG_BOND['db'] = 'bond'

DB_CONFIG_YQ = DB_CONFIG.copy()
DB_CONFIG_YQ['db'] = 'yq'

DB_CONFIG_EDB = DB_CONFIG.copy()
DB_CONFIG_EDB['db'] = 'edb'

# =============================================================================
# 模型配置
# =============================================================================

MODEL_CONFIG = {
    # 子模型1: 基于行情集中度 - 短期预测
    'model1': {
        'name': '行情集中度模型',
        'type': 'short_term',
        'horizon': 63,  # 预测天数 (约3个月)
        'weights': {
            'sentiment': 0.4,
            'concentration': 0.6
        },
        'features': ['concentration', 'concentration_rol_avg_21d',
                     'concentration_chg_5d', 'concentration_detrend'],
        'algorithm': 'GradientBoostingRegressor',
        'params': {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 3,
            'random_state': 42
        }
    },

    # 子模型2: 基于交易拥挤度 - 超短期预测
    'model2': {
        'name': '交易拥挤度模型',
        'type': 'ultra_short',
        'horizon': 30,  # 预测天数 (约1个月)
        'weights': {
            'trading_heat': 1.0
        },
        'features': ['avg_yield', 'congestion_rate', 'congestion_momentum', 'yield_volatility_20d'],
        'algorithm': 'LightGBM',
        'params': {
            'random_state': 42,
            'n_estimators': 100,
            'learning_rate': 0.05
        }
    },

    # 子模型3: 基于资金供需 - 中长期预测
    'model3': {
        'name': '资金供需模型',
        'type': 'medium_long',
        'horizon': 365,  # 预测天数 (约1年)
        'weights': {
            'supply_demand': 1.0
        },
        'features': ['avg_yield', 'demand_supply_gap', 'sin_day', 'cos_day'],
        'algorithm': 'PolynomialRegression',
        'params': {
            'degree': 2
        }
    },

    # 子模型4: 基于银行负债成本 - 中期预测
    'model4': {
        'name': '银行负债成本模型',
        'type': 'medium',
        'horizon': 365,  # 预测天数 (约1年)
        'weights': {
            'wealth_management': 0.30,
            'deposit_3y': 0.25,
            'deposit_6m': 0.25,
            'ncd': 0.20
        },
        'algorithm': 'Prophet',
        'params': {}
    },

    # 子模型5: 基于基本面和自然利率 - 长期预测
    'model5': {
        'name': '自然利率模型',
        'type': 'long',
        'horizon': 360,  # 预测天数 (约1年)
        'weights': {
            'fundamental': 0.5,
            'natural_rate': 0.5
        },
        'algorithm': 'StateSpaceModel',
        'params': {
            'alpha_c3': 0.25,
            'alpha_pi': 0.2,
            'gamma_r': 0.8,
            'zeta': 0.3,
            'sigma_g': 0.003,
            'sigma_z': 0.002
        }
    }
}

# =============================================================================
# 路径配置
# =============================================================================

import pathlib

# 项目根目录
PROJECT_ROOT = pathlib.Path(__file__).parent.absolute()

PATH_CONFIG = {
    'project_root': str(PROJECT_ROOT),
    'src_dir': str(PROJECT_ROOT / 'src'),
    'data_dir': str(PROJECT_ROOT / 'data'),
    'output_dir': str(PROJECT_ROOT / 'output'),
    'assets_dir': str(PROJECT_ROOT / 'assets')
}

# =============================================================================
# 数据表配置
# =============================================================================

TABLE_CONFIG = {
    # 输入表
    'marketinfo_curve': 'bond.marketinfo_curve',
    'basicinfo_curve': 'bond.basicinfo_curve',
    'market_concentration': 'bond.market_concentration_90pct',
    'dealtinfo': 'bond.dealtinfo',
    'wealth_management_performance': 'yq.理财业绩跟踪',
    'deposit_cost': 'yq.存款成本',

    # 输出表
    'yield_concentration_pred': 'bond.analysis_yield_concentration_pred',
    'yield_congestion_forecast': 'bond.bond_yield_congestion_forecast',
    'yield_demand_supply_forecast': 'bond.bond_yield_demand_supply_forecast',
    'liability_cost_prediction': 'yq.负债成本预测结果'
}

# =============================================================================
# 预测配置
# =============================================================================

PREDICTION_CONFIG = {
    # 预测起始日期 (通常为昨天)
    'default_start_date': None,  # None表示使用昨天

    # 预测结束日期
    'end_date': '2026-12-31',

    # 历史数据起始日期
    'history_start_date': '2015-01-01',

    # 训练数据年限
    'training_years': 5,

    # 关键预测时间点
    'key_dates': ['2025-06-30', '2025-12-31', '2026-06-30', '2026-12-31']
}

# =============================================================================
# 日志配置
# =============================================================================

LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': str(PROJECT_ROOT / 'output' / 'prediction.log')
}

# =============================================================================
# 质量控制标准
# =============================================================================

QUALITY_CONFIG = {
    # 预测准确率标准
    'short_term_accuracy_threshold': 0.80,
    'medium_term_accuracy_threshold': 0.75,
    'long_term_accuracy_threshold': 0.70,

    # 数据完整性标准
    'data_completeness_threshold': 0.95,

    # 模型R2阈值
    'r2_threshold': 0.3
}


if __name__ == '__main__':
    print("配置验证:")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"数据库主机: {DB_CONFIG['host']}")
    print(f"模型数量: {len(MODEL_CONFIG)}")
