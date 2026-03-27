import argparse
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
import sqlalchemy
from scipy import interpolate, signal
import warnings
from prophet import Prophet
import os
import matplotlib.pyplot as plt
import matplotlib
from sklearn.ensemble import GradientBoostingRegressor
import lightgbm as lgb

# -- 全局配置matplotlib以支持中文 --
# 指定中文字体，'WenQuanYi Micro Hei' 是一款常用的高质量开源中文字体
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
# 解决负号'-'显示为方块的问题
matplotlib.rcParams['axes.unicode_minus'] = False
# ------------------------------------

warnings.filterwarnings('ignore')

class LiabilityCostPredictor:
    """
    封装了银行负债成本和资金利率的预测逻辑。
    
    该类负责从数据库获取所需指标的历史数据，基于给定的未来假设
    （理财收益率、存款利率等），通过样条插值生成预测，并最终计算
    银行负债成本和银行间7天资金价格的预测值。
    """
    def __init__(self, db_config, bd='2015-01-01', plot_output_dir=None):
        """
        初始化预测器。

        :param db_config: 包含数据库连接信息的字典。
        :param bd: 历史数据获取的起始日期。
        :param plot_output_dir: 可选，用于保存诊断图的目录路径。
        """
        self.sql_engine = sqlalchemy.create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s' % (
                db_config['user'],
                db_config['password'],
                db_config['host'],
                db_config['port'],
                db_config['db'],
            ), poolclass=sqlalchemy.pool.NullPool
        )
        self.bd = bd
        self.plot_output_dir = plot_output_dir
        if self.plot_output_dir:
            os.makedirs(self.plot_output_dir, exist_ok=True)
            print(f"诊断图将保存到: {self.plot_output_dir}")

    def _fetch_series(self, sql_template, end_date):
        """
        根据SQL模板和结束日期从数据库获取单个时间序列数据。

        :param sql_template: 包含 {bd} 和 {ed} 占位符的SQL查询字符串。
        :param end_date: 数据获取的结束日期。
        :return: 一个包含'x' (日期) 和 'y' (值) 列的DataFrame。
        """
        sql = sql_template.format(bd=self.bd, ed=end_date)
        df = pd.read_sql(sql, self.sql_engine)
        df['x'] = pd.to_datetime(df['x'])
        return df

    def _get_data(self, end_date):
        """
        从数据库获取所有需要的原始时间序列数据。
        """
        indicators_to_fetch = {
            '理财业绩跟踪': "SELECT DT AS x, avg(近1年净值年化增长率) AS y from yq.理财业绩跟踪 WHERE 近1年净值年化增长率 is not null AND DT>='{bd}' AND DT <= '{ed}' group by dt order by dt",
            '定期存款3年利率': "SELECT DT AS x, close AS y from edb.edbdata WHERE trade_code='M0329279' AND DT>='{bd}' AND DT <= '{ed}'",
            '定期存款6月利率': "select A.dt as x, A.close as y from edb.edbdata A inner join edb.edbinfo B on A.TRADE_CODE=B.TRADE_CODE where A.TRADE_CODE = 'M0071532' and A.dt>='{bd}' AND A.dt <= '{ed}'",
            '存单平均收益率': "SELECT dt as x, avg(收益率) as y from( SELECT A.dt, LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * ( (RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年') ) AS 曲线期限, '存单' AS 曲线名称, SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1) AS 隐含评级, A.CLOSE AS 收益率 FROM bond.marketinfo_curve A INNER JOIN bond.basicinfo_curve B ON A.trade_code = B.TRADE_CODE WHERE A.dt>='{bd}' AND A.dt <= '{ed}' and B.classify2 like '中债商业银行同业存单到期收益率%%')sq where sq.隐含评级 not in ('A+','A','A-') and sq.曲线期限 >0 group by dt",
            '国债平均收益率': "SELECT A.dt as x, avg(A.CLOSE) AS y FROM bond.marketinfo_curve A INNER JOIN bond.basicinfo_curve B ON A.trade_code = B.TRADE_CODE WHERE A.dt <='{ed}' and A.dt>='{bd}' and B.classify2 ='中债国债到期收益率' group by dt",
            '10年国债收益率': "SELECT A.dt as x, A.CLOSE AS y FROM bond.marketinfo_curve A INNER JOIN bond.basicinfo_curve B ON A.trade_code = B.TRADE_CODE WHERE A.dt <='{ed}' AND A.dt>='{bd}' AND B.SEC_NAME = '中债国债到期收益率:10年'",
            '资金价格': "SELECT DT AS x, close AS y from edb.edbdata WHERE trade_code='M1006337' AND DT>='{bd}' AND DT <= '{ed}'", # 新增：DR007作为资金价格的历史数据
            '负债成本': "SELECT dt AS x, 存款付息率 AS y from yq.存款成本 WHERE dt>='{bd}' AND dt <= '{ed}'"
        }
        
        datasets = {}
        for name, sql_template in indicators_to_fetch.items():
            datasets[name] = self._fetch_series(sql_template, end_date)
        return datasets

    def _resample_daily(self, df):
        """
        将数据重采样为日度数据，并填充缺失值。

        :param df: 待处理的DataFrame。
        :return: 重采样后的DataFrame。
        """
        if df.empty or 'x' not in df.columns:
            return pd.DataFrame(columns=['x', 'y'])
        df = df.set_index('x')
        df = df.resample('D').mean()
        df = df.fillna(method='ffill').fillna(method='bfill')
        return df.reset_index()

    def _save_prophet_plots(self, model, forecast, name):
        """保存Prophet模型的诊断图。"""
        if not self.plot_output_dir:
            return
        
        try:
            # 绘制并保存预测图
            fig1 = model.plot(forecast)
            ax = fig1.gca()
            ax.set_title(f'{name} 预测与历史数据拟合图', size=15)
            ax.set_xlabel('日期', size=12)
            ax.set_ylabel('值', size=12)
            plot_path1 = os.path.join(self.plot_output_dir, f'{name}_forecast.png')
            fig1.savefig(plot_path1)
            plt.close(fig1)

            # 绘制并保存成分分解图
            fig2 = model.plot_components(forecast)
            plot_path2 = os.path.join(self.plot_output_dir, f'{name}_components.png')
            fig2.savefig(plot_path2)
            plt.close(fig2)

            print(f"为 '{name}' 保存诊断图成功。")
        except Exception as e:
            print(f"为 '{name}' 保存诊断图时发生错误: {e}")


    def _generate_future_assumptions(self, hist_df, name, growth_params=None):
        """
        使用Prophet模型为单个指标生成未来的动态预测假设。

        :param hist_df: 包含该指标历史数据的DataFrame ('x'和'y'列)。
        :param name: 指标名称，用于打印信息。
        :param growth_params: 可选，用于逻辑增长模型的参数字典 (e.g., {'growth': 'logistic', 'floor': 0.1, 'cap': 1.0})
        :return: 一个包含未来关键日期及其预测值的字典。
        """
        print(f"正在为 '{name}' 生成动态预测...")
        
        # 1. 准备数据以适配Prophet
        prophet_df = hist_df.rename(columns={'x': 'ds', 'y': 'y'})
        
        # 如果历史数据少于2条，无法训练，返回空字典
        if len(prophet_df) < 2:
            print(f"警告: '{name}' 的历史数据不足，无法生成预测。")
            return {}

        # 2. 初始化并训练Prophet模型
        if growth_params and growth_params.get('growth') == 'logistic':
            print(f"  -> 为 '{name}' 应用逻辑增长模型...")
            floor = growth_params.get('floor')
            cap = growth_params.get('cap')
            if floor is not None and cap is not None:
                prophet_df['floor'] = floor
                prophet_df['cap'] = cap
                print(f"     - Floor: {floor:.4f}, Cap: {cap:.4f}")
                model = Prophet(growth='logistic')
            else:
                print("     - 警告: 逻辑增长模型缺少 floor 或 cap 参数，退回到线性模型。")
                model = Prophet()
        else:
            # 默认使用线性增长模型
            model = Prophet()
            
        model.fit(prophet_df)

        # 3. 创建未来的日期序列用于预测
        future_dates = model.make_future_dataframe(periods=365*2) # 预测未来两年
        if growth_params and growth_params.get('growth') == 'logistic':
            floor = growth_params.get('floor')
            cap = growth_params.get('cap')
            if floor is not None and cap is not None:
                future_dates['floor'] = floor
                future_dates['cap'] = cap

        # 4. 生成预测
        forecast = model.predict(future_dates)
        
        # 特殊处理：如果预测目标是“资金价格”，则应用一个朝向长期目标的调整
        if name == '资金价格':
            print("  -> 检测到 '资金价格'，应用特殊目标调整...")
            # 目标是相对于原始预测的调整值: 25年末-15BP, 26年末-35BP (恢复为原始值)
            adjustments = {
                '2025-12-31': -0.15,
                '2026-12-31': -0.35
            }
            
            # 1. 准备插值点
            deviation_points = {}
            
            # 偏差的起点是最后一个历史点，偏差为0，确保平滑连接
            start_date = prophet_df['ds'].max()
            deviation_points[start_date] = 0.0

            # 2. 直接使用调整值作为偏差
            for dt_str, adjustment_val in adjustments.items():
                target_date = pd.to_datetime(dt_str)
                predicted_val_series = forecast.loc[forecast['ds'] == target_date, 'yhat']
                if not predicted_val_series.empty:
                    predicted_val = predicted_val_series.iloc[0]
                    deviation_points[target_date] = adjustment_val # 直接使用调整值
                    print(f"    - 日期: {dt_str}, 原始预测: {predicted_val:.4f}, 调整: {adjustment_val:.4f}, 目标: {predicted_val + adjustment_val:.4f}")
                else:
                    print(f"警告: 未能在预测中找到日期 {dt_str}，跳过此目标点。")

            if len(deviation_points) > 1:
                # 3. 创建并插值偏差Series
                deviation_series = pd.Series(deviation_points).sort_index()
                
                # 创建一个与forecast对齐的完整日期范围的Series
                full_deviation_series = pd.Series(index=forecast['ds'], dtype=float)
                # 将我们已知的偏差点放进去
                full_deviation_series.update(deviation_series)
                
                # 进行时间插值
                interpolated_deviations = full_deviation_series.interpolate(method='time')
                # 填充插值范围之外的区域（未来部分）
                interpolated_deviations.fillna(method='ffill', inplace=True)
                # 确保历史部分偏差为0
                interpolated_deviations.fillna(0, inplace=True)

                # 4. 应用调整
                print("  -> 正在应用插值后的偏差调整...")
                forecast['yhat'] = forecast['yhat'] + interpolated_deviations.values

        # 保存诊断图，用于分析和解释
        self._save_prophet_plots(model, forecast, name)

        # 5. 提取关键时间点的预测值
        key_dates = ['2025-06-30', '2025-12-31', '2026-06-30', '2026-12-31']
        assumptions = {}
        for dt_str in key_dates:
            target_date = pd.to_datetime(dt_str)
            closest_forecast = forecast.iloc[forecast['ds'].sub(target_date).abs().idxmin()]
            assumptions[dt_str] = closest_forecast['yhat']
        
        print(f"'{name}' 的动态预测值: {assumptions}")
        return assumptions
    
    def _create_prediction_df(self, predictions, latest_value, latest_date, start_date, end_date='2026-12-31'):
        """
        使用三次样条插值创建预测曲线。

        :param predictions: 未来关键节点的预测值。
        :param latest_value: 最近的历史值。
        :param latest_date: 最近的历史值对应的日期。
        :param start_date: 预测开始的日期。
        :param end_date: 预测结束的日期。
        :return: 包含预测值的DataFrame。
        """
        dates = list(predictions.keys())
        values = list(predictions.values())
        
        dates.insert(0, latest_date.strftime('%Y-%m-%d'))
        values.insert(0, latest_value)
        
        dates = pd.to_datetime(dates)
        pred_dates_filtered = pd.date_range(start=start_date, end=end_date, freq='D')
        
        days = [(d - dates[0]).days for d in dates]
        pred_days = [(d - dates[0]).days for d in pred_dates_filtered]

        # 移除重复的日期以进行插值
        unique_days, unique_indices = np.unique(days, return_index=True)
        unique_values = np.array(values)[unique_indices]
        
        # 至少需要两个点才能进行插值
        if len(unique_days) < 2:
            # 如果点不够，则用最新值进行常数填充
            return pd.DataFrame({'x': pred_dates_filtered, 'y': latest_value})

        # 使用PCHIP插值（分段三次Hermite插值），这种方法可以保证保形性，避免过冲导致的不合理值（如负利率）。
        # 它比'cubic'样条更适合处理金融时间序列。
        f = interpolate.PchipInterpolator(unique_days, unique_values, extrapolate=True)
        pred_values = f(pred_days)
            
        return pd.DataFrame({'x': pred_dates_filtered, 'y': pred_values})

    def _calculate_dominant_cycle(self, series):
        """
        使用FFT从时间序列中计算主导周期。
        :param series: pd.Series, 时间序列数据，索引为日期。
        :return: float, 主导周期的天数。
        """
        if len(series) < 20: # 需要足够的数据点才有意义
            print("      - 警告: 历史数据太少，无法计算周期，使用默认值(3年)。")
            return 365 * 3

        # 1. Detrend the data to remove long-term trends
        detrended_series = signal.detrend(series.values)

        # 2. Perform FFT
        yf = np.fft.rfft(detrended_series)
        # The corresponding frequencies for each point
        xf = np.fft.rfftfreq(len(detrended_series), 1) # Sample spacing is 1 day

        # 3. Find the peak frequency, ignoring the DC component (at index 0)
        if len(yf) > 1:
            idx = np.argmax(np.abs(yf[1:])) + 1
            peak_freq = xf[idx]
        else: # Should not happen given the length check above
            return 365 * 3

        # 4. Convert frequency to period in days
        if peak_freq == 0:
            print("      - 警告: 分析得到的主导频率为0，使用默认值(3年)。")
            return 365 * 3
        
        dominant_period = 1 / peak_freq
        
        return dominant_period

    def _create_timeseries_features(self, df, target_col, feature_cols):
        """为给定的DataFrame创建时间序列特征"""
        df = df.copy()
        
        # 确保日期列是datetime类型
        df['x'] = pd.to_datetime(df['x'])
        
        # 1. 时间特征
        df['month'] = df['x'].dt.month
        df['dayofyear'] = df['x'].dt.dayofyear
        df['weekday'] = df['x'].dt.weekday
        df['weekofyear'] = df['x'].dt.isocalendar().week.astype(int)

        # 2. 滞后特征 (Lags)
        # 对目标和核心驱动因素都创建滞后项
        cols_to_lag = [target_col] + feature_cols
        for col in cols_to_lag:
            if col in df.columns:
                for lag in [1, 7, 14, 30]:
                    df[f'{col}_lag_{lag}'] = df[col].shift(lag)

        # 3. 滑动窗口特征 (Rolling Window)
        for col in cols_to_lag:
             if col in df.columns:
                for window in [7, 14, 30]:
                    df[f'{col}_roll_mean_{window}'] = df[col].rolling(window=window).mean()
                    df[f'{col}_roll_std_{window}'] = df[col].rolling(window=window).std()
        
        return df

    def _predict_ml_recursively(self, hist_df, future_df, target_col, feature_cols):
        """
        使用LightGBM模型进行递归预测。
        
        :param hist_df: 包含所有相关指标历史数据的DataFrame。
        :param future_df: 包含未来日期和上游预测（驱动因素）的DataFrame。
        :param target_col: 当前需要预测的目标列名 (e.g., '存单')。
        :param feature_cols: 用于预测的核心驱动因素列表 (e.g., ['资金价格', '定存3年'])。
        :return: 带有预测结果的future_df。
        """
        print(f"  -- 开始递归预测: {target_col} --")
        
        # 1. 为历史数据创建完整的特征集
        hist_featured = self._create_timeseries_features(hist_df, target_col, feature_cols)
        
        # 2. 确定最终用于训练的特征列
        # 我们使用所有生成的特征，除了原始的目标列和日期列
        all_features = [col for col in hist_featured.columns if col not in [target_col, 'x']]
        
        # 移除因滞后和滑动窗口产生的NaN值，准备训练数据
        train_df = hist_featured.dropna(subset=all_features + [target_col])
        X_train, y_train = train_df[all_features], train_df[target_col]
        
        # 3. 训练模型
        model = lgb.LGBMRegressor(random_state=42, n_estimators=100, learning_rate=0.05, num_leaves=31)
        model.fit(X_train, y_train)
        
        # 4. 递归预测
        # 使用历史数据的最后部分来初始化递归所需的前置数据
        dynamic_df = hist_df.copy()
        
        future_df_with_preds = future_df.copy()

        for i in range(len(future_df_with_preds)):
            # a. 准备当前预测点的数据框
            current_point_df = future_df_with_preds.iloc[[i]]
            
            # b. 合并历史和当前点，以生成完整的特征
            temp_df = pd.concat([dynamic_df, current_point_df], ignore_index=True)
            
            # c. 创建时间序列特征
            temp_featured = self._create_timeseries_features(temp_df, target_col, feature_cols)
            
            # d. 提取当前预测点（最后一行）的特征
            features_for_today = temp_featured.iloc[[-1]][all_features]
            
            # e. 预测
            prediction = model.predict(features_for_today)[0]
            
            # f. 在future_df中记录预测结果
            future_df_with_preds.loc[future_df_with_preds.index[i], target_col] = prediction

            # g. 更新动态数据框，将刚刚的预测结果加入，用于下一次循环的特征生成
            dynamic_df = pd.concat([
                dynamic_df, 
                future_df_with_preds.iloc[[i]]
            ], ignore_index=True)

        print(f"  -- 完成递归预测: {target_col} --")
        return future_df_with_preds

    def _prepare_historical_df(self, datasets, col_name_map, end_date, for_training=True):
        """
        一个辅助方法，用于准备一个完整、对齐的历史数据DataFrame。
        :param for_training: 如果为True，返回完全填充的数据。如果为False，返回还原了阶梯数据真实性的数据。
        """
        hist_indicator_names = list(col_name_map.keys()) + ['国债平均收益率', '10年国债收益率']
        
        # 移除6个月定存，因为它将被派生
        if '定期存款6月利率' in hist_indicator_names:
            hist_indicator_names.remove('定期存款6月利率')

        valid_hist_dfs = []
        for name in hist_indicator_names:
            # 阶梯型数据使用原始数据，其他重采样
            if name in ['定期存款3年利率', '负债成本']:
                 valid_hist_dfs.append(datasets[name].rename(columns={'y': name}))
            elif name in datasets:
                 valid_hist_dfs.append(self._resample_daily(datasets[name]).rename(columns={'y': name}))

        if not valid_hist_dfs:
            raise ValueError("没有任何有效的历史数据可供合并。")
            
        historical_df = valid_hist_dfs[0]
        for df in valid_hist_dfs[1:]:
            historical_df = pd.merge(historical_df, df, on='x', how='outer')
        
        historical_df = historical_df.sort_values('x').set_index('x')
        # 填充前，先把需要保持稀疏的列备份
        sparse_cols_to_restore = {}
        if not for_training:
            if '定期存款3年利率' in historical_df.columns:
                sparse_cols_to_restore['定存3年'] = datasets['定期存款3年利率'].set_index('x')['y']
            if '负债成本' in historical_df.columns:
                sparse_cols_to_restore['负债成本'] = datasets['负债成本'].set_index('x')['y']

        # 为了训练和计算，我们需要一个完全填充的数据集
        historical_df.interpolate(method='time', inplace=True)
        historical_df.fillna(method='ffill', inplace=True)
        historical_df.fillna(method='bfill', inplace=True)
        
        # 在重命名和计算利差前，先重置索引
        historical_df.reset_index(inplace=True)
        historical_df = historical_df[historical_df['x'] <= end_date]
        historical_df.rename(columns=col_name_map, inplace=True)

        # 在填充数据上计算6M利差
        if '定存3年' in historical_df.columns:
            # 创建一个临时用于计算利差的历史表
            temp_spread_df = pd.merge(
                datasets['定期存款3年利率'],
                datasets['定期存款6月利率'],
                on='x', how='outer'
            ).sort_values('x')
            temp_spread_df.columns = ['x', 'y_3y', 'y_6m']
            temp_spread_df.fillna(method='ffill', inplace=True)
            temp_spread_df = temp_spread_df[temp_spread_df['x'] <= end_date]
            if not temp_spread_df.empty:
                last_hist_spread = temp_spread_df.iloc[-1]['y_6m'] - temp_spread_df.iloc[-1]['y_3y']
                historical_df['定存6月'] = historical_df['定存3年'] + last_hist_spread

        # 在所有计算完成后，再删除所有不需要的行
        historical_df.dropna(inplace=True)
        
        if historical_df.empty:
            raise ValueError("合并和清洗后无有效历史数据，无法进行预测。")

        # 如果不是为了训练，就还原稀疏列的本来面目
        if not for_training:
            historical_df.set_index('x', inplace=True)
            for col_name, sparse_series in sparse_cols_to_restore.items():
                # 使用 update 来精确地将 NaN 恢复
                # 为了避免类型问题，先将要更新的列转为 float
                historical_df[col_name] = historical_df[col_name].astype(float)
                # 创建一个全为 NaN 的Series，然后用稀疏数据填充
                nan_series = pd.Series(np.nan, index=historical_df.index, name=col_name)
                nan_series.update(sparse_series)
                historical_df[col_name] = nan_series
            historical_df.reset_index(inplace=True)

        return historical_df

    def predict(self, prediction_start_date_str):
        """
        执行完整的预测流程。
        新流程：为每个成本分项动态确定预测起点，独立预测后，
        智能合并历史与未来数据，形成统一时间序列，再进行后续计算。
        """
        prediction_start_date = pd.to_datetime(prediction_start_date_str)
        
        # 1. 获取所有原始数据
        datasets = self._get_data(prediction_start_date_str)



        # 2. 联立预测第一步：独立预测资金价格，作为后续预测的“下限”
        print("\n--- 联立预测第1步：预测资金价格以作下限 ---")
        # 修复：使用普通读取，而不是 .pop()，以避免从datasets字典中移除该项
        hist_funding_df = self._resample_daily(datasets['资金价格'])
        funding_assumption = self._generate_future_assumptions(hist_funding_df, '资金价格')
        
        if not funding_assumption:
            raise ValueError("由于'资金价格'无法生成预测，整个预测流程中止。")
        
        latest_funding_info = {
            'value': float(hist_funding_df[hist_funding_df['x'] <= prediction_start_date].iloc[-1]['y']),
            'date': hist_funding_df[hist_funding_df['x'] <= prediction_start_date].iloc[-1]['x']
        }
        pred_funding_df = self._create_prediction_df(
            funding_assumption, latest_funding_info['value'], latest_funding_info['date'], latest_funding_info['date'] + timedelta(days=1)
        )
        hist_funding_to_use = hist_funding_df[hist_funding_df['x'] <= latest_funding_info['date']]
        full_funding_series = pd.concat([hist_funding_to_use, pred_funding_df], ignore_index=True)
        # 准备一个标准的floor_df，用于注入到其他模型
        floor_df = full_funding_series.rename(columns={'x': 'ds', 'y': 'floor'})
        print("资金价格下限预测完成。")
        
        # 3. 联立预测第二步：构建回归预测链
        print("\n--- 联立预测第2步：构建回归预测链 ---")

        # 为了方便，先准备一个包含所有历史数据的对齐DataFrame
        # 注意：这里的负债成本是历史真实值，仅用于训练，不会用于直接预测
        # 修复：在映射表中加入'资金价格'
        col_name_map = {'理财业绩跟踪': '理财', '定期存款3年利率': '定存3年', '定期存款6月利率': '定存6月', '存单平均收益率': '存单', '负债成本': '负债成本', '资金价格': '资金价格'}
        all_hist_df = self._prepare_historical_df(datasets, col_name_map, prediction_start_date)

        # --- 步骤1：预测基础利率（资金价格、3年存款） ---
        print("步骤1: 正在预测基础利率...")
        
        # 计算t0时刻的6个月与3年期定存利差
        hist_3y = datasets['定期存款3年利率'].rename(columns={'y': 'y_3y'})
        hist_6m = datasets['定期存款6月利率'].rename(columns={'y': 'y_6m'})
        merged_spread_hist = pd.merge(hist_3y, hist_6m, on='x', how='outer').sort_values('x')
        merged_spread_hist.fillna(method='ffill', inplace=True)
        last_known_spread_row = merged_spread_hist[merged_spread_hist['x'] <= prediction_start_date].iloc[-1]
        spread_6m_3y = last_known_spread_row['y_6m'] - last_known_spread_row['y_3y']
        print(f"  计算得到6个月与3年期定存利差为: {spread_6m_3y:.4f}")

        # 资金价格已经独立预测完毕，这里只处理3年期存款
        pred_dfs = {}
        name = '定期存款3年利率'
        
        # --- 改进的3年期存款利率预测逻辑 (锚定回归) ---
        print(f"  -> 正在为 '{name}' 应用分阶段预测模型...")
        
        # a. 定义模型参数
        TARGET_SPREAD = 0.05  # 长期目标利差：5个基点
        TRIGGER_SPREAD = 0.1 # 回归触发利差：10个基点
        
        # b. 获取最后一个历史值作为起点
        processed_hist_df = datasets[name]
        latest_record = processed_hist_df[processed_hist_df['x'] <= prediction_start_date].iloc[-1]
        latest_val_info = {'value': float(latest_record['y']), 'date': latest_record['x']}
        constant_rate_during_hold = latest_val_info['value']
        # 关键修复：重新定义被误删的变量
        individual_start_date = latest_val_info['date'] + timedelta(days=1)
        print(f"    - 历史终点 (锚定值): {latest_val_info['date'].strftime('%Y-%m-%d')} -> {constant_rate_during_hold:.4f}")

        # c. 寻找回归触发点
        future_funding_df = full_funding_series[full_funding_series['x'] > latest_val_info['date']].copy()
        future_funding_df['spread'] = constant_rate_during_hold - future_funding_df['y']
        
        trigger_point_df = future_funding_df[future_funding_df['spread'] >= TRIGGER_SPREAD]
        
        if trigger_point_df.empty:
            print("    - 警告: 在整个预测期内未找到回归触发点。存款利率将保持恒定。")
            trigger_date = pd.to_datetime('2026-12-31') # 将触发点设到最末
        else:
            trigger_date = trigger_point_df.iloc[0]['x']
        print(f"    - 回归触发日期: {trigger_date.strftime('%Y-%m-%d')}")

        # d. 构建分阶段预测曲线
        #    第一阶段：横盘期
        hold_dates_df = future_funding_df[future_funding_df['x'] < trigger_date][['x']].copy()
        hold_dates_df['y'] = constant_rate_during_hold
        
        #    第二阶段：回归期
        convergence_dates_df = future_funding_df[future_funding_df['x'] >= trigger_date]
        if not convergence_dates_df.empty:
            # 定义回归期的目标曲线
            target_track_df = convergence_dates_df[['x', 'y']].copy()
            target_track_df['y'] += TARGET_SPREAD
            
            # 从目标曲线上采样关键点
            key_dates = ['2025-06-30', '2025-12-31', '2026-06-30', '2026-12-31']
            future_assumptions = {}
            
            # --- 关键修复 V2: 严格分离锚点和目标点，并处理边缘情况 ---
            for dt_str in key_dates:
                target_date = pd.to_datetime(dt_str)
                # 目标点的日期必须严格晚于触发日期
                if target_date > trigger_date:
                    # 关键修复：使用 .loc 按标签索引，而不是 .iloc 按位置索引
                    closest_row = target_track_df.loc[target_track_df['x'].sub(target_date).abs().idxmin()]
                    future_assumptions[dt_str] = closest_row['y']
            
            # 如果所有关键日期都早于触发点，则 future_assumptions 可能为空。
            # 这种情况下，需要一个备用目标来确保插值可以进行。
            if not future_assumptions and len(target_track_df) > 1:
                # 使用整个目标曲线的最后一个点作为最终的回归目标
                last_target_row = target_track_df.iloc[-1]
                future_assumptions[last_target_row['x'].strftime('%Y-%m-%d')] = last_target_row['y']
                print(f"      - 警告: 未找到合适的关键日期，已使用最终目标点 {last_target_row['x'].strftime('%Y-%m-%d')} -> {last_target_row['y']:.4f} 作为备用。")

            # 使用插值生成平滑回归曲线
            # 锚点是触发日的横盘利率
            if future_assumptions:
                convergence_pred_df = self._create_prediction_df(
                    future_assumptions,
                    constant_rate_during_hold,
                    trigger_date,
                    trigger_date
                )
                # 筛选出实际需要的回归期部分
                convergence_pred_df = convergence_pred_df[convergence_pred_df['x'] >= trigger_date]
                pred_df = pd.concat([hold_dates_df, convergence_pred_df], ignore_index=True)
            else:
                # 如果连备用目标都没有（例如，触发点就是最后一天），则整个预测期都是横盘
                pred_df = hold_dates_df
        else:
            pred_df = hold_dates_df

        pred_dfs[name] = pred_df

        # --- 关键修复：重构下游预测的数据准备逻辑 ---
        # 1. 准备一个包含所有未来预测所需驱动因素的DataFrame。
        #    它的起始点必须是所有预测中最早的那个，以确保数据完整。
        future_dates_df = pd.DataFrame({'x': pd.date_range(start=individual_start_date, end='2026-12-31', freq='D')})

        # 2. 将所有上游指标的 *完整序列* (历史+预测) 合并到这个DataFrame上。
        #    a. 首先合并资金价格的完整序列。
        future_df = pd.merge(future_dates_df, full_funding_series.rename(columns={'y': '资金价格'}), on='x', how='left')
        
        #    b. 准备3年期存款的完整序列，并合并。
        #       这里要精确地将锚点之前的历史与锚点之后的预测拼接起来。
        hist_df_3y = datasets['定期存款3年利率']
        pred_df_3y = pred_dfs['定期存款3年利率']
        hist_3y_to_use = hist_df_3y[hist_df_3y['x'] <= latest_val_info['date']]
        full_series_3y = pd.concat([hist_3y_to_use, pred_df_3y], ignore_index=True).rename(columns={'y': '定存3年'})
        
        future_df = pd.merge(future_df, full_series_3y[['x', '定存3年']], on='x', how='left')
        
        # 3. 安全地填充数据。
        #    因为合并的是包含历史的完整序列，所以简单的ffill就能正确处理不同指标历史结束日期不一致的情况。
        future_df.sort_values('x', inplace=True)
        future_df.fillna(method='ffill', inplace=True)
        future_df.fillna(method='bfill', inplace=True)

        # 4. 派生6个月存款利率
        future_df['定存6月'] = future_df['定存3年'] + spread_6m_3y

        # --- 步骤2: 改进的存单收益率预测 (基于利差模型) ---
        print("\n--- 步骤2: 改进的存单收益率预测 (基于利差模型) ---")

        # a. 计算历史利差: 存单 - 资金价格
        print("  a. 计算'存单 - 资金价格'的历史利差...")
        hist_spread_df = pd.DataFrame({
            'x': all_hist_df['x'],
            'y': all_hist_df['存单'] - all_hist_df['资金价格']
        }).dropna()

        # b. 使用Prophet预测未来利差
        print("  b. 使用Prophet预测利差的未来走势...")
        spread_assumption = self._generate_future_assumptions(hist_spread_df, '存单与资金价格利差')

        if not spread_assumption:
            print("  警告: 未能生成利差预测，将使用最后一个已知利差作为常数进行预测。")
            last_known_spread = hist_spread_df['y'].iloc[-1]
            future_df['存单'] = future_df['资金价格'] + last_known_spread
        else:
            # c. 创建完整的未来利差序列
            print("  c. 创建完整的未来利差曲线...")
            latest_spread_info = {
                'value': float(hist_spread_df.iloc[-1]['y']),
                'date': hist_spread_df.iloc[-1]['x']
            }
            # 确保预测从最后一个历史点之后开始
            spread_start_date = latest_spread_info['date'] + timedelta(days=1)
            pred_spread_df = self._create_prediction_df(
                spread_assumption, latest_spread_info['value'], latest_spread_info['date'], spread_start_date
            )
            
            # d. 合成最终的存单利率预测
            print("  d. 合成存单利率预测 = 预测资金价格 + 预测利差...")
            # 将预测的利差合并到未来的DataFrame中
            future_df = pd.merge(future_df, pred_spread_df.rename(columns={'y': '利差'}), on='x', how='left')
            # 填充可能因日期不对齐产生的NaN
            future_df['利差'].fillna(method='ffill', inplace=True)
            future_df['利差'].fillna(method='bfill', inplace=True)
            future_df['存单'] = future_df['资金价格'] + future_df['利差']
            future_df.drop(columns=['利差'], inplace=True) # 用完即弃

        print("--- 存单收益率预测完成 ---")

        # --- 步骤3: 改进的理财收益率预测 (基于利差模型 vs 存单) ---
        print("\n--- 步骤3: 改进的理财收益率预测 (基于利差模型 vs 存单) ---")
        
        # a. 计算历史利差及建模参数
        print("  a. 计算'理财 - 存单'的历史利差及建模参数...")
        hist_spread_wm_df = pd.DataFrame({
            'x': all_hist_df['x'],
            'y': all_hist_df['理财'] - all_hist_df['存单']
        }).dropna()

        # 定义逻辑增长模型的上下限
        spread_floor = hist_spread_wm_df['y'].min()
        spread_cap = hist_spread_wm_df['y'].median() # 使用中位数作为上限，反映压缩趋势
        print(f"    - 已确定逻辑增长模型参数: Floor={spread_floor:.4f}, Cap={spread_cap:.4f}")


        # b. 使用带约束的Prophet模型预测利差的未来走势
        print("  b. 使用带约束的Prophet模型预测利差的未来走势...")
        spread_wm_assumption = self._generate_future_assumptions(
            hist_spread_wm_df,
            '理财与存单利差',
            growth_params={'growth': 'logistic', 'floor': spread_floor, 'cap': spread_cap}
        )

        if not spread_wm_assumption:
            print("  警告: 未能生成理财-存单利差预测，将使用最后一个已知利差作为常数。")
            last_known_spread_wm = hist_spread_wm_df['y'].iloc[-1]
            future_df['理财'] = future_df['存单'] + last_known_spread_wm
        else:
            # c. 创建完整的未来利差序列
            print("  c. 创建完整的未来利差曲线...")
            latest_spread_wm_info = {
                'value': float(hist_spread_wm_df.iloc[-1]['y']),
                'date': hist_spread_wm_df.iloc[-1]['x']
            }
            spread_wm_start_date = latest_spread_wm_info['date'] + timedelta(days=1)
            pred_spread_wm_df = self._create_prediction_df(
                spread_wm_assumption, latest_spread_wm_info['value'], latest_spread_wm_info['date'], spread_wm_start_date
            )

            # d. 合成最终的理财利率预测
            print("  d. 合成理财利率预测 = 预测存单价格 + 预测利差...")
            future_df = pd.merge(future_df, pred_spread_wm_df.rename(columns={'y': '利差_wm'}), on='x', how='left')
            future_df['利差_wm'].fillna(method='ffill', inplace=True)
            future_df['利差_wm'].fillna(method='bfill', inplace=True)
            future_df['理财'] = future_df['存单'] + future_df['利差_wm']
            future_df.drop(columns=['利差_wm'], inplace=True)

        print("--- 理财收益率预测完成 ---")

        # --- 整合历史与未来 (V2 - 鲁棒版本) ---
        print("\n--- 整合历史与预测数据 (除负债成本外) ---")

        # 负债成本将被最后计算，因此从待处理列表中移除
        all_final_cols = ['理财', '定存3年', '定存6月', '存单', '资金价格', '国债平均收益率', '10年国债收益率']
        final_series_list = []
        
        # 反转列名映射以便查找
        reverse_col_name_map = {v: k for k, v in col_name_map.items()}
        # 为派生列和直接映射的列提供查找路径
        reverse_col_name_map['定存6月'] = '定期存款6月利率'
        reverse_col_name_map['国债平均收益率'] = '国债平均收益率'
        reverse_col_name_map['10年国债收益率'] = '10年国债收益率'

        hist_df_filled = self._prepare_historical_df(datasets, col_name_map, prediction_start_date, for_training=True)

        for col_name in all_final_cols:
            if col_name not in hist_df_filled.columns and col_name not in future_df.columns:
                continue # 如果列完全不存在，则跳过
            
            print(f"  组装完整序列: {col_name}")
            original_name = reverse_col_name_map.get(col_name)

            if not original_name or original_name not in datasets:
                print(f"    警告: 无法找到 '{col_name}' 的原始数据源，将仅使用填充历史。")
                hist_part = hist_df_filled[['x', col_name]]
                last_hist_date_for_col = pd.to_datetime(prediction_start_date)
            else:
                last_hist_date_for_col = datasets[original_name][datasets[original_name]['x'] <= prediction_start_date]['x'].max()
                hist_part = hist_df_filled[['x', col_name]][hist_df_filled['x'] <= last_hist_date_for_col]
            
            if col_name in future_df.columns:
                pred_part = future_df[['x', col_name]][future_df['x'] > last_hist_date_for_col]
                full_series = pd.concat([hist_part, pred_part], ignore_index=True)
            else:
                full_series = hist_part
            
            final_series_list.append(full_series.set_index('x'))

        if not final_series_list:
            raise ValueError("未能构建任何最终的时间序列。")
            
        unified_df = pd.concat(final_series_list, axis=1, join='outer')
        
        # 对合并后的数据进行填充，确保没有因合并产生的空值
        unified_df.interpolate(method='time', inplace=True)
        unified_df.fillna(method='ffill', inplace=True)
        unified_df.fillna(method='bfill', inplace=True)
        unified_df.reset_index(inplace=True)

        # --- 步骤4: 在完整时间轴上合成银行负债成本 ---
        print("\n--- 步骤4: 在完整时间轴上合成银行负债成本 ---")

        # a. 定义权重
        weights = {
            '理财': 0.30,
            '定存3年': 0.25,
            '定存6月': 0.25,
            '存单': 0.20
        }
        print(f"    - 使用权重: {weights}")

        # b. 在整个时间轴上计算加权平均值
        unified_df['负债成本'] = (
            unified_df['理财'] * weights['理财'] +
            unified_df['定存3年'] * weights['定存3年'] +
            unified_df['定存6月'] * weights['定存6月'] +
            unified_df['存单'] * weights['存单']
        )

        # c. 校准以平滑衔接最后一个真实历史点
        print("    - 正在校准以衔接最后一个真实历史点...")
        hist_cost_df = datasets['负债成本']
        last_hist_record_series = hist_cost_df[hist_cost_df['x'] <= prediction_start_date]
        
        if not last_hist_record_series.empty:
            last_hist_record = last_hist_record_series.iloc[-1]
            last_hist_val = float(last_hist_record['y'])
            last_hist_date = last_hist_record['x']

            # 找到第一个计算出的值 (在最后一个历史点之后)
            first_calc_record = unified_df[unified_df['x'] > last_hist_date].iloc[0]
            first_calc_val = first_calc_record['负债成本']

            # 计算并应用差值到所有计算点上
            delta = last_hist_val - first_calc_val
            print(f"      - LastHistVal={last_hist_val:.4f}, FirstCalcVal={first_calc_val:.4f}, Delta={delta:.4f}")
            unified_df.loc[unified_df['x'] > last_hist_date, '负债成本'] += delta
        else:
            print("    - 警告: 未找到 '负债成本' 的历史数据进行校准。")
        print("--- 银行负债成本合成完成 ---")


        # --- 第五步：预测国债收益率 ---
        print("步骤5: 正在预测国债收益率...")
        # 筛选出未来需要预测的部分
        future_indices = unified_df['x'] > prediction_start_date
        merged_pred_df = unified_df[future_indices].copy()
        
        # 使用为训练准备的、完全填充的历史数据进行计算
        historical_df_for_calc = self._prepare_historical_df(datasets, col_name_map, prediction_start_date, for_training=True)

        # 5a. 准备纯历史数据DataFrame，用于计算历史波动性和利差
        # 复用上面已经准备好的训练用历史数据
        
        constant_spread = historical_df_for_calc['10年国债收益率'].iloc[-1] - historical_df_for_calc['国债平均收益率'].iloc[-1]
        
        # 5b. 计算历史波动振幅
        historical_diff = historical_df_for_calc['国债平均收益率'] - historical_df_for_calc['负债成本']
        amplitude = historical_diff.std()
        if pd.isna(amplitude) or amplitude == 0:
            print("警告: 历史波动振幅为0或无效，将使用一个小的默认值(0.1)以避免计算错误。")
            amplitude = 0.1
        print(f"\n根据历史数据计算，国债收益率围绕负债成本的波动振幅(标准差)为: {amplitude:.4f}\n")

        # 5c. 生成正弦波
        print("    - 正在从国债收益率历史数据中分析主导周期...")
        full_hist_yield = historical_df_for_calc['国债平均收益率']
        
        if not full_hist_yield.empty:
            dominant_period_days = self._calculate_dominant_cycle(full_hist_yield)
        else:
            print("      - 警告: 国债收益率历史数据为空，无法计算周期，使用默认值(3年)。")
            dominant_period_days = 365 * 1.5
        
        print(f"    - 分析得到主导周期为: {dominant_period_days:.2f} 天")
        
        frequency = 2 * np.pi / dominant_period_days
        time_steps = np.arange(len(merged_pred_df))
        
        # 5d. 精确计算初始相位
        last_historical_yield = historical_df_for_calc['国债平均收益率'].iloc[-1]
        first_predicted_cost = merged_pred_df['负债成本'].iloc[0]
        initial_diff = last_historical_yield - first_predicted_cost
        
        arcsin_input = np.clip(initial_diff / amplitude, -1.0, 1.0)
        phase1 = np.arcsin(arcsin_input)
        phase2 = np.pi - phase1

        cos1 = np.cos(phase1)
        
        if np.sign(initial_diff) * np.sign(cos1) >= 0:
            phase = phase2
        else:
            phase = phase1

        sin_wave = amplitude * np.sin(frequency * time_steps + phase)
        
        # 5e. 将预测值填充到unified_df的未来部分
        unified_df.loc[future_indices, '国债平均收益率'] = unified_df.loc[future_indices, '负债成本'].values + sin_wave
        unified_df.loc[future_indices, '10年国债收益率'] = unified_df.loc[future_indices, '国债平均收益率'].values + constant_spread

        # -- 校准以确保平滑过渡 --
        print("\n--- 应用平滑过渡校准 ---")
        # 负债成本已经经过更精确的校准，因此从这个通用校准循环中移除
        for col_name in ['存单', '理财']:
            # 找到最后一个历史值
            original_name = reverse_col_name_map.get(col_name)
            if not original_name or original_name not in datasets: continue
            
            last_hist_record = datasets[original_name][datasets[original_name]['x'] <= prediction_start_date]
            if last_hist_record.empty: continue
            last_hist_val = last_hist_record.iloc[-1]['y']
            last_hist_date = last_hist_record.iloc[-1]['x']

            # 找到第一个预测值
            first_pred_record = unified_df[unified_df['x'] > last_hist_date].iloc[0]
            first_pred_val = first_pred_record[col_name]
            
            # 计算差值并应用
            delta = last_hist_val - first_pred_val
            print(f"  校准 {col_name}: LastHistVal={last_hist_val:.4f}, FirstPredVal={first_pred_val:.4f}, Delta={delta:.4f}")
            unified_df.loc[unified_df['x'] > last_hist_date, col_name] += delta

        # --- 最后一步: 严格还原阶梯型利率的真实历史数据 ---
        print("\n--- 最后一步: 还原历史数据的原始稀疏性 ---")
        
        # 定义需要还原稀疏性的列及其在原始datasets中的名称
        # 负债成本已被重计算，不再需要还原
        sparse_cols_map = {
            '定存3年': '定期存款3年利率',
            '定存6月': '定期存款6月利率',
        }

        # 为了高效更新，先将 unified_df 的索引设置为日期
        unified_df.set_index('x', inplace=True)

        for col_name, original_name in sparse_cols_map.items():
            if col_name in unified_df.columns and original_name in datasets:
                print(f"  正在处理: {col_name}")
                
                # 1. 获取原始的、稀疏的历史数据
                sparse_hist_series = datasets[original_name].set_index('x')['y']
                
                # 2. 获取该列在历史时期（直到预测开始日期）的索引
                hist_indices = unified_df.index[unified_df.index <= prediction_start_date]
                
                # 3. 将 unified_df 中对应列的历史部分完全置为 NaN
                unified_df.loc[hist_indices, col_name] = np.nan
                
                # 4. 使用原始的稀疏数据，通过 update 方法精确地填入值
                # update 只会填充索引匹配且源数据非 NaN 的值，完美符合需求
                unified_df[col_name].update(sparse_hist_series)

        # 操作完成后，将日期索引恢复为普通列
        unified_df.reset_index(inplace=True)
        
        return unified_df

    def save_predictions(self, predictions_df, run_date_str):
        """
        将预测结果及中间值保存到数据库，并使用'run_date'进行版本控制。
        该方法不使用显式事务，将删除和插入作为两个独立操作。

        :param predictions_df: 包含预测结果的DataFrame。
        :param run_date_str: 本次预测运行的日期 (YYYY-MM-DD)，用于版本控制。
        """
        if predictions_df.empty:
            print("没有可供保存的预测数据。")
            return
            
        df_to_save = predictions_df.copy()
        # 添加 run_date 列用于版本控制
        df_to_save['run_date'] = pd.to_datetime(run_date_str)

        df_to_save.rename(columns={
            'x': 'prediction_date',
            '理财': 'wealth_management_rate',
            '定存3年': 'deposit_rate_3y',
            '定存6月': 'deposit_rate_6m',
            '存单': 'ncd_rate',
            '负债成本': 'liability_cost',
            '资金价格': 'funding_rate',
            '国债平均收益率': 'gov_bond_rate_avg',
            '10年国债收益率': 'gov_bond_rate_10y'
        }, inplace=True)
        
        table_name = '负债成本预测结果'

        # 采用最直接的“连接-执行-关闭”模式，并确保两个操作使用同一个连接。
        connection = None
        try:
            # 获取一个连接，用于本次保存的所有操作
            connection = self.sql_engine.connect()

            # --- 操作 1: 删除当天旧数据 ---
            delete_query = sqlalchemy.text(f"DELETE FROM {table_name} WHERE run_date = :current_run_date")
            connection.execute(delete_query, {'current_run_date': run_date_str})
            print(f"清理了表中运行于 {run_date_str} 的旧数据。")

            # --- 操作 2: 插入新数据 ---
            # 使用同一个连接将数据写入数据库
            df_to_save.to_sql(
                table_name,
                connection,  # 显式传递连接对象
                if_exists='append',
                index=False,
                method='multi',
                chunksize=100  # 分块写入，避免单次插入数据量过大
            )
            print(f"成功保存 {len(df_to_save)} 条新预测记录到数据库表 '{table_name}'。")
        
        except Exception as e:
            print(f"数据库操作失败: {e}")
            print("警告：旧数据可能已被删除，但新数据未能写入，可能导致数据不一致。")
        finally:
            if connection:
                connection.close()
                print("数据库连接已关闭。")


