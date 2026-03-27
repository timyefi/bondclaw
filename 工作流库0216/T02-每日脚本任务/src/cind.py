import psycopg2
import logging
import pandas as pd
import sqlalchemy
import numpy as np
import pandas as pd
import time
from sqlalchemy.sql import text
from iFinDPy import *
from time import sleep
from sqlalchemy import inspect, MetaData, Table, Column, Text, text
from sklearn.linear_model import LinearRegression

 # 连接源数据库
sql_engine_bond = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor_bond = sql_engine_bond.connect()
sql_engine_yq = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor_yq = sql_engine_yq.connect()

sql_engine_tsdb = psycopg2.connect(
        host="139.224.107.113",
        port=18032,
        user="postgres",
        password="hzinsights2015",
        database="tsdb"
    )
# 创建游标
_cursor_tsdb = sql_engine_tsdb.cursor()

_cursor_pg='postgresql://postgres:hzinsights2015@139.224.107.113:18032/tsdb'
def trans_sql_bond(sql1):
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    global sql_engine_bond
    global _cursor_bond
    while retry_count < max_retries:
        try:
            # 开始事务
            trans_bond = _cursor_bond.begin()
            try:
                _cursor_bond.execute(text(sql1))
                # 提交事务
                trans_bond.commit()
                
            except Exception as e:
                # 如果出错，回滚事务
                trans_bond.rollback()
                raise e

            break  # 如果成功，则退出循环

        except Exception as e:
            print(f"Error: {e}")
            retry_count += 1
            sql_engine_bond = sqlalchemy.create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s' % (
                'hz_work',
                'Hzinsights2015',
                'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                '3306',
                'bond',
            ), poolclass=sqlalchemy.pool.NullPool
            )
            _cursor_bond = sql_engine_bond.connect()
            sleep(1)  # 休眠一秒后重试

def trans_sql_yq(sql1):
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    global sql_engine_yq
    global _cursor_yq
    while retry_count < max_retries:
        try:
            # 开始事务
            trans_yq = _cursor_yq.begin()
            try:
                # 执行UPDATE语句
                _cursor_yq.execute(text(sql1))
                # 提交事务
                trans_yq.commit()
            except Exception as e:
                # 如果出错，回滚事务
                trans_yq.rollback()
                raise e

            break  # 如果成功，则退出循环

        except Exception as e:
            print(f"Error: {e}")
            retry_count += 1
            sql_engine_yq = sqlalchemy.create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s' % (
                'hz_work',
                'Hzinsights2015',
                'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                '3306',
                'yq',
            ), poolclass=sqlalchemy.pool.NullPool
            )
            _cursor_yq = sql_engine_yq.connect()
            sleep(1)  # 休眠一秒后重试

def trans_sql_tsdb(sql1):
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    global sql_engine_tsdb
    global _cursor_tsdb
    # 连接数据库
    while retry_count < max_retries:
        try:
            # 开始事务
            sql_engine_tsdb.autocommit = False  # 禁用自动提交
            _cursor_tsdb.execute(sql1)
            # 提交事务
            sql_engine_tsdb.commit()
            break  # 如果成功，则退出循环

        except Exception as e:
            print(f"Error: {e}")
            retry_count += 1
            sql_engine_tsdb = psycopg2.connect(
                host="139.224.107.113",
                port=18032,
                user="postgres",
                password="hzinsights2015",
                database="tsdb"
            )
            # 创建游标
            _cursor_tsdb = sql_engine_tsdb.cursor()
            sleep(1)  # 休眠一秒后重试
    else:
        print("Max retries reached. Operation failed.")

THS_iFinDLogin('nylc082','491448')
# THS_iFinDLogin('hznd002', '160401')
# THS_iFinDLogin('hzqh172','6769be')
def pro_data(wsd_data,database_name,table_name):
    sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        database_name,
    ), poolclass=sqlalchemy.pool.NullPool
    )   

    inspector = inspect(sql_engine)
    table_exists = inspector.has_table(table_name)
    if table_exists:
        # 获取现有表的列名
        existing_columns = inspector.get_columns(table_name)
        existing_columns_names = [col['name'] for col in existing_columns]
        # 获取df_news的列名
        wsd_data_columns = wsd_data.columns.tolist()

        # 检查并添加缺失的列
        for col in wsd_data_columns:
            if col not in existing_columns_names:
                with sql_engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col} Float;"))

            # 构建INSERT INTO ... ON DUPLICATE KEY UPDATE语句
        columns = wsd_data_columns
        insert_columns = ', '.join(columns)
        update_columns = ', '.join([f"{col} = VALUES({col})" for col in columns])

        insert_query = text(f"""
        INSERT INTO {table_name} ({insert_columns})
        VALUES ({', '.join([f':{col}' for col in columns])})
        ON DUPLICATE KEY UPDATE {update_columns};
        """)
            # 打印调试信息
        print("Generated SQL Query:")
        print(insert_query)
        print("Sample Data Row:")
        print(wsd_data.iloc[0].to_dict())
        # 插入或更新数据
        # 插入或更新数据
        with sql_engine.begin() as connection:
            for _, row in wsd_data.iterrows():
                try:
                    connection.execute(insert_query,  row.to_dict())
                except Exception as e:
                    print(f"Error inserting row: {row}")
                    print(e)
        print('更新完成')
