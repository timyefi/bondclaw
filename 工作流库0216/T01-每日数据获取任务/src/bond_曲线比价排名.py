from datetime import datetime, date, timedelta, time
import numpy as np
import pandas as pd
import re
import psycopg2
import logging
import pandas as pd
import sqlalchemy
import numpy as np
import pandas as pd
import time
from sqlalchemy.sql import text
from iFinDPy import *
from time import sleep
from sqlalchemy import inspect, MetaData, Table, Column, Text, text
from sklearn.linear_model import LinearRegression

# 连接源数据库
sql_engine_bond = sqlalchemy.create_engine(
  'mysql+pymysql://%s:%s@%s:%s/%s' % (
    'hz_work',
    'Hzinsights2015',
    'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    '3306',
    'bond',
  ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine_bond.connect()


qxclasses = ['国开', '口行', '农发', '地方债', '中票', '企业债', '普通城投债', '私募城投债', '永续城投债',
      '普通产业债', '私募产业债', '次级产业债', '永续产业债', '银行二级资本债', '银行永续债', '普通金融债', '存单', 'ABS']
terms = ['0.083333333', '0.24999999899999997', '0.49999999799999995',
    '0.749999997', '1', '2', '3', '4', '5', '7', '10', '15', '20', '30']
yhpjs = ['AAA+', 'AAA', 'AAA-', 'AA+', 'AA', 'AA(2)', 'AA-']

mapping = {
  '国债': '中债国债到期收益率',
  '国开': '中债国开债到期收益率',
  '口行': '中债进出口行债到期收益率', # 假设'口行'代表'进出口行'
  '农发': '中债农发行债到期收益率',
  '地方债': '财政部-中国地方政府债券收益率',
  '中票': '中债中短期票据到期收益率',
  '企业债': '中债企业债到期收益率',
  '普通城投债': '中债城投债到期收益率',
  '私募城投债': '中债非公开发行城投债到期收益率',
  '永续城投债': '中债可续期城投债到期收益率',
  '普通产业债': '银行间产业债到期收益率',
  '私募产业债': '中债非公开发行产业债到期收益率',
  '次级产业债': '中债次级可续期产业债到期收益率',
  '永续产业债': '中债可续期产业债到期收益率',
  '银行二级资本债': '中债商业银行二级资本债到期收益率',
  '银行永续债': '中债商业银行无固定期限资本债',
  '普通金融债': '中债商业银行普通债到期收益率',
  '存单': '中债商业银行同业存单到期收益率',
  'ABS': '中债企业资产支持证券'
}


def datePurge(x):
  _x = float(x[:-1])
  if '月' in x:
    _x /= 12
  elif '天' in x:
    _x /= 365
  return _x


mapping1 = {
  '0.083333333': 0.083,
  '0.24999999899999997': 0.25,
  '0.49999999799999995': 0.5, # 假设'口行'代表'进出口行'
  '0.749999997': 0.75,
  '1': 1,
  '2': 2,
  '3': 3,
  '4': 4,
  '5': 5,
  '7': 7,
  '10': 10,
  '15': 15,
  '20': 20,
  '30': 30
}


def get_sql(classname):
  if classname in ['国债', '国开', '口行', '农发', '地方债']:
    sql1 = ''
  else:
    sql1 = f"""and sq.隐含评级 = '{yhpj}'"""
  return sql1


def pro_qx(qxclass, term, yhpj):
  class1 = mapping[qxclass]
  term1 = mapping1[term]
  if qxclass in ['国债', '国开', '口行', '农发', '地方债']:
    name1 = f'{term1}年{qxclass}'
  else:
    name1 = f'{term1}年{yhpj}{qxclass}'
  df = pd.read_sql(f"""SELECT sq1.dt,
  round(100*sq1.收益率/sq2.收益率,2) as '与国债比值%%',
  sq1.收益率 as '曲线收益率%%',
  sq2.收益率 as '国债收益率%%'
  from(
  SELECT 
  sq.dt,avg(sq.收益率) as 收益率
  from(
  SELECT 
  A.dt,
  LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
    (RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
  ) AS 曲线期限,
  SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
      AS 隐含评级,
  A.CLOSE AS 收益率
  FROM bond.marketinfo_curve A
  INNER JOIN bond.basicinfo_curve B
  ON A.trade_code = B.TRADE_CODE
  WHERE B.classify2 like '{class1}%%'
  and A.dt >='2014-01-01')sq
  where sq.曲线期限 = '{term}'{get_sql(qxclass)}
  GROUP BY sq.dt)sq1
  inner join 
  (
  SELECT 
  sq.dt,avg(sq.收益率) as 收益率
  from(  
  SELECT 
  A.dt,
  LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
    (RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
  ) AS 曲线期限,
  SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
      AS 隐含评级,
  A.CLOSE AS 收益率
  FROM bond.marketinfo_curve A
  INNER JOIN bond.basicinfo_curve B
  ON A.trade_code = B.TRADE_CODE
  WHERE B.classify2 like '中债国债到期收益率%%'
  and A.dt >='2014-01-01')sq
  where sq.曲线期限 = '{term}'
  GROUP BY sq.dt)sq2
  on sq1.dt=sq2.dt
  """, _cursor)

  df['dt'] = pd.to_datetime(df['dt'])
  window_size = timedelta(days=365 * 10)
  df['与国债比值历史分位点%'] = ((df['dt'].apply(lambda x: df[(x - window_size <= df['dt'])
            & (df['dt'] <= x)][df.columns[1]].rank(pct=True).iloc[-1]))*100).round(2)
  df['曲线名称'] = name1
  return df


df0 = pd.DataFrame()
for qxclass in qxclasses:
  for term in terms:
    if qxclass in ['国债', '国开', '口行', '农发', '地方债']:
      try:
        print(qxclass, term)
        df = pro_qx(qxclass, term, '')
        df0 = pd.concat([df0, df])
      except:
        continue
    else:
      for yhpj in yhpjs:
        try:
          df = pro_qx(qxclass, term, yhpj)
          df0 = pd.concat([df0, df])
        except:
          continue
dts = df0['dt'].unique()
dt = max(dts)
df1 = df0[df0['dt'] == dt]
try:
  df1.to_sql('曲线比价排名', _cursor, if_exists='append', index=False)
except:
  print('录入失败')
