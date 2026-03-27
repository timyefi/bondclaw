# -*- coding: utf-8 -*-
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
from datetime import datetime, timedelta, date

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)

bd = '2014-01-01'
ed = '2024-12-08    '
type_name= ['国债','国开','口行','农发','地方债','城投','产业','普通金融债','二永','存单']
term =['0-1','1-3','2-3','4-5','6-7','8-12','13-17','18-22','23-27','28-50']
type_name1 = "','".join(type_name)
term1 ="','".join(term)
yhpj1 ="','".join(['AAA','AA+','AA','AA(2)','AA-'])
name1=f'7MA成交金额：{type_name1},期限{term1}年,隐含评级{yhpj1}'
name2='收益率'

raw = pd.read_sql(f"""
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1 then '0-1'
	when sq.曲线期限<3 then '1-3'
	when sq.曲线期限<5 then '3-5'
	when sq.曲线期限<7 then '5-7'
	when sq.曲线期限<10 then '7-10'
	when sq.曲线期限<13 then '10-13'
	when sq.曲线期限<17 then '13-17'
	when sq.曲线期限<23 then '17-23'
	when sq.曲线期限<27 then '23-27'
	when sq.曲线期限<33 then '27-33'
	ELSE '33-50'
	END as 久期
from(
SELECT 
A.dt,
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
CASE
		WHEN B.classify2 ='中债国债到期收益率' THEN '国债'
		WHEN B.classify2 ='中债国开债到期收益率' THEN '国开'
		WHEN B.classify2 ='中债进出口行债到期收益率' THEN '口行'
		WHEN B.classify2 ='中债农发行债到期收益率' THEN '农发'
		WHEN B.classify2 ='财政部-中国地方政府债券收益率' THEN '地方债'
		ELSE '地方债'
END AS 曲线名称,
'' AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 in ('中债国债到期收益率','中债国开债到期收益率','中债进出口行债到期收益率','中债农发行债到期收益率','财政部-中国地方政府债券收益率'))sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
union all
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1.5 then '0-1'
	when sq.曲线期限<3.5 then '2-3'
	when sq.曲线期限<5.5 then '4-5'
	when sq.曲线期限<7.5 then '6-7'
	when sq.曲线期限<12.5 then '8-12'
	when sq.曲线期限<17.5 then '13-17'
	when sq.曲线期限<22.5 then '18-22'
	when sq.曲线期限<27.5 then '23-27'
	ELSE '28-50'
	END as 久期
from(
SELECT  
A.dt,
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
'城投' AS 曲线名称,
SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
        AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 like '中债城投债到期收益率%%')sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
union all
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1.5 then '0-1'
	when sq.曲线期限<3.5 then '2-3'
	when sq.曲线期限<5.5 then '4-5'
	when sq.曲线期限<7.5 then '6-7'
	when sq.曲线期限<12.5 then '8-12'
	when sq.曲线期限<17.5 then '13-17'
	when sq.曲线期限<22.5 then '18-22'
	when sq.曲线期限<27.5 then '23-27'
	ELSE '28-50'
	END as 久期
from(
SELECT 
A.dt,
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
'产业' AS 曲线名称,
SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
        AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 like '银行间产业债到期收益率%%')sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
union all
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1.5 then '0-1'
	when sq.曲线期限<3.5 then '2-3'
	when sq.曲线期限<5.5 then '4-5'
	when sq.曲线期限<7.5 then '6-7'
	when sq.曲线期限<12.5 then '8-12'
	when sq.曲线期限<17.5 then '13-17'
	when sq.曲线期限<22.5 then '18-22'
	when sq.曲线期限<27.5 then '23-27'
	ELSE '28-50'
	END as 久期
from(
SELECT
A.dt,  
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
'普通金融债' AS 曲线名称,
SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
        AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 like '中债商业银行普通债到期收益率%%')sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
union all
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1.5 then '0-1'
	when sq.曲线期限<3.5 then '2-3'
	when sq.曲线期限<5.5 then '4-5'
	when sq.曲线期限<7.5 then '6-7'
	when sq.曲线期限<12.5 then '8-12'
	when sq.曲线期限<17.5 then '13-17'
	when sq.曲线期限<22.5 then '18-22'
	when sq.曲线期限<27.5 then '23-27'
	ELSE '28-50'
	END as 久期
from(
SELECT 
A.dt, 
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
'二永' AS 曲线名称,
SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
        AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 like '中债商业银行二级资本债到期收益率%%')sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
union all
SELECT dt,曲线名称,avg(收益率) as 收益率,
CASE 
	when sq.曲线期限<1.5 then '0-1'
	when sq.曲线期限<3.5 then '2-3'
	when sq.曲线期限<5.5 then '4-5'
	when sq.曲线期限<7.5 then '6-7'
	when sq.曲线期限<12.5 then '8-12'
	when sq.曲线期限<17.5 then '13-17'
	when sq.曲线期限<22.5 then '18-22'
	when sq.曲线期限<27.5 then '23-27'
	ELSE '28-50'
	END as 久期
from(
SELECT
A.dt, 
LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
	(RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
) AS 曲线期限,
'存单' AS 曲线名称,
SUBSTRING(REPLACE(B.classify2, '＋', '+'), LOCATE('(', REPLACE(B.classify2, '＋', '+'))+1,CHAR_LENGTH(B.classify2)-LOCATE('(', REPLACE(B.classify2, '＋', '+'))-1)
        AS 隐含评级,
A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt <='{ed}' and A.dt>='{bd}'
and B.classify2 like '中债商业银行同业存单到期收益率%%')sq
where sq.隐含评级 in ('{yhpj1}')
and sq.曲线期限 >0
group by dt,曲线名称,久期
""", _cursor)

raw=raw[raw['曲线名称'].isin(type_name)]
raw=raw[raw['久期'].isin(term)]
raw=raw.groupby('dt').mean()
raw=raw.reset_index()
raw=raw.bfill()