with sql_engine_yq.begin() as connection:
    dates=pd.read_sql("SELECT dt FROM xyfxzs where (城投+产业+全部+金融+ABS) is not NULL", connection)

dates['dt'] = pd.to_datetime(dates['dt'])
dates = dates['dt'].dt.strftime('%Y-%m-%d').tolist()
dates = "','".join(x for x in dates)

target_term='2'
if target_term=='0.5':
    classify3='中债国债到期收益率:6月'
else:
    classify3='中债国债到期收益率:'+str(target_term)+'年'

if dates=='':
    trade_dates = pd.read_sql(f"""SELECT Distinct dt AS "DT" FROM hzcurve_credit
                        WHERE target_term=2""", _cursor_pg)
else:
    trade_dates = pd.read_sql(f"""SELECT Distinct dt AS "DT" FROM hzcurve_credit
                        WHERE target_term=2 and dt not in ('{dates}')""", _cursor_pg)   
trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])
trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
unique_dates = "','".join(x for x in trade_dates)

query=f"""
SELECT 
    A.dt,
    B.大类,
    sum(A.balance) as 余额,
    CASE WHEN sum(A.balance)>0 THEN sum(A.balance*A.stdyield) / sum(A.balance)
        ELSE NULL END AS 收益率
FROM 
    hzcurve_credit A
    LEFT JOIN (SELECT * FROM tc最新所属曲线 WHERE 日期 = (SELECT MAX(日期) FROM tc最新所属曲线)) C
    ON A.trade_code=C.trade_code
    LEFT JOIN 曲线代码 B
    ON C.代码=B.代码
WHERE 
    A.dt IN ('{unique_dates}')
    AND A.target_term='{target_term}'
    AND B.大类 is not NULL
    GROUP BY A.dt,B.大类
    ORDER BY A.dt;
"""
if unique_dates != '':
    result = pd.read_sql(query, _cursor_pg)
    result.dropna(how='all',inplace=True)
    cols=result['大类'].drop_duplicates().tolist()
    result1=result[['dt', '大类','收益率']]
    result1=result1.set_index(['dt', '大类'])['收益率'].unstack()
    result1=result1[cols].reset_index()
    result['收益率*余额']=result['收益率']*result['余额']
    grouped = result.groupby(['dt'])
    result_df = grouped.agg({'余额': 'sum', '收益率*余额': 'sum'}).reset_index()
    result1['全部']=result_df['收益率*余额']/result_df['余额']
    result1.bfill(inplace=True)
    result1.ffill(inplace=True)
    cols=result1.columns[1:].tolist()

    result1['dt'] = pd.to_datetime(result1['dt'])
    result1['dt'] = result1['dt'].dt.strftime('%Y-%m-%d')

    base_data=pd.read_sql(f"""SELECT dt, trade_code, close AS BASE_CLOSE
                    FROM `bond`.`marketinfo_curve` 
                    WHERE DT IN ('{unique_dates}')
                    AND trade_code IN (SELECT trade_code FROM `bond`.`basicinfo_curve` WHERE `sec_name` = '{classify3}') order by dt """,_cursor_bond)
    base_data['dt'] = pd.to_datetime(base_data['dt'])
    base_data['dt'] = base_data['dt'].dt.strftime('%Y-%m-%d')

    result1=result1.merge(base_data[['dt','BASE_CLOSE']],on=['dt'],how='inner')

    for i in range(1, len(result1.iloc[:,:-1].columns)):    
        result1[f'{result1.columns[i]}'] = round((result1[f'{result1.columns[i]}']-result1['BASE_CLOSE'])*100,2)
    result1=result1.iloc[:,:-1]

    column_diffs = result1.iloc[-1,1:] - result1.iloc[0,1:]
    sorted_columns = column_diffs.sort_values().index.tolist()
    cols=result1.columns[1:].tolist()
    cols = sorted(cols, key=lambda x: sorted_columns.index(x))
    cols=['dt']+cols
    result1=result1[cols]
    cols=result1.columns[1:].tolist()
    pro_data(result1,'yq','xyfxzs')

