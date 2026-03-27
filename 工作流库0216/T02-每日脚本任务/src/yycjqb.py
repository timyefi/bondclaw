#任务1：取最近15天
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
from datetime import datetime,date, timedelta
from sqlalchemy import inspect, MetaData, Table, Column, Text, text


sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)

def pro_data(wsd_data):
    # wsd_data = wsd_data.reset_index().rename(columns={'index': 'dt'})
    
    # 将 dt 列转换为 datetime 对象，并剔除转换失败的行
    wsd_data['tradedDate'] = pd.to_datetime(wsd_data['tradedDate'], errors='coerce')
    wsd_data = wsd_data.dropna(subset=['tradedDate'])
    
    # 过滤掉日期小于 dt0 的数据
    # wsd_data = wsd_data[wsd_data['dt'] >= pd.to_datetime(dt0)]
    
    # 将 NaN 值替换为 None
    wsd_data = wsd_data.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
    if wsd_data.empty:
        print("No valid data to insert.")
        return

    inspector = inspect(sql_engine)
    table_exists = inspector.has_table('cjqb')
    if table_exists:
        # 获取现有表的列名
        existing_columns = inspector.get_columns('cjqb')
        existing_columns_names = [col['name'] for col in existing_columns]
        # 获取df_news的列名
        wsd_data_columns = wsd_data.columns.tolist()

        # 检查并添加缺失的列
        for col in wsd_data_columns:
            if col not in existing_columns_names:
                col_type = "FLOAT" if pd.api.types.is_numeric_dtype(wsd_data[col]) else "VARCHAR(255)"
                with sql_engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE `cjqb` ADD COLUMN {col} {col_type};"))

            # 构建INSERT INTO ... ON DUPLICATE KEY UPDATE语句
        columns = wsd_data_columns
        insert_columns = ', '.join(columns)
        update_columns = ', '.join([f"{col} = VALUES({col})" for col in columns])

        insert_query = text(f"""
        INSERT INTO yq.`cjqb` ({insert_columns})
        VALUES ({', '.join([f':{col}' for col in columns])})
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
                    connection.execute(insert_query,  row.to_dict())
                except Exception as e:
                    print(f"Error inserting row: {row}")
                    print(e)
        print('更新完成')


def get_content(bd,ed):
    global proxies
    global run_count
    global start_time
    url = "https://host.ratingdog.cn/api/services/app/Bond/QueryTradedHistoricalOfFrontDeskTenants"
    
    headers_login = {
        '.Aspnetcore.Culture': 'zh-Hans',
        'authority': 'auth.ratingdog.cn',
        'ethod': 'POST',
        'path': '/api/TokenAuth/Authenticate',
        'cheme': 'https',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Length': '100',
        'Content-Type': 'application/json;charset=UTF-8',
        'Devicechannel': 'gclife_bmp_pc',
        'Origin': 'https://www.ratingdog.cn',
        'Priority': 'u=1, i',
        'Ratingdog.Tenantid': '114',
        'Referer': 'https://www.ratingdog.cn/',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site':'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
    }

    # 定义 data
    data_login = {
        "UserNameOrEmailAddressOrPhone": "13918339361",
        "internationalPhoneCode": "86",
        "password": "welcome@1"
    }
    url_login='https://auth.ratingdog.cn/api/TokenAuth/Authenticate'
    r = requests.post(url_login, headers=headers_login, json=data_login)
    accessToken=r.json()['result']['accessToken']
    headers = {
        '.Aspnetcore.Culture': 'zh-Hans',
        'Host': 'host.ratingdog.cn',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        "Authorization": f"Bearer {accessToken}",
        'Content-Length': '242',
        'Content-Type': 'application/json;charset=UTF-8',
        'Devicechannel': 'gclife_bmp_pc',
        'Origin': 'https://www.ratingdog.cn',
        'Ratingdog.Tenantid': '114',
        'Referer': 'https://www.ratingdog.cn/',
        'Sec-Ch-Ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        }
    # num=4283*150
    num=0
    totalCount=num
    while num<=totalCount:
        post_dict = {
        "BondTypes": [],
        "Citys": [],
        "EndTradedDate":ed,
        "IssueMethods": [],
        "IssuerTypes": [],
        "MaxResultCount": 150,
        "Natures": [],
        "SkipCount": num,
        "SourceTypes": [],
        "StartTradedDate": bd,
        "TransactionMarkets": [],
        "YYIndustrys": [],
        "YYRatings": [],
        }
        def tryres():
            try:
                response = requests.post(url, headers=headers, json=post_dict, timeout=30)
            except:
                df=tryres()
            try:
                df=response.json()
            except:
                df=tryres()
            if df['success']!=True:
                df=tryres()
            return df
    
        try:
            df=tryres()
        except:
            df=tryres()
        if totalCount==0:
            try:
                totalCount=df['result']['totalCount']
            except:
                totalCount=0
        df=pd.DataFrame(df['result']['items'])
        print(df)
        if not df.empty:
            pro_data(df)
        num1=num/150
        print(f'成功{num1}')
        num+=150

with sql_engine.begin() as connection:
    date_list = pd.read_sql("""select distinct dt from bond.marketinfo_curve where dt not in (select distinct tradedDate from yq.cjqb)
    and dt>='2024-01-01'
           """, connection)
    # date_list = pd.read_sql("""select distinct dt from bond.marketinfo_curve where dt='2024-10-15'
    #        """, connection)

# start_date_str = min(date_list['dt']).strftime("%Y-%m-%d")
# end_date_str = max(date_list['dt']).strftime("%Y-%m-%d")
# start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
# end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

# 遍历日期范围，包含end_date的当天
# current_date = start_date
# while current_date <= end_date:
for current_date in date_list['dt']:
    # 在这里执行您想要的操作，比如获取内容
    # 这里用print代替
    dt=current_date.strftime("%Y-%m-%d")
    dt=datetime.strptime(dt, "%Y-%m-%d")
    print(dt)
    get_content(dt,dt)
    
    # 移动到下一天
    current_date += timedelta(days=1)



