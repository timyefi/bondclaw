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
from sqlalchemy import text
from datetime import datetime,date, timedelta
from iFinDPy import *
import numpy as np

db_config = {
    'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    'user': 'hz_work',
    'password': 'Hzinsights2015',
    'database': 'yq',
    'port': 3306
}
connection = pymysql.connect(**db_config)
#THS_iFinDLogin('nylc082','491448') 
# THS_iFinDLogin('hzqh172','6769be')
THS_iFinDLogin('hznd002', '160401')


# 获取当前日期  
end_date = datetime.now()
current_date1 = end_date - timedelta(days=3)
# current_date1=datetime(2020,1,1)
# end_date=datetime.date(2024,6,1)
with connection.cursor() as cursor:
    query = """
    INSERT INTO 理财业绩跟踪 (`公司名称`, `dt`,  `今年以来净值年化增长率`,`近1月净值年化增长率`,  `近3月净值年化增长率`, `近6月净值年化增长率`,`近1年净值年化增长率`)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    `今年以来净值年化增长率` = VALUES(`今年以来净值年化增长率`),
    `近1月净值年化增长率` = VALUES(`近1月净值年化增长率`),
    `近3月净值年化增长率` = VALUES(`近3月净值年化增长率`),
    `近6月净值年化增长率` = VALUES(`近6月净值年化增长率`),
    `近1年净值年化增长率` = VALUES(`近1年净值年化增长率`);
    """

    current_date = current_date1
    while current_date <= end_date:
        try:
            last_year_end_date = datetime(current_date.year - 1, 12, 31)
            days = (current_date - last_year_end_date).days
            dt=current_date.strftime('%Y%m%d')
            df=THS_DR('p04838',f'edate={dt};cplx=1','p04838_f001:Y,p04838_f002:Y,p04838_f004:Y,p04838_f005:Y,p04838_f006:Y,p04838_f007:Y,p04838_f008:Y','format:dataframe')
            df=df.data
            if df is None:
                pass
                print(f'{dt}未取到')
            else:
                df=df.replace('--',np.nan)
                df.columns=['公司名称', 'dt',  '今年以来净值年化增长率','近1月净值年化增长率',  '近3月净值年化增长率', '近6月净值年化增长率','近1年净值年化增长率']
                df['今年以来净值年化增长率']=df['今年以来净值年化增长率'].astype(float)*365/days
                df['近1月净值年化增长率']=df['近1月净值年化增长率'].astype(float)*365/30
                df['近3月净值年化增长率']=df['近3月净值年化增长率'].astype(float)*365/90
                df['近6月净值年化增长率']=df['近6月净值年化增长率'].astype(float)*365/180
                df['近1年净值年化增长率']=df['近1年净值年化增长率'].astype(float)
                df = df.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
                for index, row in df.iterrows():
                    cursor.execute(query, (row['公司名称'], row['dt'], row['今年以来净值年化增长率'], row['近1月净值年化增长率'], row['近3月净值年化增长率'], row['近6月净值年化增长率'], row['近1年净值年化增长率']))
                print(dt)
                print(df['dt'].tolist())
            connection.commit()
            current_date += timedelta(days=1)
        except Exception as e:
            print(e)

    # 获取当前日期和最近3天的日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=390)
    cursor.execute(f"""
        SELECT
            A.trade_code,
            A.dt,
            A.NAV_ADJ
        FROM
            fund.marketinfo A
        INNER JOIN (
            SELECT DISTINCT trade_code
            FROM fund.basicinfo
            WHERE dt = (SELECT MAX(dt) FROM fund.basicinfo)
            AND FUND_INVESTTYPE IN ('中长期纯债型基金', '被动指数型债券基金', '短期纯债型基金', '增强指数型债券基金')
        ) D
        ON
            A.trade_code = D.trade_code
        WHERE
            A.dt BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}';
    """)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['trade_code', 'dt', 'NAV_ADJ'])
    # 转换日期列为datetime类型
    df['dt'] = pd.to_datetime(df['dt'])
    df.replace(0, np.nan, inplace=True)
    # 填充缺失日期
    df = df.set_index('dt').groupby('trade_code').apply(lambda x: x.resample('D').ffill()).reset_index(level=0, drop=True).reset_index()
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    print(df)
    # 计算近1月年化收益率和近1年年化收益率
    df['近1月年化收益率'] = df.groupby('trade_code')['NAV_ADJ'].apply(lambda x: (x / x.shift(30) - 1) * 365 / 30).reset_index(level=0, drop=True)
    df['近1年收益率'] = df.groupby('trade_code')['NAV_ADJ'].apply(lambda x: (x / x.shift(365) - 1)).reset_index(level=0, drop=True)
    # 计算每个日期的平均收益率
    df=df[df['trade_code']!='511010.OF']
    avg_df = df.groupby('dt').agg({
        '近1月年化收益率': 'mean',
        '近1年收益率': 'mean'
    }).reset_index()
    
    avg_df.dropna(inplace=True)
    # 插入或更新目标表
    for _, row in avg_df.iterrows():
        cursor.execute("""
        INSERT INTO fund.纯债基金业绩表现 (dt, 近1月年化收益率, 近1年收益率)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            近1月年化收益率 = VALUES(近1月年化收益率),
            近1年收益率 = VALUES(近1年收益率);
        """, (row['dt'], row['近1月年化收益率'], row['近1年收益率']))
    # 提交事务
connection.commit()
connection.close()



