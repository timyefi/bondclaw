import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

from sqlalchemy import create_engine
import pandas as pd

def insert_database(raw: pd.DataFrame, db: str, key_list: list, mode='UPDATE', dt_type='DATE'):
    """
    :param raw:
    :param db:
    :param key_list:
    :param mode: 'update' or 'replace'
    :return:
    """
    if 'DT' in raw.columns:
        if dt_type == 'DATE':
            raw['DT'] = raw['DT'].apply(lambda x: str(x)[:10])
    final_table = raw.where(raw.notnull(), None)  # 将NAN，Nan转换为None
    values = final_table.values.tolist()
    if mode == 'UPDATE':
        col = raw.columns.tolist()
        col2 = col.copy()
        if len(key_list) > 0:
            for key in key_list:
                col2.remove(key)

        update_str = ','.join(f'`{x}` = VALUES(`{x}`)' for x in col2)
        SQL.executemany(
            f"INSERT INTO {db} (`{'`,`'.join(x for x in col)}`) VALUES (%s{', %s' * (len(raw.columns) - 1)}) ON DUPLICATE KEY UPDATE {update_str}",
            values)

    elif mode == 'REPLACE':
        SQL.executemany(
            f"REPLACE INTO {db} VALUES (%s{', %s' * (len(final_table.columns) - 1)})", values)

    else:
        raise Exception('SELECT MODE IN (UPDATE, REPLACE)')

sql_engine = create_engine(
        'mysql+pymysql://%s:%s@%s:%s/%s' % (
            'hz_work',
            'Hzinsights2015',
            'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            '3306',
            'bond',
        )
    )
conns = sql_engine.connect()


import iFinDPy as THS
from sql_conns_new import insert_update_info, insert_database
THS.THS_iFinDLogin('hznd002', '160401')
# THS.THS_iFinDLogin('hzmd112', '992555')

dts = []

# 主数据（严格两个日期，否则报错）
main_dates = [i.strftime('%Y%m%d') for i in pd.read_sql("select DT from stock.indexcloseprice where trade_code = '881001.WI' order by DT desc limit 2", conns).T.values[0]]

dts.append([main_dates[0], main_dates[0]])  # 强制两个不同日期

# # 补数数据（严格单日）
# hist_date = [i.strftime('%Y%m%d') for i in pd.read_sql(f"SELECT DT FROM dealtinfo GROUP BY DT HAVING COUNT(*) < 5000 and DT < '{main_dates[1]}' ORDER BY DT DESC LIMIT 1", conns).T.values[0]][0]

# if hist_date:
#     dts.append([hist_date, hist_date])  # 严格单日模式

print(dts)
# 执行循环
for edate, sdate in dts:    
    print(edate, sdate)
    df = THS.THS_DR('p03751',f'sdate={sdate};edate={edate};type=640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024;jycs=全部;cjly=0;datetype=年;syqxmin=;syqxmax=;code=','p03751_f001:Y,p03751_f002:Y,p03751_f003:Y,p03751_f004:Y,p03751_f005:Y,p03751_f006:Y,p03751_f007:Y,p03751_f008:Y,p03751_f009:Y,p03751_f010:Y,p03751_f011:Y,p03751_f012:Y,p03751_f018:Y,p03751_f019:Y,p03751_f020:Y,p03751_f021:Y,p03751_f022:Y,p03751_f023:Y,p03751_f024:Y,p03751_f025:Y,p03751_f026:Y,p03751_f027:Y','format:dataframe')
        #  THS_DR('p03751','sdate=20240321;edate=20240328;type=640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024;jycs=全部;cjly=0;datetype=年;syqxmin=;syqxmax=;code=','p03751_f001:Y,p03751_f002:Y,p03751_f003:Y,p03751_f004:Y,p03751_f005:Y,p03751_f006:Y,p03751_f007:Y,p03751_f008:Y,p03751_f009:Y,p03751_f010:Y,p03751_f011:Y,p03751_f012:Y,p03751_f013:Y,p03751_f014:Y,p03751_f015:Y,p03751_f016:Y,p03751_f017:Y,p03751_f018:Y,p03751_f019:Y,p03751_f020:Y,p03751_f021:Y,p03751_f022:Y,p03751_f023:Y,p03751_f024:Y,p03751_f025:Y,p03751_f026:Y,p03751_f027:Y,p03751_f028:Y,p03751_f029:Y,p03751_f030:Y,p03751_f031:Y,p03751_f032:Y,p03751_f033:Y,p03751_f034:Y,p03751_f035:Y,p03751_f036:Y,p03751_f037:Y,p03751_f038:Y,p03751_f039:Y,p03751_f040:Y','format:dataframe')
        #  THS_DR('p03751','sdate=20240321;edate=20240328;type=640,640001,640001001,640001002,640001003,640001004,640002,640002001,640002002,640002003,640002004,640003,640004,640004001,640004001001,640004001002,640004001003,640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005,640005,640005001,640005001001,640005001002,640005001003,640005002,640005002001,640005002002,640006,640007,640008,640008001,640008002,640008002001,640008002002,640008002003,640009,640009001,640009002,640009003,640009004,640010,640010001,640010001001,640010001002,640010001003,640010002,640010003,640010006,640011,640012,640013,640013001,640013002,640014,640014001,640014003,640015,640016,640016001,640016002,640018,640021,640021001,640021002,640022,640024;jycs=全部;cjly=0;datetype=年;syqxmin=;syqxmax=;code=','p03751_f001:Y,p03751_f002:Y,p03751_f003:Y,p03751_f005:Y,p03751_f006:Y,p03751_f007:Y,p03751_f008:Y,p03751_f009:Y,p03751_f010:Y,p03751_f011:Y,p03751_f012:Y,p03751_f013:Y,p03751_f014:Y,p03751_f015:Y,p03751_f016:Y,p03751_f017:Y,p03751_f018:Y,p03751_f019:Y,p03751_f020:Y,p03751_f021:Y,p03751_f022:Y,p03751_f023:Y,p03751_f024:Y,p03751_f025:Y,p03751_f026:Y,p03751_f027:Y,p03751_f028:Y,p03751_f029:Y,p03751_f030:Y,p03751_f031:Y,p03751_f032:Y','format:dataframe')
# #区间日行情,输入参数:开始日期(sdate)、截止日期(edate)、债券类型(type)、交易场所(jycs)、成交来源(cjly)、日期类型(datetype)、剩余期限-开始(syqxmin)、剩余期限-结束(syqxmax)、检索(code)、概念分类(gnfl)-iFinD数据接口
# THS_DR('p04685','sdate=20240611;edate=20240710;type=640004002,640004002001,640004002002,640004002003,640004002004,640004002005,640004003,640004003001,640004003002,640004003003,640004003004,640004003005;jycs=0;cjly=4;datetype=1;syqxmin=;syqxmax=;code=;gnfl=0','p04685_f001:Y,p04685_f002:Y,p04685_f003:Y,p04685_f004:Y,p04685_f009:Y,p04685_f011:Y,p04685_f023:Y,p04685_f024:Y,p04685_f025:Y','format:dataframe')
df.data.columns = pd.read_sql("select * from bond.dealtinfo limit 1", conns).columns
insert_database(df.data.fillna(''), 'bond.dealtinfo', ['DT', 'TRADE_CODE'])
insert_update_info(df.data.fillna(''), 'bond.dealtinfo', 'THS')
#df.data.to_sql('dealtinfo', conns, if_exists='append', index=False)
# df.data