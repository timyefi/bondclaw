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
current_date1 = current_date + timedelta(days=7)

dt0=current_date.strftime('%Y-%m-%d')
dt1=current_date1.strftime('%Y-%m-%d')
query = f"""
SELECT
    distinct dt
FROM
    yq.债券到期
WHERE
    dt >= '{dt0}'
    """
with sql_engine.begin() as connection:
    dates=pd.read_sql(query,con=connection)
dates['dt']=pd.to_datetime(dates['dt'])

print(f"{dt0},{dt1}")

for dt in pd.date_range(start=dt0, end=dt1):
    if dt in dates['dt'].values:
        continue
    dt_str = dt.strftime('%Y-%m-%d')
    table_name = '债券到期'
    # 生成列名映射

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=governmentbonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='国债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=centralbankbills;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='央行票据'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=cds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='存单'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=commercialbankbonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='普通金融债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=policybankbonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='政策银行债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=commercialbanksubordinatedbonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='商业银行次级债券'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=insurancecompanybonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='保险债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=corporatebondsofsecuritiescompany;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='证券公司债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=securitiescompanycps;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='证券公司短融债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=otherfinancialagencybonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='其他金融机构债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=enterprisebonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='企业债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)


    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=enterprisebonds;dealmarket=allmarkets;conceptbond=urbaninvestmentbonds(wind);field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='企业债'
    wsd_data['isurbanincestmentbonds']='是'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=corporatebonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='公司债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=corporatebonds;dealmarket=allmarkets;conceptbond=urbaninvestmentbonds(wind);field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='公司债'
    wsd_data['isurbanincestmentbonds']='是'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=medium-termnotes;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='中期票据'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=medium-termnotes;dealmarket=allmarkets;conceptbond=urbaninvestmentbonds(wind);field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='中期票据'
    wsd_data['isurbanincestmentbonds']='是'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=cps;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='短期融资券'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=cps;dealmarket=allmarkets;conceptbond=urbaninvestmentbonds(wind);field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='短期融资券'
    wsd_data['isurbanincestmentbonds']='是'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=projectrevenuenotes;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='项目收益票据'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=ppn;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='ppn'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=ppn;dealmarket=allmarkets;conceptbond=urbaninvestmentbonds(wind);field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='ppn'
    wsd_data['isurbanincestmentbonds']='是'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=supranationalbonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='国际机构债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=agencybonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='政府支持机构债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=standardizednotes;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='标准化票据'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=abs;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='abs'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=convertiblebonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='可转债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=exchangeablebonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='可交换债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)

    error_code, wsd_data=w.wset("bondissuanceandmaturity",f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;bondtype=detachableconvertiblebonds;dealmarket=allmarkets;conceptbond=default;field=startdate,enddate,totalredemption",usedf = True)
    wsd_data['bondtype']='可分离转债'
    wsd_data['isurbanincestmentbonds']='否'
    wsd_data.rename(columns={'startdate':'dt'},inplace=True)
    wsd_data.drop(columns=['enddate'],inplace=True)
    column_mapping = generate_column_mapping(wsd_data.columns)
    change_column_names(table_name, column_mapping, to_english=True)
    if error_code == 0:
        pro_data(wsd_data,table_name)
    change_column_names(table_name, column_mapping, to_english=False)