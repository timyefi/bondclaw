import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import warnings
import matplotlib.pyplot as plt
import matplotlib

warnings.filterwarnings('ignore')

# -- 全局配置matplotlib以支持中文 --
# 指定中文字体，'WenQuanYi Micro Hei' 是一款常用的高质量开源中文字体
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
# 解决负号'-'显示为方块的问题
matplotlib.rcParams['axes.unicode_minus'] = False



def get_yield_data(engine, start_date, end_date):
    """
    获取国债平均到期收益率。
    """
    print(f"正在获取从 {start_date} 到 {end_date} 的国债平均收益率...")
    sql = f"""
    SELECT 
        A.dt as trade_date,
        avg(A.CLOSE) AS avg_yield
    FROM bond.marketinfo_curve A
    INNER JOIN bond.basicinfo_curve B ON A.trade_code = B.TRADE_CODE
    WHERE A.dt BETWEEN '{start_date}' AND '{end_date}'
      AND B.classify2 = '中债国债到期收益率'
    GROUP BY A.dt
    """
    df = pd.read_sql(sql, engine)
    if df.empty:
        return pd.DataFrame(columns=['trade_date', 'avg_yield'])
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    print("国债平均收益率数据获取完成。")
    return df


def get_demand_supply_data(engine, start_date, end_date):
    """
    获取和计算债市的需求-供给数据 (严格遵循1.md的计算逻辑)。
    """
    print(f"正在获取从 {start_date} 到 {end_date} 的需求-供给数据...")

    # =========================================================================
    # Part 1: 计算总需求 (Demand Side), 严格复现 1.md 的步骤
    # =========================================================================
    print("正在计算总需求...")
    
    # 1.1 初始六个指标
    sql_demand1 = f"""
    select dt, B.SEC_NAME, avg(A.close/10000) as close
    from edb.edbdata_ths A
    inner join edb.edbinfo_ths B on A.TRADE_CODE=B.TRADE_CODE
    where A.TRADE_CODE in ('S003138026','S005890488','S004054283','S004054284','M004030789','M004030786')
      and A.dt between '{start_date}' and '{end_date}'
    group by dt, B.SEC_NAME order by dt
    """
    df = pd.read_sql(sql_demand1, engine)
    df = df.pivot_table(index='dt', columns='SEC_NAME', values='close').reset_index()

    # 1.2 合并理财规模
    sql_demand2 = f"SELECT dt, `理财规模` FROM yq.理财规模 WHERE dt BETWEEN '{start_date}' AND '{end_date}'"
    df1 = pd.read_sql(sql_demand2, engine)
    df = pd.merge(df, df1[['dt', '理财规模']], on='dt', how='outer')

    # 1.3 合并另一个债基数据源 M5207867
    sql_demand3 = f"SELECT dt, close/10000 as close FROM edb.edbdata WHERE trade_code='M5207867' AND dt BETWEEN '{start_date}' AND '{end_date}'"
    df1 = pd.read_sql(sql_demand3, engine)
    df = pd.merge(df, df1[['dt', 'close']], on='dt', how='outer')

    # 1.4 合并金融资负 M0150191
    sql_demand4 = f"SELECT dt, M0150191/10000 AS close1 FROM yq.金融资负 WHERE dt BETWEEN '{start_date}' AND '{end_date}'"
    df1 = pd.read_sql(sql_demand4, engine)
    df = pd.merge(df, df1[['dt', 'close1']], on='dt', how='outer')

    # 1.5 合并券商资管 M5524595
    sql_demand5 = f"SELECT dt, M5524595/10000 AS '券商资管' FROM yq.金融资负 WHERE dt BETWEEN '{start_date}' AND '{end_date}'"
    df1 = pd.read_sql(sql_demand5, engine)
    df = pd.merge(df, df1[['dt', '券商资管']], on='dt', how='outer')

    # 1.6 合并信托 M5207551
    sql_demand6 = f"SELECT dt, M5207551/100000000 AS '信托' FROM yq.金融资负 WHERE dt BETWEEN '{start_date}' AND '{end_date}'"
    df1 = pd.read_sql(sql_demand6, engine)
    df = pd.merge(df, df1[['dt', '信托']], on='dt', how='outer')

    # 1.7 数据清洗和插值 (与1.md完全一致)
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.sort_values(by='dt', ascending=True)
    df.replace(0, np.nan, inplace=True)
    df.interpolate(method='linear', inplace=True) # 只插值，不填充头尾

    # 1.8 计算衍生列和总和
    df = df.rename(columns={
        '开放式基金:债券型基金:总份额': '开放式债基总份额',
        '私募基金管理人:私募证券投资基金:资产净值:固定收益策略': '私募固收产品规模',
        '产险公司总资产': '产险公司总资产',
        '寿险公司总资产': '寿险公司总资产'
    })
    
    # 确保在计算前所有列都存在
    required_demand_cols = ['产险公司总资产', '寿险公司总资产', 'close', 'close1', '信托', '券商资管', '理财规模', '开放式债基总份额', '私募固收产品规模']
    for col in required_demand_cols:
        if col not in df.columns:
            df[col] = np.nan

    df['保险投债资金测算'] = (df['产险公司总资产'] + df['寿险公司总资产']) / 3
    
    sum_cols = ['close', 'close1', '信托', '券商资管', '理财规模', '保险投债资金测算', '开放式债基总份额', '私募固收产品规模']
    df['total_demand'] = df[sum_cols].sum(axis=1, skipna=True)
    df_demand = df[['dt', 'total_demand']].copy()

    print("总需求计算完成。")

    # =========================================================================
    # Part 2: 计算净供给 (Supply Side), 严格复现 1.md 的步骤
    # =========================================================================
    print("正在计算净供给...")

    # 2.1 获取债市总规模
    sql_supply_total = f"SELECT dt as 日期, 余额/10000 as 规模 FROM yq.债券市场规模 WHERE 类型='合计' AND dt BETWEEN '{start_date}' AND '{end_date}' ORDER BY dt"
    raw = pd.read_sql(sql_supply_total, engine)

    # 2.2 获取三部分银行持仓数据
    sql_bank1 = f"""
    select TRADE_DATE as 日期, sum(IFNULL(JRZ_HOLD, 0)) AS 金融债含存单, 0 as 政策性银行债
    from yq.investor_sh where TYPE= '银行自营' AND TRADE_DATE BETWEEN '{start_date}' AND '{end_date}' GROUP BY 日期 ORDER BY 日期
    """
    raw0 = pd.read_sql(sql_bank1, engine)

    sql_bank2 = f"""
    select trade_date as 日期, sum(IFNULL(商业银行债券,0)) as 金融债含存单1, sum(IFNULL(政策性银行债,0)) as 政策性银行债1
    from yq.investor_zz where 分类 in ('1.商业银行','2.信用社') AND trade_date BETWEEN '{start_date}' AND '{end_date}' GROUP BY 日期 ORDER BY 日期
    """
    raw01 = pd.read_sql(sql_bank2, engine)

    # 2.3 第一次合并与插值
    raw0 = pd.merge(raw0, raw01, on=['日期'], how='outer')
    raw0.sort_values(by='日期', inplace=True)
    raw0.interpolate(method='linear', inplace=True)
    raw0['金融债含存单'] = raw0['金融债含存单'].fillna(0) + raw0['金融债含存单1'].fillna(0)
    raw0['政策性银行债'] = raw0['政策性银行债'].fillna(0) + raw0['政策性银行债1'].fillna(0)
    raw0.drop(columns=['金融债含存单1', '政策性银行债1'], inplace=True)

    # 2.4 获取第三部分银行持仓并进行第二次合并与插值
    sql_bank3 = f"""
    select trade_date as 日期, sum(IFNULL(金融债券,0))+sum(IFNULL(同业存单,0)) as 金融债含存单2, 0 AS 政策性银行债2
    from yq.investor_sq where 分类 in ('2.存款类金融机构','1.政策性银行') AND trade_date BETWEEN '{start_date}' AND '{end_date}' GROUP BY 日期 ORDER BY 日期
    """
    raw01 = pd.read_sql(sql_bank3, engine)
    raw0 = pd.merge(raw0, raw01, on=['日期'], how='outer')
    raw0.sort_values(by='日期', inplace=True)
    raw0.interpolate(method='linear', inplace=True)
    raw0['金融债含存单'] = raw0['金融债含存单'].fillna(0) + raw0['金融债含存单2'].fillna(0)
    raw0['政策性银行债'] = raw0['政策性银行债'].fillna(0) + raw0['政策性银行债2'].fillna(0)
    raw0.drop(columns=['金融债含存单2', '政策性银行债2'], inplace=True)

    # 2.5 合并总规模和银行持仓，并进行最终插值和计算
    raw = pd.merge(raw, raw0, on=['日期'], how='outer')
    raw.sort_values(by='日期', inplace=True)
    raw.interpolate(method='linear', inplace=True)
    
    # 确保列存在，避免KeyError
    if '规模' not in raw.columns: raw['规模'] = np.nan
    if '金融债含存单' not in raw.columns: raw['金融债含存单'] = np.nan
    if '政策性银行债' not in raw.columns: raw['政策性银行债'] = np.nan

    # 修正: 在计算前将'日期'列转换为datetime，以匹配df_demand中的'dt'类型
    raw['日期'] = pd.to_datetime(raw['日期'])

    raw['net_supply'] = raw['规模'] - raw['金融债含存单']/10000 - raw['政策性银行债']/10000
    df_supply = raw[['日期', 'net_supply']].copy()
    df_supply.rename(columns={'日期': 'dt'}, inplace=True)

    print("净供给计算完成。")

    # =========================================================================
    # Part 3: 合并需求与供给，计算差值
    # =========================================================================
    df_final = pd.merge(df_demand, df_supply, on='dt', how='outer')
    df_final['dt'] = pd.to_datetime(df_final['dt'])
    df_final.sort_values(by='dt', inplace=True)
    df_final.interpolate(method='linear', inplace=True)

    df_final['demand_supply_gap'] = df_final['total_demand'] - df_final['net_supply']
    
    print("需求-供给数据计算完成。")
    return df_final.reset_index().rename(columns={'dt': 'trade_date'})[['trade_date', 'demand_supply_gap']]


