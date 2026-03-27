import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import lightgbm as lgb  # 引入LightGBM
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


def get_congestion_data(engine, start_date, end_date):
    """
    获取和计算债券市场的交易拥挤度（活跃券成交占比）。
    """
    print(f"正在获取从 {start_date} 到 {end_date} 的交易拥挤度数据...")
    sql = f"""
    SELECT
        DT as trade_date,
        TRADE_CODE as bond_code,
        sum(transaction_amount) / 10000 as turnover
    FROM bond.dealtinfo
    WHERE SEC_NAME LIKE '%%国债%%'
      AND DT BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY trade_date, bond_code
    """
    df = pd.read_sql(sql, engine)
    if df.empty:
        print("警告：在指定日期范围内未找到国债成交数据。")
        return pd.DataFrame(columns=['trade_date', 'congestion_rate'])

    df['trade_date'] = pd.to_datetime(df['trade_date'])
    
    # 1. 计算每日每只债券的成交金额排名和占比
    df['daily_rank'] = df.groupby('trade_date')['turnover'].rank(ascending=False)
    
    # 2. 识别活跃券
    df['is_active'] = (
        (df['daily_rank'] <= 4) &
        (df['turnover'] > df.groupby('trade_date')['turnover'].transform('mean') * 3)
    )

    # 3. 计算每日活跃券和非活跃券的成交总额
    daily_stats = df.groupby(['trade_date', 'is_active'])['turnover'].sum().unstack(fill_value=0)
    if True not in daily_stats.columns:
        daily_stats[True] = 0
    if False not in daily_stats.columns:
        daily_stats[False] = 0

    daily_stats.columns = ['inactive_turnover', 'active_turnover']

    # 4. 计算活跃券成交占比
    total_turnover = daily_stats['active_turnover'] + daily_stats['inactive_turnover']
    # 避免除以零的情况
    daily_stats['congestion_rate'] = np.where(total_turnover > 0, daily_stats['active_turnover'] / total_turnover, 0)

    # 关键步骤：与 1.md 保持一致，使用20日移动平均值作为最终的拥挤度指标
    # rolling需要有序的索引
    daily_stats.sort_index(inplace=True)
    daily_stats['congestion_rate'] = daily_stats['congestion_rate'].rolling(20, min_periods=1).mean().round(4)
    
    print("交易拥挤度数据计算完成。")
    return daily_stats.reset_index()[['trade_date', 'congestion_rate']]


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
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    # 使用后向填充处理周末或节假日导致的缺失值
    df = df.asfreq('D').bfill()
    print("国债平均收益率数据获取完成。")
    return df.reset_index()


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
    print("正在创建数据库连接引擎...")
    try:
        engine = create_engine(
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
        )
        print("数据库连接引擎创建成功。")
    except Exception as e:
        print(f"创建数据库连接引擎时出错: {e}")
        return

    # 2. 定义数据时间范围（使用最近5年数据进行训练）
    end_date = datetime.now()
    start_date = end_date - relativedelta(years=5)

    # 3. 获取数据
    df_congestion = get_congestion_data(engine, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    df_yield = get_yield_data(engine, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    # 4. 数据整合与预处理
    print("正在整合收益率和拥挤度数据...")
    df = pd.merge(df_yield, df_congestion, on='trade_date', how='inner')
    df.dropna(subset=['avg_yield', 'congestion_rate'], inplace=True)
    df.set_index('trade_date', inplace=True)
    df.sort_index(inplace=True)

    if df.empty:
        print("数据合并后为空，请检查数据源。脚本终止。")
        return

    # 5. 特征工程 (增强版)
    print("正在进行增强版特征工程...")
    # a. 拥挤度动量：捕捉“快速回落”
    df['congestion_momentum'] = df['congestion_rate'].diff(5)
    
    # b. 收益率波动率：量化“震荡”状态
    df['yield_volatility_20d'] = df['avg_yield'].rolling(20).std()

    # c. 目标变量：未来1个月（约30个自然日）的收益率变化
    prediction_days = 30
    df['yield_change'] = df['avg_yield'].shift(-prediction_days) - df['avg_yield']
    
    # 准备建模数据，移除因计算导致NaN的早期行
    df_model = df.dropna()
    
    # 使用增强后的特征集
    features = ['avg_yield', 'congestion_rate', 'congestion_momentum', 'yield_volatility_20d']
    X = df_model[features]
    y = df_model['yield_change']

    # 6. 模型训练 (升级为LightGBM)
    print("正在训练LightGBM模型...")
    model = lgb.LGBMRegressor(random_state=42)
    model.fit(X, y)
    print("模型训练完成。")

    # 7. 预测未来1个月走势
    print("正在进行预测...")
    # 关键修正：使用 df 的最后一行（最新数据）进行预测，而不是 df_model（训练数据）的最后一行。
    # df_model 为了训练，去除了没有未来收益率（yield_change）的近期数据，因此是历史数据。
    latest_data = df.iloc[-1:]
    latest_features = latest_data[features]
    
    predicted_change = model.predict(latest_features)[0]
    latest_yield = latest_data['avg_yield'].iloc[0]
    predicted_yield_1m = latest_yield + predicted_change
    
    latest_date = latest_data.index[0]
    prediction_date = latest_date + relativedelta(months=1)

    print("\n--- 预测结果 ---")
    print(f"最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
    print(f"最新国债平均收益率: {latest_yield:.4f}")
    print(f"最新拥挤度 (20日均线): {latest_data['congestion_rate'].iloc[0]:.4f}")
    print(f"最新拥挤度动量 (5日): {latest_data['congestion_momentum'].iloc[0]:.4f}")
    print(f"最新收益率波动率 (20日): {latest_data['yield_volatility_20d'].iloc[0]:.4f}")
    print(f"模型预测未来1个月收益率变化: {predicted_change:.4f}")
    print(f"预测 {prediction_date.strftime('%Y-%m-%d')} 的平均收益率: {predicted_yield_1m:.4f}")
    print("--------------------")

    # 8. 准备并存储结果
    print("正在准备最终结果用于存储...")
    # 创建包含历史数据的DataFrame
    df_history = df[['avg_yield', 'congestion_rate']].copy()
    df_history['is_prediction'] = 0

    # 创建包含未来预测路径的DataFrame
    future_dates = pd.to_datetime(pd.date_range(start=latest_date + timedelta(days=1), periods=30, freq='D'))
    future_yields = np.linspace(latest_yield, predicted_yield_1m, 31)[1:]

    df_future = pd.DataFrame({
        'trade_date': future_dates,
        'avg_yield': future_yields,
        'congestion_rate': np.nan,  # 未来拥挤度未知
        'is_prediction': 1
    }).set_index('trade_date')
    
    # 合并历史与未来
    df_result = pd.concat([df_history, df_future]).reset_index()
    df_result.rename(columns={'index': 'trade_date'}, inplace=True)
    df_result['trade_date'] = pd.to_datetime(df_result['trade_date']).dt.date
    
    # 存储到数据库
    table_name = 'bond_yield_congestion_forecast'
    print(f"准备将结果写入数据库表: `{table_name}`")
    try:
        df_result.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=1000)
        print(f"成功！已将 {len(df_result)} 行数据保存到数据表 '{table_name}' 中。")
    except Exception as e:
        print(f"\n保存数据到数据库时出错: {e}")

    # 9. 可视化
    print("正在生成可视化图表...")
    fig, ax1 = plt.subplots(figsize=(16, 8))

    # 绘制历史和预测收益率
    ax1.plot(df_result[df_result['is_prediction']==0]['trade_date'], df_result[df_result['is_prediction']==0]['avg_yield'], label='历史平均收益率', color='blue')
    ax1.plot(df_result[df_result['is_prediction']==1]['trade_date'], df_result[df_result['is_prediction']==1]['avg_yield'], label='预测平均收益率 (1个月)', color='red', linestyle='--')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('国债平均收益率', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    # 创建第二个y轴绘制拥挤度
    ax2 = ax1.twinx()
    ax2.plot(df_result[df_result['is_prediction']==0]['trade_date'], df_result[df_result['is_prediction']==0]['congestion_rate'], label='交易拥挤度 (20日移动平均)', color='green', alpha=0.6)
    ax2.set_ylabel('交易拥挤度', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    plt.title('国债平均收益率历史与未来1个月走势预测\n(基于LightGBM模型和增强特征)', fontsize=16)
    fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    plt.savefig('/data/项目/快速处理/2025/利率预测/子模型2-基于交易拥挤度-超短期/yield_congestion_forecast.png')
    print("图表已保存为 `yield_congestion_forecast.png`")
    plt.show()


if __name__ == '__main__':
    main()
    print("--- 脚本执行完毕 ---") 