def main():
    """
    主执行函数，用于运行银行负债成本预测并保存结果。
    
    可以通过命令行参数 '--date' 指定预测的起始日期，
    格式为 'YYYY-MM-DD'。如果未提供，则默认为昨天。
    """
    parser = argparse.ArgumentParser(description='银行负债成本及资金利率预测执行脚本')
    parser.add_argument('--date', help="预测起始日期，格式 'YYYY-MM-DD'。默认为昨天。")
    args = parser.parse_args()

    if args.date:
        try:
            run_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"错误：日期格式无效。请输入 'YYYY-MM-DD' 格式的日期。")
            return
    else:
        run_date = date.today() - timedelta(days=1)
    
    run_date_str = run_date.strftime('%Y-%m-%d')
    print(f"开始为日期 {run_date_str} 生成预测...")

    # 为本次运行创建专属的绘图输出目录
    plot_output_dir = f'/data/项目/快速处理/2025/利率预测/子模型4-基于银行负债成本-中期/prediction_plots_{run_date_str}'

    # 数据库连接配置
    db_config = {
        'user': 'hz_work',
        'password': 'Hzinsights2015',
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': '3306',
        'db': 'yq',
    }

    predictor = None
    try:
        # 初始化预测器，并传入绘图目录
        predictor = LiabilityCostPredictor(db_config, plot_output_dir=plot_output_dir)
        
        # 执行预测
        predictions_df = predictor.predict(run_date_str)
        print("预测计算完成。")
        
        # -- 数据最终诊断 --
        print("\n--- 准备写入数据库的数据体检报告 ---")
        print("1. 数据类型及非空值统计 (info):")
        # 使用 BytesIO 来捕获 info() 的输出，避免直接打印到 stdout 导致格式问题
        from io import StringIO
        buffer = StringIO()
        predictions_df.info(buf=buffer)
        print(buffer.getvalue())

        # 保存预测结果到数据库
        predictor.save_predictions(predictions_df, run_date_str)
        
        print(f"\n预测任务成功完成！")

    except Exception as e:
        print(f"\n预测过程中发生错误: {e}")
    finally:
        # 主流程中不再需要管理连接，连接已在 save_predictions 中按需处理
        print("预测流程结束。")

if __name__ == '__main__':
    main() 