# query = """
# SELECT dt, CLOSE as zj
# FROM marketinfo_curve
# WHERE trade_code = 'L001619493'
# order by dt
# """
# df = pd.read_sql_query(query, _cursor_bond)
# df['zj'] = df['zj'].rolling(20).mean()
# df.to_sql('xyfxzs_temp_zj', con=_cursor_yq, if_exists='replace', index=False)
# query = """
# UPDATE xyfxzs
# INNER JOIN xyfxzs_temp_zj ON xyfxzs.dt = xyfxzs_temp_zj.dt
# SET xyfxzs.zj = xyfxzs_temp_zj.zj;
# """
# trans_sql_yq(query)


# # 补充其他数据
# ed=pd.read_sql("SELECT max(tradedate) as dt FROM bondpriceabnormalchanges", _cursor_yq)
# ed=ed['dt'][0]
# update_date = pd.read_sql(f"SELECT distinct dt FROM hzcurve_credit where dt>'{ed}'", _cursor_pg)
# # update_date = pd.read_sql(f"SELECT distinct dt FROM xyfxzs where jyqx is NULL", _cursor_l)
# update_date['dt'] = pd.to_datetime(update_date['dt'])
# update_date = update_date['dt'].dt.strftime('%Y%m%d').tolist()
# for dt in update_date:
#     df=THS_DR('p03091',f'edate={dt};plbl=;jysc=全部;ytm=20','jydm:Y,jydm_mc:Y,p03091_f001:Y,p03091_f012:Y,p03091_f013:Y','format:dataframe')    
#     df=df.data
#     if df is None:
#         continue
#     df.columns = ['windcode', 'shortname', 'tradedate', 'dealchangeratioclean', 'bpchangeytm']
#     df['tradedate'] = pd.to_datetime(df['tradedate']).dt.date
#     # 去掉windcode为None的行
#     df = df.loc[df['windcode'].notna()]
#     # 将bpchangeytm列转换为数字，然后去掉bpchangeytm<0的行
#     df['dealchangeratioclean'] = pd.to_numeric(df['dealchangeratioclean'], errors='coerce')
#     df = df.loc[df['dealchangeratioclean'] <= 0]
#     # 去掉shortname中含'转债'的行
#     df = df.loc[~df['shortname'].str.contains('转债')]
#     df.to_sql('bondpriceabnormalchanges', con=_cursor_yq, if_exists='append', index=False)
# _cursor_yq.commit()


# # 执行查询
# query =f"""
# UPDATE xyfxzs 
# JOIN (
#     SELECT tradedate as dt, count(windcode) as jyqx
#     FROM bondpriceabnormalchanges A
#     JOIN bond.basicinfo_credit B
#     ON A.windcode=B.trade_code
#     GROUP BY tradedate
# ) AS temp 
# ON xyfxzs.dt = temp.dt 
# SET xyfxzs.jyqx = temp.jyqx;
# """
# trans_sql_yq(query)
# #！记得回来修改dmzc
# df11 = pd.read_sql('SELECT * FROM xyfxzs', _cursor_yq)
# # df11['dmzc'] = df11['dmzc'].fillna(method='ffill')
# pro_data(df11,'yq','xyfxzs')

# from sklearn.neural_network import MLPRegressor
# from sklearn.preprocessing import StandardScaler

# # 执行SQL查询
# query = "SELECT dt, 城投, 产业, 全部, 金融, ABS FROM xyfxzs WHERE dt >= '2020-01-01'"
# df = pd.read_sql_query(query, _cursor_yq)
# df = df.interpolate()
# from sklearn.preprocessing import MinMaxScaler
# import matplotlib.pyplot as plt

# # 选择要显示的变量
# variables_to_plot = ['dmzc', 'jyqx', 'zj']  # 你可以修改这个列表来选择要显示的变量

# # 创建一个归一化器
# scaler = MinMaxScaler()

# # 对选择的变量进行归一化
# df_normalized = pd.DataFrame(scaler.fit_transform(df[variables_to_plot]), columns=variables_to_plot)*100
# df[['dmzc', 'jyqx', 'zj']] = df_normalized
# df['dmzc']=100-df['dmzc']
# df['dt'] = pd.to_datetime(df['dt'])
# df.set_index('dt', inplace=True)
# df = df.resample('D').interpolate(method='linear')
# df = df.reset_index()

# import pandas as pd
# from statsmodels.tsa.vector_ar.var_model import VAR
# from sklearn.metrics import mean_squared_error

# # 计算每个变量的一阶差分，以获取变化的方向
# # df_diff = df[['dmzc', 'jyqx', 'zj', '全部']].diff().dropna()

# df1=df[['dmzc', 'jyqx', 'zj', '全部', '城投', '产业', '金融', 'ABS']].dropna()
# rolling_n=30
# # 添加滚动平均特征
# df_rolling = pd.DataFrame()
# for col in ['dmzc', 'jyqx', 'zj', '全部', '城投', '产业', '金融', 'ABS']:
#     for window in [rolling_n]:
#         df_rolling[f'{col}_mean_{window}'] = df1[col].rolling(window).mean()

