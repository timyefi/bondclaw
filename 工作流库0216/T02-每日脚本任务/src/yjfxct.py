#用益信托网
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
import numpy as np
from sqlalchemy import inspect, MetaData, Table, Column, Text, text
from datetime import datetime, timedelta 
from iFinDPy import *
from WindPy import w


sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
# _cursor = sql_engine.connect()

w.start()
# THS_iFinDLogin('hznd002', '160401')
THS_iFinDLogin('nylc082','491448') 
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

# 获取当前日期  
current_date = datetime.now()
start_date = datetime(2024, 6, 1)

# current_date1 = current_date - timedelta(days=1)
# dt=current_date1.strftime('%Y%m%d')
dt1=current_date.strftime('%Y-%m-%d')
# dt0=start_date.strftime('%Y-%m-%d')

def get_data(code,dt,type,database_name,table_name):
    try:
        if table_name=='edbdata':
            query = f"""
            SELECT
            close
            FROM
                {database_name}.{table_name}
            where dt='{dt}'
            and trade_code='{code}'"""
            with sql_engine.begin() as connection:
                dates=pd.read_sql(query,con=connection)
            if len(dates)!=0:
                print('edbdata已有')
                return
        if table_name=='一级发行跟踪':
            query = f"""
            SELECT
            trade_code
            FROM
                {database_name}.{table_name}
            where 起息日期='{dt}'"""
            with sql_engine.begin() as connection:
                dates=pd.read_sql(query,con=connection)
            if len(dates)!=0:
                print('一级发行跟踪已有')
                return
    except:
        dt0=datetime(2015,1,31)

    if 0<1:
        dt=pd.to_datetime(dt)
        dt0 = dt.strftime('%Y%m%d')
        print(dt0)
        if type==1:
            dt0 = dt.strftime('%Y-%m-%d')
            print(1)
            error_code, wsd_data=w.edb(f"{code}", f"{dt0}", f"{dt0}",usedf = True)
            wsd_data.reset_index(inplace=True)
            wsd_data.columns=['TRADE_CODE','CLOSE']
            wsd_data['DT']=dt0
            wsd_data=wsd_data[['TRADE_CODE','CLOSE','DT']]
            if error_code == 0:
                pro_data(wsd_data,database_name,table_name)
        else:
            df=THS_DR('p04524',f'sdate={dt0};edate={dt0};zqlx=640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024;sclx=0;jglx=0;datetype=7;fxqx=0;ztpj=0;hy=0;qyxz=0;dq=0;gnfl=000200020001','jydm:Y,jydm_mc:Y,p04524_f001:Y,p04524_f008:Y,p04524_f009:Y,p04524_f010:Y,p04524_f011:Y,p04524_f012:Y,p04524_f067:Y,p04524_f013:Y,p04524_f017:Y,p04524_f018:Y,p04524_f035:Y','format:dataframe')
            df = df.data
            if df is None:
                print(f'{dt0}未取到')
            else:
                df.columns=['trade_code','债券简称','发行人','发行金额','债券期限','特殊期限','债券评级','主体评级','YY定价','票面利率','NAFMI参考利率','参考利率价差','起息日期']
                # df.columns=['trade_code','债券简称','YY定价','起息日期']
                print(df)
                # df=df[['time','value']]
                # df.columns=['index',code]
                # df.set_index('index',inplace=True)
                pro_data(df,database_name,table_name)


# start_date=datetime(2024,10,11)
start_date=datetime.now()
end_date=datetime.now()
# end_date=datetime(2024,5,30)
for dt in pd.date_range(start=start_date, end=end_date):
    print(dt)
    get_data('',dt,2,'yq','一级发行跟踪')
    get_data('M0062050',dt,1,'edb','edbdata')
    


# sql="""
# SELECT
#     起息日期 as dt,
#     trade_code
#     from yq.一级发行跟踪
#     where cfets估值 is null"""
# with sql_engine.begin() as connection:
#     df=pd.read_sql(sql,con=connection)
# for dt,trade_code in zip(df['dt'],df['trade_code']):
#     print(dt,trade_code)
#     df=THS_DS(f'{trade_code}','ths_evaluate_yeild_cfets_bond','','',f'{dt}',f'{dt}')
#     df = df.data
#     if df is None:
#         print(f'{dt1}未取到')
#     else:
#         df=df[['time','thscode','ths_evaluate_yeild_cfets_bond']]
#         df.columns=['起息日期','trade_code','cfets估值']
#         print(df)
#         # df=df[['time','value']]
#         # df.columns=['index',code]
#         # df.set_index('index',inplace=True)
#         pro_data(df,'yq','一级发行跟踪')
