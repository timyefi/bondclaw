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
from sklearn.linear_model import LinearRegression
from datetime import datetime

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

# 补充其他数据
date_list = pd.read_sql("""select distinct dt from bond.marketinfo_curve where dt not in (select distinct dt from yq.债券市场规模期限) and dt>='2024-01-01'
                      """, _cursor_bond)
# date_list = pd.read_sql("""select distinct dt from bond.marketinfo_curve where dt in ('2024-10-17','2024-10-24','2024-11-04')
#                       """, _cursor_bond)
date_list['dt']=pd.to_datetime(date_list['dt'])
dates = date_list['dt'].tolist()
formatted_dates = [date.strftime('%Y%m%d') for date in dates]
def pro_df(df,name):
    df=df.data
    df.columns = ['期限', '余额']
    # 将字符串解析为日期对象
    dt_obj = datetime.strptime(dt, '%Y%m%d')
    # 然后将日期对象格式化为 'YYYY-MM-DD'
    dt_formatted = dt_obj.strftime('%Y-%m-%d')
    df['dt'] = dt_formatted
    print(dt_formatted)  # 输出类似 '2023-04-01'
    # 去掉windcode为None的行
    df['类型']=name
    # 将bpchangeytm列转换为数字，然后去掉bpchangeytm<0的行
    # df['dealchangeratioclean'] = pd.to_numeric(df['dealchangeratioclean'], errors='coerce')
    # df = df.loc[df['dealchangeratioclean'] <= 0]
    # 去掉shortname中含'转债'的行
    # df = df.loc[~df['shortname'].str.contains('转债')]
    try:
        df.to_sql('债券市场规模期限', con=_cursor_yq, if_exists='append', index=False)
    except Exception as e:
        print(e)
    print(dt)

for dt in formatted_dates:
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640001,640001001,640001002,640001003,640001004;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'国债')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640002,640002001,640002002,640002003,640002004;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'地方债')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640004001,640004001001,640004001002,640004001003;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'政金债')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640004002002,640004002003,640004002004,640004002005,640004003002;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'二永')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640004002001,640004003001,640004003003,640004003004,640004003005;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'普通金融债')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640008,640008001,640008002,640008002001,640008002002,640008002003,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640018,640024;gnfl=000200020046','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'产业')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640008,640008001,640008002,640008002001,640008002002,640008002003,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640018,640024;gnfl=000200020001','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'城投')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'ABS')
    df=THS_DR('p04675',f'date={dt};sclx=0;zqlx=640006,640007,640021,640021001,640021002;gnfl=0','p04675_f001:Y,p04675_f004:Y','format:dataframe')
    pro_df(df,'转债')
    if df is None:
        continue

date_list = pd.read_sql("""select distinct dt from bond.marketinfo_curve where dt not in (select distinct dt from yq.债券市场规模) and dt>='2024-01-01'
                      """, _cursor_bond)
date_list['dt']=pd.to_datetime(date_list['dt'])
dates = date_list['dt'].tolist()
formatted_dates = [date.strftime('%Y%m%d') for date in dates]
for dt in formatted_dates:
    df=THS_DR('p04665',f'date={dt};sclx=0;fl=640;gnfl=0','p04665_f001:Y,p04665_f004:Y','format:dataframe')
    df=df.data
    df.columns = ['类型', '余额']
    # 将字符串解析为日期对象
    dt_obj = datetime.strptime(dt, '%Y%m%d')
    # 然后将日期对象格式化为 'YYYY-MM-DD'
    dt_formatted = dt_obj.strftime('%Y-%m-%d')
    df['dt'] = dt_formatted
    try:    
        df.to_sql('债券市场规模', con=_cursor_yq, if_exists='append', index=False)
    except Exception as e:
        print(e)