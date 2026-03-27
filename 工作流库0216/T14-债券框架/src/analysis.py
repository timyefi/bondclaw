# -*- coding: utf-8 -*-
"""
债券框架 - 核心分析模块
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from numpy.linalg import LinAlgError
from tqdm import tqdm

import config


def preprocess_factor_data(df, factor_name):
    """
    改进后的自动类型判断预处理

    参数:
        df: 包含'value'列的DataFrame
        factor_name: 因子名称

    返回:
        pd.Series: 处理后的数据序列
    """
    df['value'] = pd.to_numeric(df['value'], errors='coerce').ffill()

    if pd.notna(factor_name):
        if '同比' in factor_name:
            return df['value'].pct_change()
        if '环比' in factor_name:
            return df['value'].diff()
        if '率' in factor_name or '指数' in factor_name:
            return df['value']

    stats = df['value'].describe()
    if (stats['mean'] < 1) & (stats['std'] < 1):
        return df['value']
    df['value'] = df['value'].replace([np.inf, -np.inf], np.nan).ffill()
    return df['value'].pct_change()


def pca_reduce(df, n_components=0.95):
    """PCA降维处理"""
    pca = PCA(n_components=n_components)
    reduced = pca.fit_transform(df)
    return pd.DataFrame(reduced, index=df.index), pca.explained_variance_ratio_


def ridge_regression(X, y, alpha=1.0):
    """岭回归建模"""
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    return model


def batch_regression(yield_curve, factors_dict, window_size=None,
                     group_type=None, rolling_window=60):
    """
    改进后的回归函数，支持整体指标分析

    参数:
        yield_curve: 收益率曲线代码
        factors_dict: 因子字典
        window_size: 窗口大小
        group_type: None表示单因子分析，'price'/'quantity'表示整体分析
        rolling_window: 滚动窗口大小（月）

    返回:
        pd.DataFrame: 回归结果
    """
    from src.utils import get_yield_curve_data, get_standardized_data

    yield_data = get_yield_curve_data(yield_curve)

    if group_type is None:
        # 单因子分析
        results = []
        for code, name in tqdm(factors_dict.items()):
            try:
                factor_data = get_standardized_data(code)
                merged = pd.merge(yield_data, factor_data, on='date',
                                  how='inner', suffixes=('_yield', ''))

                merged['processed'] = preprocess_factor_data(merged, name)
                merged = merged.replace([np.inf, -np.inf], np.nan)
                merged = merged.dropna().sort_values('date')
                merged = merged.dropna(subset=['processed', 'yield_rate'])

                if len(merged) < 12:
                    continue

                if window_size is None:
                    # 全局回归
                    if merged['processed'].isnull().any():
                        continue
                    y = merged['yield_rate']
                    model = sm.OLS(y, merged['processed']).fit()

                    results.append({
                        '因子代码': code,
                        '因子名称': name,
                        '模型类型': '自回归模型',
                        '系数': model.params['processed'],
                        'p值': model.pvalues['processed'],
                        'R方': model.rsquared,
                        'DW统计量': sm.stats.durbin_watson(model.resid),
                        '协整关系': merged['processed'].isnull().any()
                    })
                else:
                    # 滚动窗口回归
                    dates = pd.date_range(
                        merged['date'].min() + pd.DateOffset(months=window_size),
                        merged['date'].max(), freq='MS'
                    )

                    for end_date in dates:
                        start_date = end_date - pd.DateOffset(months=window_size)
                        window_data = merged[
                            (merged['date'] > start_date) &
                            (merged['date'] <= end_date)
                        ]
                        if window_data['processed'].isnull().any():
                            continue

                        y = window_data['yield_rate']
                        model = sm.OLS(y, window_data['processed']).fit()

                        results.append({
                            'date': end_date,
                            '因子代码': code,
                            '因子名称': name,
                            '模型类型': '自回归模型',
                            '系数': model.params['processed'],
                            'p值': model.pvalues['processed'],
                            'R方': model.rsquared,
                            'DW统计量': sm.stats.durbin_watson(model.resid),
                            '协整关系': window_data['processed'].isnull().any()
                        })
            except LinAlgError:
                pass
            except Exception:
                pass

        if results:
            df = pd.DataFrame(results)
            if 'R方' not in df.columns:
                df['R方'] = np.nan
            return df
        else:
            return pd.DataFrame(columns=['因子代码', '因子名称', '系数', 'p值', 'R方'])

    else:
        # 整体指标分析
        dynamic_group_results = []
        all_factors = []
        for code in factors_dict.keys():
            factor_data = get_standardized_data(code)
            factor_data = factor_data.set_index('date')
            all_factors.append(factor_data['value'].rename(code))

        yield_data = yield_data[
            yield_data['date'] >= pd.to_datetime('2002-01-04')
        ]

        merged = pd.concat(all_factors, axis=1).join(
            yield_data.set_index('date')
        )

        factor_cols = list(factors_dict.keys())
        merged[factor_cols] = merged[factor_cols].astype(np.float64)
        merged[factor_cols] = merged[factor_cols].ffill()
        merged[factor_cols] = merged[factor_cols].bfill()
        merged[factor_cols] = merged[factor_cols].fillna(0)

        merged = merged.dropna(subset=['yield_rate'])

        if merged[factor_cols].isnull().any().any():
            nan_cols = merged[factor_cols].columns[
                merged[factor_cols].isnull().any()
            ].tolist()
            merged = merged.drop(columns=nan_cols)
            factor_cols = [col for col in factor_cols if col not in nan_cols]

        dates = pd.date_range(
            merged.index.min() + pd.DateOffset(months=rolling_window),
            merged.index.max(), freq='MS'
        )

        for end_date in dates:
            start_date = end_date - pd.DateOffset(months=rolling_window)
            window_data = merged[
                (merged.index > start_date) &
                (merged.index <= end_date)
            ]
            if len(window_data) < 12:
                continue

            X_window = window_data[factor_cols]
            y_window = window_data['yield_rate']

            X_reduced, var_ratio = pca_reduce(X_window)
            model = ridge_regression(X_reduced, y_window)
            r2 = model.score(X_reduced, y_window)

            dynamic_group_results.append({
                'date': end_date,
                'group_type': group_type,
                'r2': r2,
                'var_ratio': var_ratio.sum(),
                'n_factors': len(factors_dict),
                'n_components': X_reduced.shape[1]
            })

        return pd.DataFrame(dynamic_group_results)


# ============== 资金因子定价分析函数 ==============

def calculate_optimal_shift(fund_rate, yield_rate, shift_range=(-0.5, 0.5), step=0.01):
    """寻找最优平移值"""
    best_shift = 0
    best_corr = -1

    fund_series = pd.Series(fund_rate).dropna()
    yield_series = pd.Series(yield_rate).dropna()

    common_index = fund_series.index.intersection(yield_series.index)
    fund_series = fund_series.loc[common_index]
    yield_series = yield_series.loc[common_index]

    for shift in np.arange(shift_range[0], shift_range[1], step):
        shifted_rate = fund_series + shift
        corr = np.corrcoef(shifted_rate, yield_series)[0, 1]
        if corr > best_corr:
            best_corr = corr
            best_shift = shift
    return best_shift, best_corr


def calculate_rolling_shift(df, window=30, min_periods=10):
    """优化滚动窗口计算逻辑"""
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.dropna().sort_values('dt')

    if df['dt'].duplicated().any():
        raise ValueError("存在重复日期，请先去重")
    if len(df) < min_periods:
        raise ValueError(f"有效数据量不足{min_periods}条，当前{len(df)}条")

    dated_df = df.set_index('dt').sort_index()

    fund_roll = dated_df['fund_rate'].rolling(
        window=window, min_periods=min_periods, closed='both'
    )
    yield_roll = dated_df['yield_rate'].rolling(
        window=window, min_periods=min_periods, closed='both'
    )

    fund_windows = [w.values.tolist() for w in fund_roll]
    yield_windows = [w.values.tolist() for w in yield_roll]

    roll_df = pd.DataFrame({
        'fund_window': fund_windows,
        'yield_window': yield_windows
    }, index=dated_df.index).dropna()

    def vectorized_shift(row):
        try:
            fund_rates = pd.Series(row['fund_window'])
            yield_rates = pd.Series(row['yield_window'])
            return calculate_optimal_shift(fund_rates, yield_rates)[0]
        except Exception:
            return np.nan

    shifts = roll_df.apply(vectorized_shift, axis=1).rename('最优平移值')

    recent_dates = dated_df.last('30D').index
    for end_date in recent_dates:
        window_data = dated_df.loc[
            end_date - pd.Timedelta(window):end_date
        ]
        if len(window_data) >= min_periods:
            shifts.loc[end_date] = calculate_optimal_shift(
                window_data['fund_rate'],
                window_data['yield_rate']
            )[0]

    return shifts.reset_index(name='最优平移值')


def build_analysis_dataset(factor_code, yield_code, lag_days=5):
    """构建分析数据集"""
    from src.utils import load_financial_data, load_yield_data

    fund = load_financial_data(factor_code)
    yield_data = load_yield_data(yield_code)

    merged = pd.merge_asof(
        yield_data.sort_index(),
        fund.sort_index(),
        left_index=True,
        right_index=True,
        direction='nearest',
        tolerance=pd.Timedelta(days=7)
    ).dropna()

    merged = merged.rename_axis('dt').reset_index()

    shift_series = calculate_rolling_shift(merged)
    merged['最优平移值'] = shift_series['最优平移值']

    merged = merged.replace(0, np.nan).dropna(how='any')
    merged['预期缺口'] = merged['fund_rate'] + merged['最优平移值']

    merged = merged.ffill().bfill()
    merged = merged.dropna(subset=['fund_rate', 'yield_rate', '最优平移值'])

    if len(merged) == 0:
        raise ValueError("合并后数据集为空")

    # 滞后项生成
    merged['yield_lag1'] = merged['yield_rate'].shift(1)
    merged['yield_lag2'] = merged['yield_rate'].shift(2)
    merged['yield_lag3'] = merged['yield_rate'].shift(3)

    # 自回归项
    merged['yield_ar1'] = merged['yield_rate'].rolling(5).mean()
    merged['yield_ar2'] = merged['yield_rate'].rolling(10).mean()

    merged = merged.ffill().dropna()

    keep_columns = [
        'dt', 'fund_rate', 'yield_rate', '预期缺口', '最优平移值',
        'yield_lag1', 'yield_lag2', 'yield_lag3', 'yield_ar1', 'yield_ar2'
    ]
    merged = merged[keep_columns]

    return merged


def run_regression_analysis(df):
    """执行回归分析"""
    results = {}
    lags = {
        '当期': 0,
        '领先5日': 5,
        '领先15日': 15,
        '领先30日': 30
    }

    for name, lag in lags.items():
        try:
            X = sm.add_constant(df[['fund_rate', '预期缺口']].shift(lag))
            y = df['yield_rate']

            valid_idx = X.dropna().index.intersection(y.index)
            X = X.loc[valid_idx]
            y = y.loc[valid_idx]

            model = sm.OLS(y, X)
            results[name] = model.fit()
        except Exception as e:
            print(f"[ERROR] {name}回归失败: {str(e)}")
            raise

    return results


def rolling_regression(df, window=252):
    """滚动回归分析"""
    params = []
    for i in range(len(df) - window):
        sub_df = df.iloc[i:i+window]
        X = sm.add_constant(sub_df[['fund_rate', '预期缺口']])
        model = sm.OLS(sub_df['yield_rate'], X).fit()
        params.append({
            'dt': sub_df['dt'].iloc[-1],
            'fund_beta': model.params['fund_rate'],
            'gap_beta': model.params['预期缺口']
        })
    return pd.DataFrame(params)


def run_regression_advanced(df):
    """处理自相关和异方差的增强模型"""
    results = {}

    # 基础模型
    X_basic = sm.add_constant(df[['fund_rate', '预期缺口']])
    model_basic = sm.OLS(df['yield_rate'], X_basic)
    results['基础模型'] = model_basic.fit(cov_type='HC3')

    # 自回归模型
    X_ar = sm.add_constant(df[['fund_rate', '预期缺口', 'yield_ar1', 'yield_ar2']])
    model_ar = sm.OLS(df['yield_rate'], X_ar)
    results['自回归模型'] = model_ar.fit(cov_type='HC3')

    # 误差修正模型
    df['短期缺口'] = df['预期缺口'] - df['预期缺口'].shift(1)
    ecm_data = df[['fund_rate', '短期缺口', 'yield_ar1']].copy()
    ecm_data['delta_yield'] = df['yield_rate'].diff()
    ecm_data = ecm_data.dropna()

    X_ecm = sm.add_constant(ecm_data[['fund_rate', '短期缺口', 'yield_ar1']])
    model_ecm = sm.OLS(ecm_data['delta_yield'], X_ecm)
    results['误差修正模型'] = model_ecm.fit(cov_type='HC3')

    return results
