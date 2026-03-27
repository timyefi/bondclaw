# 同花顺理财
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import random
import pymysql
import sys
import sqlalchemy
from datetime import datetime, date, timedelta
from iFinDPy import *
from sqlalchemy import inspect, text

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine.connect()

# THS_iFinDLogin('hznd002', '160401')
THS_iFinDLogin('nylc082','491448') 

def generate_column_mapping(columns):
    return {col: f"col_{i}" for i, col in enumerate(columns)}

def change_column_names(table_name, column_mapping, to_english=True):
    with sql_engine.begin() as connection:
        for original_name, new_name in column_mapping.items():
            if to_english:
                if original_name=='dt':
                    connection.execute(text(f"ALTER TABLE `{table_name}` CHANGE `{original_name}` `{new_name}` DATE;"))
                else:
                    connection.execute(text(f"ALTER TABLE `{table_name}` CHANGE `{original_name}` `{new_name}` VARCHAR(255);"))
            else:
                if original_name=='dt':
                    connection.execute(text(f"ALTER TABLE `{table_name}` CHANGE `{new_name}` `{original_name}` DATE;"))
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
        df.sort_values
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

def pro_thslc(current_date, dt):
    table_name = '理财期限跟踪1'
    # 获取当前日期  
    df = THS_DR('p02186', f'type=销售起始日期;sdate={current_date};edate={current_date}', 'p02186_f002:Y,p02186_f003:Y,p02186_f004:Y,p02186_f005:Y,p02186_f006:Y,p02186_f007:Y,p02186_f008:Y,p02186_f009:Y,p02186_f010:Y,p02186_f011:Y,p02186_f012:Y,p02186_f013:Y,p02186_f014:Y,p02186_f015:Y,p02186_f016:Y,p02186_f017:Y,p02186_f018:Y,p02186_f019:Y,p02186_f020:Y,p02186_f021:Y,p02186_f022:Y,p02186_f023:Y,p02186_f024:Y,p02186_f025:Y,p02186_f001:Y', 'format:dataframe')
    df = df.data
    if df is None:
        print(f'{dt}未取到')
    else:
        df = df[df['p02186_f002'] == '合计']
        df.loc[df.index[0], 'p02186_f002'] = dt
        df = df[['p02186_f002', 'p02186_f003', 'p02186_f005', 'p02186_f006', 'p02186_f008', 'p02186_f009', 'p02186_f011', 'p02186_f012', 'p02186_f014', 'p02186_f015', 'p02186_f017', 'p02186_f018', 'p02186_f020', 'p02186_f021', 'p02186_f023', 'p02186_f024']]
        df.columns = ['dt', '1个月以内数量', '1个月以内占比', '1-3月数量', '1-3月占比', '3-6月数量', '3-6月占比', '6-12月数量', '6-12月占比', '12-24月数量', '12-24月占比', '24月以上数量', '24月以上占比', '未公布数量', '未公布占比', '总数']
        
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
        
        print(dt)
    return df

current_date = datetime.now()
yesterday = current_date - timedelta(days=1)
sql = """
select distinct dt from yq.理财期限跟踪1
"""
with sql_engine.begin() as connection:
    dtlist = pd.read_sql(sql, con=connection)['dt'].tolist()

data_range = pd.date_range(start=yesterday, end=current_date)
for dt in data_range:
    current_date1 = dt.strftime('%Y%m%d')
    dt1 = dt.strftime('%Y-%m-%d')
    if dt1 not in dtlist:
        pro_thslc(current_date1, dt1)