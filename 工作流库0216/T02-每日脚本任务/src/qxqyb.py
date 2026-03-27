# 用益信托网
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
from datetime import datetime, date, timedelta
import requests
from bs4 import BeautifulSoup
import re

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
sql = """
SELECT 
    distinct
    case when
    (A.classify2 LIKE '%%中债%%' AND A.classify2 LIKE '%%城投债%%') then '是'
    else '否' end AS 是否城投,
    CASE
                WHEN classify2 LIKE '%%非公开%%' THEN '私募'
                ELSE '公募'
            END AS 发行方式,
    CASE
                WHEN classify2 LIKE '%%可续期%%' THEN '是'
                ELSE '否'
            END AS 是否永续,
    CASE WHEN classify2 LIKE '%%次级可续期%%' THEN '是' ELSE '否' END AS 是否次级,
    SUBSTRING(
                REPLACE(classify2, '＋', '+'),
                LOCATE('(', REPLACE(classify2, '＋', '+')) + 1,
                CHAR_LENGTH(classify2) - LOCATE('(',
                            REPLACE(classify2, '＋', '+')) - 1
            ) AS 隐含评级,
    t.term as 曲线期限
    FROM bond.basicinfo_curve A
	CROSS JOIN yq.目标期限 t
    WHERE (A.classify2 LIKE '%%中债%%' AND A.classify2 LIKE '%%城投债%%') or (A.classify2 LIKE '%%中债%%' AND (A.classify2 LIKE '%%产业%%' or A.classify2 LIKE '%%企业%%'))
"""
with sql_engine.begin() as _cursor:
    df = pd.read_sql(sql, _cursor)
    df.to_sql('曲线全样本', _cursor, if_exists='replace', index=False)
