from datetime import datetime, date, timedelta, time
import numpy as np
import pandas as pd

import pandas as pd
import sqlalchemy
import numpy as np
from datetime import datetime, timedelta

# 数据库连接
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

bd = '2020-01-01'
ed = '2024-12-8'
name0=f'{bd}-{ed}期间所处分位点'
terms1 ="','".join(['10'])
terms2 ="','".join(['10'])
yhpj1="','".join(['AA+'])
yhpj2="','".join([''])
class10='普通城投债'
class20='国债'
if class10 =

mapping = {
    '国债': '中债国债到期收益率',
    '国开': '中债国开债到期收益率',
    '口行': '中债进出口行债到期收益率',  # 假设'口行'代表'进出口行'
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
class1 = mapping[class10]
class2 = mapping[class20]
mapping1 = {
    '0.083333333': 0.083,
    '0.24999999899999997': 0.25,
    '0.49999999799999995': 0.5,  # 假设'口行'代表'进出口行'
    '0.749999997': 0.75,
    '1':1,
	'2':2,
    '3':3,
    '4':4,
    '5':5,
    '7':7,
    '10':10,
    '15':15,
    '20':20,
    '30':30
}

def get_sql(classname,yhpj):
    if classname in ['国债','国开','口行','农发','地方债']:
        sql1=''
    else:
        sql1=f"""and sq.隐含评级 in ('{yhpj}')"""
    return sql1

if class10 in ['国债','国开','口行','农发','地方债']:
    name1=f'{class10}'
else:
    name1=f'{yhpj1}{class10}'
if class20 in ['国债','国开','口行','农发','地方债']:
    name2=f'{class20}'
else:
    name2=f'{yhpj2}{class20}'
term3 = [str(mapping1[term]) for term in ['10']]
term3 = "','".join(term3)
term4 = [str(mapping1[term]) for term in ['10']]
term4 = "','".join(term4)

name=f'{term3}年期{name1}/{term4}年期{name2}历史分位点'


df=pd.read_sql(f"""SELECT sq1.dt,
round(100*sq1.收益率/sq2.收益率,2) as close,
sq1.收益率 as close1,
sq2.收益率 as close2
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
and A.dt BETWEEN '{bd}' AND '{ed}')sq
where sq.曲线期限 in ('{terms1}'){get_sql(class10,yhpj1)}
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
WHERE B.classify2 like '{class2}%%'
and A.dt BETWEEN '{bd}' AND '{ed}')sq
where sq.曲线期限 in ('{terms2}'){get_sql(class20,yhpj2)}
GROUP BY sq.dt)sq2
on sq1.dt=sq2.dt
""",_cursor)

df['dt'] = pd.to_datetime(df['dt'])
window_size = timedelta(days=365 * 10)
i=1
df[df.columns[i]] = (((df['dt'].apply(lambda x: df[(x - window_size <= df['dt']) & (df['dt'] <= x)][df.columns[i]].rank(pct=True).iloc[-1])).astype(float)*100)).round(2)
print(df)