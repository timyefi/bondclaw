#同花顺理财
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
_cursor = sql_engine.connect()

from datetime import datetime

from datetime import datetime, timedelta 
THS_iFinDLogin('nylc082','491448') 
  
# 获取当前日期  
current_date = datetime.now()
current_date1 = current_date - timedelta(days=1)
current_date=current_date1.strftime('%Y%m%d')
dt=current_date1.strftime('%Y-%m-%d')
df=THS_DR('p02186',f'type=收益起始日期;sdate={current_date};edate={current_date}','p02186_f002:Y,p02186_f003:Y,p02186_f004:Y,p02186_f005:Y,p02186_f006:Y,p02186_f007:Y,p02186_f008:Y,p02186_f009:Y,p02186_f010:Y,p02186_f011:Y,p02186_f012:Y,p02186_f013:Y,p02186_f014:Y,p02186_f015:Y,p02186_f016:Y,p02186_f017:Y,p02186_f018:Y,p02186_f019:Y,p02186_f020:Y,p02186_f021:Y,p02186_f022:Y,p02186_f023:Y,p02186_f024:Y,p02186_f025:Y,p02186_f001:Y','format:dataframe')
df=df.data
if df is None:
    pass
    print(f'{dt}未取到')
else:
    df=df[df['p02186_f002']=='合计']
    df['p02186_f002'].iloc[0]=dt
    df=df[['p02186_f002', 'p02186_f003', 'p02186_f005','p02186_f006',  'p02186_f008', 'p02186_f009','p02186_f011', 'p02186_f012', 'p02186_f014', 'p02186_f015', 'p02186_f017','p02186_f018', 'p02186_f020', 'p02186_f021', 'p02186_f023', 'p02186_f024']]
    df.columns=['dt', '1个月以内数量',  '1个月以内占比','1-3月数量',  '1-3月占比', '3-6月数量','3-6月占比', '6-12月数量', '6-12月占比', '12-24月数量', '12-24月占比','24月以上数量', '24月以上占比', '未公布数量', '未公布占比', '总数']
    df.to_sql('理财期限跟踪', con=_cursor, if_exists='append', index=False)
    _cursor.commit()
    print(dt)