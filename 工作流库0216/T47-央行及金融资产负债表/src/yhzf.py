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

def pro_data(wsd_data):
    wsd_data = wsd_data.reset_index().rename(columns={'index': 'dt'})
    
    # 将 dt 列转换为 datetime 对象，并剔除转换失败的行
    wsd_data['dt'] = pd.to_datetime(wsd_data['dt'], errors='coerce')
    wsd_data = wsd_data.dropna(subset=['dt'])
    
    # 过滤掉日期小于 dt0 的数据
    wsd_data = wsd_data[wsd_data['dt'] >= pd.to_datetime(dt0)]
    
    # 将 NaN 值替换为 None
    wsd_data = wsd_data.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
    if wsd_data.empty:
        print("No valid data to insert.")
        return

    inspector = inspect(sql_engine)
    table_exists = inspector.has_table('金融资负')
    if table_exists:
        # 获取现有表的列名
        existing_columns = inspector.get_columns('金融资负')
        existing_columns_names = [col['name'] for col in existing_columns]
        # 获取df_news的列名
        wsd_data_columns = wsd_data.columns.tolist()

        # 检查并添加缺失的列
        for col in wsd_data_columns:
            if col not in existing_columns_names:
                with sql_engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE 金融资负 ADD COLUMN {col} Float;"))

            # 构建INSERT INTO ... ON DUPLICATE KEY UPDATE语句
        columns = wsd_data_columns
        insert_columns = ', '.join(columns)
        update_columns = ', '.join([f"{col} = VALUES({col})" for col in columns])

        insert_query = text(f"""
        INSERT INTO yq.金融资负 ({insert_columns})
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
query = f"""
SELECT
    max(dt) as dt
FROM
    yq.金融资负"""
with sql_engine.begin() as connection:
    dates=pd.read_sql(query,con=connection)
dt0=dates['dt'].iloc[0]
dt0 = (dt0 + timedelta(days=1)).strftime('%Y-%m-%d')
print(f"{dt0},{dt1}")
error_code, wsd_data=w.edb("M0001538,M0001527,M0251904,M0001528,M0001529,M0001530,M0062047,M0062845,M0062846,M0251905,M0001533,M0001534,M0251906,M0251907,M0062848,M0001536,M0001537,M0001557,M0001539,M0061954,M0001540,M0251908,M0001542,M0001545,M0251909,M0001543,M0001547,M0001541,M0001544,M0001548,M0001549,M0001550,M0001551,M0251910,M0251911,M0001552,M0251912,M0061955,M0001554,M0150191,M0062849,M0001556", f"{dt0}", f"{dt1}",usedf = True)
if error_code == 0:
    pro_data(wsd_data)

error_code, wsd_data=w.edb("M0251956,M0251940,M0251941,M0251942,M0251943,M0251944,M0251945,M0251946,M0251947,M0251948,M0251949,M0251950,M0251951,M0251952,M0251953,M0251954,M0251955,M0251977,M0251957,M0251958,M0251959,M0251960,M0251961,M0251962,M0251963,M0251964,M0251965,M0333070,M0333071,M0251966,M0333072,M0251967,M0251968,M0251969,M0251970,M0251971,M0251972,M0251973,M0333073,M0251974,M0251975,M0251976",f"{dt0}", f"{dt1}",usedf = True)
if error_code == 0:
    pro_data(wsd_data)

error_code, wsd_data=w.edb("M0048455,M0048441,M0252060,M0062879,M0048445,M0252061,M0252062,M0062881,M0062876,M0048442,M0048443,M0048444,M0062878,M0252063,M0252064,M0252065,M0252066,M0048451,M0252068,M0048452,M0048453,M0048454,M0048471,M0048456,M0061993,M0048457,M0048466,M0061994,M0061995,M0061996,M0048468,M0150196,M0062883,M0252069,M0048469,M0048470,M0009940,M0043410,M0043412,M0043411,M0043413,M0009947,M0009969,M0043417,M0043418,M0009978,M0043419,M0001380,M0001382,M0001384,M0001386,M0010131,M0001485,M0001486,M0001487,M0001488,M0001489,M0001490,M0001491,M0001492,M0001494,M0001493,M0001495,M0001496,M0001497,M0001504,M0001498,M0001499,M0001500,M5639029,M5639030,M5639031,M5639032,M5639033,M5639034,M5639035,J3426133,M0010125,M5525755,M5525756,M5525757,M5525758,M5525759,M5525760,M5525761,M5525762,M6179494,M6094230,M6094231,Y7375557",f"{dt0}", f"{dt1}",usedf = True)
if error_code == 0:
    pro_data(wsd_data)
