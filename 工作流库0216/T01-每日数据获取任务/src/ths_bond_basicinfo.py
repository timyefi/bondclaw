import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

import iFinDPy as THS
THS.THS_iFinDLogin('hznd002', '160401')
# THS.THS_iFinDLogin('hzmd112', '992555')

from sql_conns_new import insert_update_info, insert_database

sql_engine = create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'stock',
    ), pool_size=20, max_overflow=10, pool_timeout=10, pool_recycle=3600
)
conn = sql_engine.connect()

bond_codes = {
    '国债': '031026_640001',
    '地方政府债': '031026_640002',
    '央行票据': '031026_640003',
    '同业存单': '031026_640016',
    '政府支持机构债': '031026_640022',
    '金融债': '031026_640004',
    '企业债': '031026_640005',
    '公司债': '031026_640008',
    '中期票据': '031026_640012',
    '集合票据': '031026_640013',
    '短期融资券': '031026_640014',
    '非公开定向债务融资工具(PPN)': '640014100',
    '项目收益票据(PRN)': '031026_640018',
    '国际机构债': '031026_640009',
    '其他债券': '031026_640015',
    '资产支持证券': '031026_640010',
    '可转债': '031026_640007',
    '可分离可转债': '031026_640006',
    '可交换债券': '031026_640021'
}

bond_categories = {
    '国债': 'rate',
    '地方政府债': 'rate',
    '央行票据': 'rate',
    '同业存单': 'finance',
    '政府支持机构债': 'rate',
    '金融债': 'finance',
    '企业债': 'credit',
    '公司债': 'credit',
    '中期票据': 'credit',
    '集合票据': 'credit',
    '短期融资券': 'credit',
    '非公开定向债务融资工具(PPN)': 'credit',
    '项目收益票据(PRN)': 'credit',
    '国际机构债': 'credit',
    '其他债券': 'credit',
    '资产支持证券': 'abs',
    '可转债': 'equity',
    '可分离可转债': 'equity',
    '可交换债券': 'equity'
}

code_dts = pd.read_sql("SELECT DT FROM `stock`.`indexcloseprice` WHERE `TRADE_CODE` = '881001.WI' ORDER BY `DT` DESC limit 1", conn)['DT'].apply(lambda x:x.strftime('%F'))

# 增量数据拉取
for DT in code_dts:
    for bond_type, bond_code in bond_codes.items():
        database = 'bond.basicinfo_' + bond_categories[bond_type]

        result = THS.THS_DR('p03291',f"date={DT.replace('-', '')};blockname={bond_code};iv_type=allcontract",'p03291_f002:Y','format:dataframe')
        if result.errorcode == 0:
            data_df = result.data.rename(columns={'p03291_f002':'TRADE_CODE'})
            data_insert_df = data_df.loc[~data_df['TRADE_CODE'].isin(pd.read_sql(f"select TRADE_CODE from {database}", conn)['TRADE_CODE'].to_list())]
            insert_database(data_insert_df, database, [])
            insert_update_info(data_insert_df, database, 'THS')
            print(f"{bond_type}: {data_insert_df.shape}")
        else:
            print("Error occurred:", result.errmsg)
        # break