def main():
    """
    主函数：执行数据获取、模型训练、预测和存储全过程。
    """
    print("--- 预测脚本开始执行 ---")
    
    # 1. 数据库连接
    db_config = {
        'user': 'hz_work',
        'password': 'Hzinsights2015',
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': '3306',
        'db': 'bond',
    }
    db_config_yq = db_config.copy()
    db_config_yq['db'] = 'yq'
    db_config_edb = db_config.copy()
    db_config_edb['db'] = 'edb'

    print("正在创建数据库连接引擎...")
    try:
        engine_bond = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}")
        engine_yq = create_engine(f"mysql+pymysql://{db_config_yq['user']}:{db_config_yq['password']}@{db_config_yq['host']}:{db_config_yq['port']}/{db_config_yq['db']}")
        engine_edb = create_engine(f"mysql+pymysql://{db_config_edb['user']}:{db_config_edb['password']}@{db_config_edb['host']}:{db_config_edb['port']}/{db_config_edb['db']}")
        # For simplicity in functions, we can create a dictionary of engines
        engines = {'bond': engine_bond, 'yq': engine_yq, 'edb': engine_edb}
        print("数据库连接引擎创建成功。")
    except Exception as e:
        print(f"创建数据库连接引擎时出错: {e}")
        return

    # 2. 定义数据时间范围（使用最近10年数据进行训练）
    end_date = datetime.now()
    start_date = end_date - relativedelta(years=10)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # 3. 获取数据
    df_yield = get_yield_data(engines['bond'], start_date_str, end_date_str)
    # The demand-supply function needs multiple engines, let's pass them all.
    # A cleaner way is to pass one engine and specify db in sql. Assuming `get_demand_supply_data` is adapted.
    # Let's adapt the function to take one main engine and it will handle different DBs.
    # For now, let's use a combined engine approach for simplicity of the call.
    # Re-writing the get_demand_supply_data to use a single engine and fully qualified table names.
    df_demand_supply = get_demand_supply_data(engine_bond, start_date_str, end_date_str) # bond engine has access to other dbs
    # 4. 数据整合与预处理
    print("正在整合所有数据...")
    df = pd.merge(df_yield, df_demand_supply, on='trade_date', how='left')
    
    df.set_index('trade_date', inplace=True)
    df.sort_index(inplace=True)
    df = df[df.index >= '2022-06-05']  # 筛选2022-06-05及以后的数据
    df = df.asfreq('D').interpolate(method='linear') # Fill weekends
    df.dropna(subset=['avg_yield'], inplace=True) # Drop if yield is still missing
    df.ffill(inplace=True)
    df.bfill(inplace=True)


    if df.empty:
        print("数据合并后为空，请检查数据源。脚本终止。")
        return

    # 5. 特征工程 (升级为基于市场状态的切换模型)
    print("正在进行特征工程 (区分市场状态)...")
    
    # 5.1 定义市场状态
    # 状态判断1: 需求-供给差值的趋势 (90日移动平均)
    df['gap_trend'] = df['demand_supply_gap'].rolling(90, min_periods=30).mean().diff()
    # 状态判断2: 需求-供给差值是否处于高位 (1年期滚动75%分位数)
    df['gap_high_threshold'] = df['demand_supply_gap'].rolling(365, min_periods=90).quantile(0.75)
    
    # 定义“单边下行”状态：趋势向上 或 处于高位
    df['regime_is_downward_yield'] = (df['gap_trend'] > 0) | (df['demand_supply_gap'] > df['gap_high_threshold'])

    # 5.2 准备基础特征
    df['yield_t_plus_1'] = df['avg_yield'].shift(-1)
    df['day_of_year'] = df.index.dayofyear
    df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    
    df_model = df.dropna()
    
    features = ['avg_yield', 'demand_supply_gap', 'sin_day', 'cos_day']
    
    # 6. 模型训练 (训练两个专家模型)
    df_downward_regime = df_model[df_model['regime_is_downward_yield'] == True]
    df_oscillating_regime = df_model[df_model['regime_is_downward_yield'] == False]

    if len(df_downward_regime) < 20 or len(df_oscillating_regime) < 20:
        print("警告: 某个市场状态的数据量过少，无法训练双模型。请检查数据范围或状态定义。")
        return

    print("正在为 '单边下行' 市场状态训练模型...")
    model_downward = make_pipeline(PolynomialFeatures(degree=2, include_bias=False), LinearRegression())
    model_downward.fit(df_downward_regime[features], df_downward_regime['yield_t_plus_1'])

    print("正在为 '震荡' 市场状态训练模型...")
    model_oscillating = make_pipeline(PolynomialFeatures(degree=2, include_bias=False), LinearRegression())
    model_oscillating.fit(df_oscillating_regime[features], df_oscillating_regime['yield_t_plus_1'])
    
    print("双模型训练完成。")

    # 7. 预测未来2年走势 (根据最新状态选择模型进行递推)
    print("正在进行逐日递推预测...")

    # 7.1 判断当前市场状态
    latest_regime_is_downward = df_model['regime_is_downward_yield'].iloc[-1]
    if latest_regime_is_downward:
        prediction_model = model_downward
        print("预测基于 '单边下行' 市场状态模型。")
    else:
        prediction_model = model_oscillating
        print("预测基于 '震荡' 市场状态模型。")

    # 7.2 逐日预测 (生成无约束的原始预测)
    prediction_days = 365 * 2
    future_predictions = []
    
    latest_data = df_model.iloc[-1:].copy()
    current_yield = latest_data['avg_yield'].iloc[0]
    current_gap = latest_data['demand_supply_gap'].iloc[0]
    current_date = latest_data.index[0]

    for i in range(prediction_days):
        current_date += timedelta(days=1)
        day_of_year = current_date.dayofyear
        sin_day = np.sin(2 * np.pi * day_of_year / 365.25)
        cos_day = np.cos(2 * np.pi * day_of_year / 365.25)
        current_features = np.array([[current_yield, current_gap, sin_day, cos_day]])
        
        raw_predicted_yield = prediction_model.predict(current_features)[0]
        future_predictions.append({'trade_date': current_date, 'yield': raw_predicted_yield})
        current_yield = raw_predicted_yield

    df_raw_future = pd.DataFrame(future_predictions).set_index('trade_date')

    # 7.3 应用周期振幅校准
    print("正在进行周期振幅校准...")
    
    # 计算历史振幅 (最近6个月)
    hist_series_for_amp = df_model['avg_yield'].iloc[-180:]
    historical_amplitude = hist_series_for_amp.max() - hist_series_for_amp.min()
    print(f"参考历史周期振幅 (最近6个月最高-最低): {historical_amplitude:.4f}")

    # 计算原始预测振幅
    predicted_series = df_raw_future['yield']
    predicted_amplitude = predicted_series.max() - predicted_series.min()
    print(f"原始预测曲线振幅: {predicted_amplitude:.4f}")

    df_future_pred = df_raw_future.copy()

    # 当历史和预测振幅都有效时，进行校准
    if historical_amplitude > 1e-4 and predicted_amplitude > 1e-4:
        scaling_factor = historical_amplitude / predicted_amplitude
        print(f"计算振幅校准因子: {scaling_factor:.2f}")

        # 1. 识别趋势
        x_pred = np.arange(len(predicted_series))
        trend_coeffs = np.polyfit(x_pred, predicted_series, 1) # 线性趋势
        trend_line = np.polyval(trend_coeffs, x_pred)

        # 2. 分离周期波动
        cyclical_part = predicted_series.values - trend_line

        # 3. 缩放周期波动
        scaled_cyclical_part = cyclical_part * scaling_factor

        # 4. 重新组合
        final_yield = trend_line + scaled_cyclical_part
        df_future_pred['yield'] = final_yield
        print("已根据历史振幅完成对预测曲线的校准。")
    else:
        print("历史或预测振幅过小，不进行校准，使用原始预测。")
        
    # 7.4 消除起点跳跃，确保平滑连接
    print("正在校准预测起点以确保平滑连接...")
    last_historical_yield = df_model['avg_yield'].iloc[-1]
    first_predicted_yield = df_future_pred['yield'].iloc[0]
    
    jump_correction = last_historical_yield - first_predicted_yield
    df_future_pred['yield'] += jump_correction
    print(f"起点校准完成，整体调整值: {jump_correction:.4f}")

    df_future_pred.reset_index(inplace=True)
    
    latest_date_from_df = df_model.index[-1]
    predicted_yield_2y = df_future_pred['yield'].iloc[-1]
    prediction_date = df_future_pred['trade_date'].iloc[-1]
    
    print("\n--- 预测结果 ---")
    print(f"最新数据日期: {latest_date_from_df.strftime('%Y-%m-%d')}")
    print(f"最新国债平均收益率: {df_model['avg_yield'].iloc[-1]:.4f}")
    print(f"最新需求-供给差值: {df_model['demand_supply_gap'].iloc[-1]:.2f}")
    print(f"预测 {prediction_date.strftime('%Y-%m-%d')} 的平均收益率: {predicted_yield_2y:.4f}")
    print("--------------------")

    # 8. 准备并存储结果
    print("正在准备最终结果用于存储...")
    # 使用完整的df_model准备历史数据，以包含regime信息用于绘图
    df_history = df_model.copy()
    df_history['is_prediction'] = 0
    df_history.rename(columns={'avg_yield': 'yield'}, inplace=True)

    df_future = pd.DataFrame({
        'trade_date': df_future_pred['trade_date'],
        'yield': df_future_pred['yield'],
        'demand_supply_gap': np.nan,
        'is_prediction': 1
    })
    
    # 填充未来时段的状态，用于绘图，但不存入数据库
    df_future['regime_is_downward_yield'] = latest_regime_is_downward

    df_result_for_plot = pd.concat([df_history.reset_index(), df_future])
    
    # 准备存入数据库的数据 (不含regime列)
    df_result_for_db = df_result_for_plot[['trade_date', 'yield', 'demand_supply_gap', 'is_prediction']].copy()
    df_result_for_db['trade_date'] = pd.to_datetime(df_result_for_db['trade_date']).dt.date
    
    table_name = 'bond_yield_demand_supply_forecast'
    print(f"准备将结果写入数据库表: `{table_name}`")
    try:
        df_result_for_db.to_sql(table_name, engine_bond, if_exists='replace', index=False, chunksize=1000)
        print(f"成功！已将 {len(df_result_for_db)} 行数据保存到数据表 '{table_name}' 中。")
    except Exception as e:
        print(f"\n保存数据到数据库时出错: {e}")

    # 9. 可视化 (增加状态背景标注)
    print("正在生成可视化图表...")
    fig, ax1 = plt.subplots(figsize=(16, 9))

    # 绘制状态背景
    downward_label_added = False
    oscillating_label_added = False
    for _, row in df_result_for_plot.groupby((df_result_for_plot['regime_is_downward_yield'].shift() != df_result_for_plot['regime_is_downward_yield']).cumsum()):
        start_date = row['trade_date'].iloc[0]
        end_date = row['trade_date'].iloc[-1]
        is_downward = row['regime_is_downward_yield'].iloc[0]
        if is_downward:
            label = '单边下行期 (需求强/升)' if not downward_label_added else None
            downward_label_added = True
            ax1.axvspan(start_date, end_date, color='lightcoral', alpha=0.3, label=label)
        else:
            label = '震荡期 (需求弱/降)' if not oscillating_label_added else None
            oscillating_label_added = True
            ax1.axvspan(start_date, end_date, color='lightcyan', alpha=0.3, label=label)

    hist_data = df_result_for_plot[df_result_for_plot['is_prediction']==0]
    pred_data = df_result_for_plot[df_result_for_plot['is_prediction']==1]
    
    last_hist_date = hist_data['trade_date'].iloc[-1]
    last_hist_yield = hist_data['yield'].iloc[-1]
    first_pred_date = pred_data['trade_date'].iloc[0]
    first_pred_yield = pred_data['yield'].iloc[0]
    
    ax1.plot(hist_data['trade_date'], hist_data['yield'], label='历史平均收益率', color='blue')
    ax1.plot(
        [last_hist_date, first_pred_date], 
        [last_hist_yield, first_pred_yield], 
        color='red', linestyle='--'
    )
    ax1.plot(pred_data['trade_date'], pred_data['yield'], label='预测平均收益率 (2年)', color='red', linestyle='--')
    
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('国债平均收益率', color='blue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2 = ax1.twinx()
    ax2.plot(hist_data['trade_date'], hist_data['demand_supply_gap'], label='债市需求-供给差值 (万亿)', color='purple', alpha=0.6)
    ax2.set_ylabel('需求-供给差值 (万亿)', color='purple', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='purple')

    plt.title('国债平均收益率走势预测 (基于市场状态切换模型)', fontsize=18, pad=20)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    
    # Manually add patches for axvspan to legend
    import matplotlib.patches as mpatches
    legend_patches = [
        mpatches.Patch(color='lightcoral', alpha=0.3, label='单边下行期 (需求强/升)'),
        mpatches.Patch(color='lightcyan', alpha=0.3, label='震荡期 (需求弱/降)')
    ]

    ax1.legend(handles=lines + lines2 + legend_patches, loc='upper left')

    plt.tight_layout()
    plt.savefig('/data/项目/快速处理/2025/利率预测/子模型3-基于资金供需 - 中长期/yield_demand_supply_forecast.png')
    print("图表已保存为 `yield_demand_supply_forecast.png`")
    plt.show()


if __name__ == '__main__':
    main()
    print("--- 脚本执行完毕 ---") 