# # 删除有空值的行
# df_rolling = df_rolling.dropna()
# df_rolling['dt']=df['dt']
# df_rolling['全部']=df['全部']
# df_rolling['城投']=df['城投']
# df_rolling['产业']=df['产业']
# df_rolling['金融']=df['金融']
# df_rolling['ABS']=df['ABS']

# import pandas as pd
# from scipy.optimize import minimize
# import statsmodels.api as sm
# import numpy as np

# # 定义损失函数
# def loss(params, X, y):
#     predictions = X @ params
#     return np.sum((y - predictions) ** 2)

# # 初始化参数
# params_initial = np.array([ 0.1, 0.1, 0.1])

# # 设置参数约束
# bounds = [(0, None), (0, None), (0, None)]

# # 滚动窗口大小
# window = 180

# # 需要进行回归的列
# target_cols = ['全部', '城投', '产业', '金融', 'ABS']

# # 对每一个目标列进行回归
# for target_col in target_cols:
#     # 保存预测指数和系数
#     df_rolling[f'{target_col}_y1'] = np.nan
#     df_rolling[f'{target_col}_a1'] = np.nan
#     df_rolling[f'{target_col}_a2'] = np.nan
#     df_rolling[f'{target_col}_a3'] = np.nan

#     # 遍历数据集，对每一天使用过去180天的数据进行回归
#     for i in range(window, len(df_rolling) - 30):  # 保证有30天的数据可以用于预测
#         # 获取滚动窗口的数据
#         X = df_rolling[['dmzc_mean_30', 'jyqx_mean_30', 'zj_mean_30']].iloc[i-window:i]

#         # 获取目标变量，这里我们需要使用30天后的数据
#         y = df_rolling[f'{target_col}_mean_30'].shift(-30).iloc[i-window:i]

#         # 删除NaN值
#         valid_indices = y[~y.isna()].index
#         X = X.loc[valid_indices]
#         y = y.loc[valid_indices]

#         # # 添加常数项
#         # X.insert(0, 'const', 1.0)

#         # 使用minimize函数进行优化
#         result = minimize(loss, params_initial, args=(X, y), bounds=bounds)

#         # 获取系数
#         a1, a2, a3 = result.x # 注意这里我们只取后三个元素，因为第一个元素是常数项

#         # 保存预测指数和系数
#         # df_rolling.at[df_rolling.index[i], f'{target_col}_c0'] = c0
#         df_rolling.at[df_rolling.index[i], f'{target_col}_a1'] = a1
#         df_rolling.at[df_rolling.index[i], f'{target_col}_a2'] = a2
#         df_rolling.at[df_rolling.index[i], f'{target_col}_a3'] = a3

#     df_rolling.bfill(inplace=True)
#     df_rolling.ffill(inplace=True)

#     # df_rolling[f'{target_col}_c0'] = df_rolling[f'{target_col}_c0'].rolling(rolling_n).mean()

#     # 计算预测指数
#     df_rolling[f'{target_col}_y1'] = df_rolling['dmzc_mean_30'] * df_rolling[f'{target_col}_a1'] + df_rolling['jyqx_mean_30'] * df_rolling[f'{target_col}_a2'] + df_rolling['zj_mean_30'] * df_rolling[f'{target_col}_a3'] 

#     # 计算各列的占比
#     # df_rolling[f'{target_col}_a1'] = df_rolling[f'{target_col}_a1'] * df_rolling['dmzc_mean_30'] 
#     # df_rolling[f'{target_col}_a2'] = df_rolling[f'{target_col}_a2'] * df_rolling['jyqx_mean_30'] 
#     # df_rolling[f'{target_col}_a3'] = df_rolling[f'{target_col}_a3'] * df_rolling['zj_mean_30'] 
#     total = df_rolling[f'{target_col}_a1'] + df_rolling[f'{target_col}_a2'] + df_rolling[f'{target_col}_a3']
#     df_rolling[f'{target_col}_a1'] = df_rolling[f'{target_col}_a1'] / total
#     df_rolling[f'{target_col}_a2'] = df_rolling[f'{target_col}_a2'] / total
#     df_rolling[f'{target_col}_a3'] = df_rolling[f'{target_col}_a3'] / total

# df_rolling.to_sql('xyfxzs_model', con=_cursor_yq, if_exists='replace', index=False)
# _cursor_yq.commit()
# _cursor_bond.close()
# _cursor_yq.close()
# _cursor_tsdb.close()
# sql_engine_bond.dispose()
# sql_engine_yq.dispose()
# sql_engine_tsdb.close()