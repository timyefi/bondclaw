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
from WindPy import w
from iFinDPy import *


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

# w.start()

THS_iFinDLogin('nylc082','491448') 
# THS_iFinDLogin('hzqh172','6769be')
# THS_iFinDLogin('hznd002', '160401')


def generate_column_mapping(columns):
    return {col: f"col_{i}" for i, col in enumerate(columns)}

def change_column_names(table_name, column_mapping, to_english=True):
    with sql_engine.begin() as connection:
        for original_name, new_name in column_mapping.items():
            if to_english:
                connection.execute(text(f"ALTER TABLE `{table_name}` CHANGE `{original_name}` `{new_name}` VARCHAR(255);"))
            else:
                connection.execute(text(f"ALTER TABLE `{table_name}` CHANGE `{new_name}` `{original_name}` VARCHAR(255);"))

def pro_data(wsd_data, table_name):
    # 将 dt 列转换为 datetime 对象，并剔除转换失败的行
    wsd_data['dt'] = pd.to_datetime(wsd_data['dt'], errors='coerce')
    wsd_data = wsd_data.dropna(subset=['dt'])
    wsd_data['dt'] = wsd_data['dt'].dt.strftime('%Y-%m-%d')
    
    # 将 NaN 值替换为 None
    wsd_data = wsd_data.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
    if wsd_data.empty:
        print("No valid data to insert.")
        return

    # 生成列名映射
    column_mapping = generate_column_mapping(wsd_data.columns)
    wsd_data = wsd_data.rename(columns=column_mapping)

    inspector = inspect(sql_engine)
    table_exists = inspector.has_table(table_name)
    if table_exists:
        # 获取现有表的列名
        existing_columns = inspector.get_columns(table_name)
        existing_columns_names = [col['name'] for col in existing_columns]
        wsd_data_columns = wsd_data.columns.tolist()

        # 检查并添加缺失的列
        for col in wsd_data_columns:
            if col not in existing_columns_names:
                col_type = "FLOAT" if pd.api.types.is_numeric_dtype(wsd_data[col]) else "VARCHAR(255)"
                with sql_engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE `{table_name}` ADD COLUMN `{col}` {col_type};"))

        insert_columns = ', '.join([f"`{col}`" for col in wsd_data_columns])
        update_columns = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in wsd_data_columns])
        value_placeholders = ', '.join([f":{col}" for col in wsd_data_columns])

        insert_query = text(f"""
        INSERT INTO `{table_name}` ({insert_columns})
        VALUES ({value_placeholders})
        ON DUPLICATE KEY UPDATE {update_columns};
        """)

        # 打印调试信息
        print("Generated SQL Query:")
        print(insert_query)
        print("Sample Data Row:")
        print(wsd_data.iloc[0].to_dict())

        # 插入或更新数据
        with sql_engine.begin() as connection:
            for _, row in wsd_data.iterrows():
                try:
                    # 打印每一行的数据
                    print("Inserting row:", row.to_dict())
                    params = {col: row[col] for col in wsd_data_columns}
                    print("Params:", params)
                    connection.execute(insert_query, params)
                except Exception as e:
                    print(f"Error inserting row: {row}")
                    print("Exception:", e)
        print('更新完成')


# 获取当前日期  
current_date = datetime.now()
# start_date = datetime(2024, 6, 1)

current_date1 = current_date + timedelta(days=1)
current_date2 = current_date + timedelta(days=30)
dt0=current_date1.strftime('%Y%m%d')
dt1=current_date2.strftime('%Y%m%d')
# dt1=current_date.strftime('%Y-%m-%d')
# dt0=start_date.strftime('%Y-%m-%d')
# query = f"""
# SELECT
#     max(dt) as dt
# FROM
#     yq.金融资负"""
# with sql_engine.begin() as connection:
#     dates=pd.read_sql(query,con=connection)
# dt0=dates['dt'].iloc[0]
# dt0 = (dt0 + timedelta(days=1)).strftime('%Y-%m-%d')
print(f"{dt0},{dt1}")
# error_code, wsd_data=w.wset("newbondissueview","startdate=2024-09-09;enddate=2024-09-15;datetype=paymentdate;bondtype=债券分类(Wind);dealmarket=allmarkets;maingrade=all;field=windcode,paydate,planissueamount,bondterm,bondtype,isurbanincestmentbonds",usedf = True)
# if error_code == 0:
#     pro_data(wsd_data)

df=THS_DR('p04524',f'sdate={dt0};edate={dt1};zqlx=640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024;sclx=0;jglx=0;datetype=5;fxqx=0;ztpj=0;hy=0;qyxz=0;dq=0;gnfl=0','jydm:Y,jydm_mc:Y,p04524_f005:Y,p04524_f006:Y,p04524_f009:Y,p04524_f029:Y,p04524_f063:Y','format:dataframe')

df=df.data
if df is not None:
    df.columns=['trade_code','sec_name','dt','planissueamount','bondterm','bondtype','isurbanincestmentbonds']

table_name = '债券新发行1'
# 生成列名映射
column_mapping = generate_column_mapping(df.columns)

# 修改表的列名为英文
change_column_names(table_name, column_mapping, to_english=True)

# 处理数据
try:
    pro_data(df, table_name)
except Exception as e:
    print("Exception:", e)

# 修改表的列名为中文
change_column_names(table_name, column_mapping, to_english=False)
        
# with sql_engine.begin() as connection:
#     df.to_sql('债券新发行1',connection,if_exists='replace',index=False)