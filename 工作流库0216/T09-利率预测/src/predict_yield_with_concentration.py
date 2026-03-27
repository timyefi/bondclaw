import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import GradientBoostingRegressor
from datetime import datetime
from dateutil.relativedelta import relativedelta
import warnings

warnings.filterwarnings('ignore')

# # -- 全局配置matplotlib以支持中文 --
# import matplotlib
# # 指定中文字体，'WenQuanYi Micro Hei' 是一款常用的高质量开源中文字体
# matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
# # 解决负号'-'显示为方块的问题
# matplotlib.rcParams['axes.unicode_minus'] = False


def main():
    """
    主函数，用于执行数据获取、模型训练、预测和存储的全过程。
    """
    print("--- 脚本开始执行 ---")
    # 1. 数据库连接
    db_config = {
        'user': 'hz_work',
        'password': 'Hzinsights2015',
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': '3306',
        'db': 'bond',
    }
    print("正在创建数据库连接引擎...")
    try:
        engine = create_engine(
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
        )
        print("数据库连接引擎创建成功。")
    except Exception as e:
        print(f"创建数据库连接引擎时出错: {e}")
        return

    # 2. 数据获取
    sql_concentration = """
    SELECT `dt`, `concentration_90pct`
    FROM bond.market_concentration_90pct
    ORDER BY `dt`
    """
    print("正在获取行情集中度数据...")
    try:
        df_concentration = pd.read_sql(sql_concentration, engine)
        df_concentration.rename(columns={'concentration_90pct': 'concentration'}, inplace=True)
    except Exception as e:
        print(f"获取行情集中度数据时出错: {e}")
        print("请检查 `bond.market_concentration_90pct` 表中是否存在 `dt` 和 `concentration_90pct` 列。")
        return

    sql_yield = """
    SELECT `dt`, `close` AS `yield`
    FROM bond.marketinfo_curve
    WHERE trade_code = 'L001619604'
    ORDER BY `dt`
    """
    print("正在获取10年国债收益率数据...")
    df_yield = pd.read_sql(sql_yield, engine)

    # 3. 数据整合与特征工程
    print("正在整合数据...")
    df_concentration['dt'] = pd.to_datetime(df_concentration['dt'])
    df_yield['dt'] = pd.to_datetime(df_yield['dt'])
    df = pd.merge(df_yield, df_concentration, on='dt', how='inner')
    
    if df.empty:
        print("数据合并后为空，请检查两个数据源的日期是否存在重叠。")
        return
        
    df.dropna(subset=['yield', 'concentration'], inplace=True)
    df.set_index('dt', inplace=True)
    df.sort_index(inplace=True)

    print("正在进行特征工程以捕捉拐点...")
    df['concentration_rol_avg_21d'] = df['concentration'].rolling(window=21).mean()
    df['concentration_chg_5d'] = df['concentration'].diff(5)
    df['concentration_detrend'] = df['concentration'] - df['concentration_rol_avg_21d']

    # 计算未来3个月的收益率变化作为目标变量
    prediction_days = 63 # 恢复为3个月
    df['yield_change'] = df['yield'].shift(-prediction_days) - df['yield']
    
    # 准备建模数据
    df_model = df.dropna()
    features = ['concentration', 'concentration_rol_avg_21d', 'concentration_chg_5d', 'concentration_detrend']
    X = df_model[features]
    y = df_model['yield_change']

    # 4. 模型训练 (使用GradientBoostingRegressor)
    print("正在训练 Gradient Boosting Regressor 模型...")
    model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    model.fit(X, y)
    
    print(f"\n--- 模型分析 ---")
    print("模型: Gradient Boosting Regressor")
    print("特征重要性:")
    for feature, importance in zip(features, model.feature_importances_):
        print(f"  - {feature}: {importance:.4f}")
    print(f"模型R-squared (决定系数): {model.score(X, y):.4f}")
    print("--------------------")

    # 5. 预测未来
    print("正在进行预测...")
    latest_data = df.iloc[-1:]
    if latest_data.empty or latest_data[features].isnull().values.any():
        print("无法获取最新的有效数据进行预测，部分特征可能为空。")
        return
        
    latest_features = latest_data[features]
    predicted_change = model.predict(latest_features)[0]
    
    latest_yield = latest_data['yield'].iloc[0]
    predicted_yield_3m = latest_yield + predicted_change

    latest_date = latest_data.index[0]
    prediction_date = latest_date + relativedelta(months=3)

    print("\n--- 预测结果 ---")
    print(f"最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
    print(f"最新10年国债收益率: {latest_yield:.4f}")
    print(f"最新行情集中度: {latest_data['concentration'].iloc[0]:.4f}")
    print(f"预测未来3个月收益率变化: {predicted_change:.4f} (基点)")
    print(f"预测 {prediction_date.strftime('%Y-%m-%d')} 的10年国债收益率: {predicted_yield_3m:.4f}")
    print("--------------------")

    # 6. 准备并存储结果
    print("正在准备最终结果用于存储...")
    # 在历史数据上生成预测 (仅在有完整特征的行上)
    df['predicted_yield_change'] = np.nan
    df.loc[X.index, 'predicted_yield_change'] = model.predict(X)
    
    print("正在生成未来3个月的每日预测路径...")
    future_dates = pd.date_range(start=latest_date + pd.Timedelta(days=1), end=prediction_date, freq='D')
    
    num_future_days = len(future_dates)
    interpolated_yield_path = np.linspace(start=latest_yield, stop=predicted_yield_3m, num=num_future_days + 1)
    future_yields = interpolated_yield_path[1:]

    prediction_df = pd.DataFrame({
        'dt': future_dates,
        'yield': future_yields,
        'concentration': np.nan,
        'concentration_rol_avg_21d': np.nan,
        'concentration_chg_5d': np.nan,
        'concentration_detrend': np.nan,
        'yield_change': np.nan,
        'predicted_yield_change': predicted_change
    })
    print(f"已生成 {len(prediction_df)} 条未来每日预测数据。")

    # 合并历史数据与预测数据
    df_result = pd.concat([df.reset_index(), prediction_df])
    df_result['dt'] = pd.to_datetime(df_result['dt']).dt.date
    
    df_result.rename(columns={
        'dt': 'trade_date',
        'yield': 'yield_10y',
        'concentration': 'market_concentration_pct',
        'concentration_rol_avg_21d': 'concentration_rol_avg_21d',
        'concentration_chg_5d': 'concentration_chg_5d',
        'concentration_detrend': 'concentration_detrend',
        'yield_change': 'actual_yield_change_3m',
        'predicted_yield_change': 'predicted_yield_change_3m'
    }, inplace=True)
    
    table_name = 'analysis_yield_concentration_pred'
    print(f"准备将结果写入数据库表: `{table_name}`")
    try:
        # 选择要存储的列以匹配潜在的现有表结构或定义新结构
        columns_to_store = [
            'trade_date', 'yield_10y', 'market_concentration_pct', 
            'concentration_rol_avg_21d', 'concentration_chg_5d', 'concentration_detrend',
            'actual_yield_change_3m', 'predicted_yield_change_3m'
        ]
        df_to_store = df_result[columns_to_store]
        df_to_store.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=1000)
        print(f"\n成功！已将 {len(df_to_store)} 行数据保存到数据表 '{table_name}' 中。")
    except Exception as e:
        print(f"\n保存数据到数据库时出错: {e}")

if __name__ == '__main__':
    print("--- 脚本入口 ---")
    main()
    print("--- 脚本执行完毕 ---") 