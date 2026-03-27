#内部数据库取数
import pandas as pd
import sqlalchemy
from datetime import datetime, date, timedelta, time
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine.connect()
_cursor_pg='postgresql://postgres:hzinsights2015@139.224.107.113:18032/tsdb'

sql="Truncate bond.债券分类"
_cursor.execute(text(sql))
_cursor.commit()
sql=f"""INSERT ignore INTO bond.债券分类 (trade_code,大类,子类)
		SELECT
			trade_code,
			CASE
				WHEN ths_is_city_invest_debt_yy_bond='否' THEN '产业'
				else '城投' end as 大类,
			CASE
				WHEN ths_is_city_invest_debt_yy_bond='否' THEN CASE
					WHEN ths_object_the_sw_bond LIKE '%%银行%%' THEN '' 
					WHEN ths_object_the_sw_bond LIKE '%%证券%%' THEN '非银金融--多元金融--其他多元金融'
					WHEN ths_object_the_sw_bond LIKE '%%保险%%' THEN '非银金融--多元金融--其他多元金融'
					ELSE ths_object_the_sw_bond 
				END
				else ths_urban_platform_area_bond end as 子类
			FROM bond.basicinfo_credit
			WHERE ths_object_the_sw_bond not IN ('银行--其他银行Ⅱ--其他银行Ⅲ','银行--银行--银行','银行--城商行Ⅱ--城商行Ⅲ')
			"""
_cursor.execute(text(sql))
_cursor.commit()
sql=f"""INSERT ignore INTO bond.债券分类 (trade_code,大类,子类)
			SELECT
			trade_code,
			'金融' as 大类,
			'银行' as 子类
			FROM bond.basicinfo_credit
			WHERE ths_object_the_sw_bond IN ('银行--其他银行Ⅱ--其他银行Ⅲ','银行--银行--银行','银行--城商行Ⅱ--城商行Ⅲ')
			"""
_cursor.execute(text(sql))
_cursor.commit()
sql=f"""INSERT ignore INTO bond.债券分类 (trade_code,大类,子类)				
			SELECT
			trade_code,
			'金融' as 大类,
			CASE
				WHEN ths_org_type_bond LIKE '%%银行%%' THEN '银行'
				WHEN ths_org_type_bond LIKE '%%证券公司%%' THEN '证券公司'
				WHEN ths_org_type_bond LIKE '%%保险%%' THEN '保险' 
				WHEN ths_ths_bond_third_type_bond = '其他非银金融机构债' THEN '其他'       
			END as 子类
			FROM bond.basicinfo_finance"""
_cursor.execute(text(sql))
_cursor.commit()
df=pd.read_sql("""SELECT
trade_code,
'ABS' as 大类,
abs类型 as 子类
from 债券新分类
where abs类型 is not null and abs类型 !=''
""",_cursor_pg)
df.to_sql('债券分类',_cursor,if_exists='append',index=False)


# 定义所有需要查询的表名
table_names = ['bond.marketinfo_credit', 'bond.marketinfo_finance', 'bond.marketinfo_abs']

# 对每个表名执行查询
for table_name in table_names:
	query = f"""
		UPDATE 
		bond.`债券分类`
		INNER JOIN 
		(
			SELECT 
				mc.trade_code, 
				mc.ths_cb_market_implicit_rating_bond
			FROM 
				{table_name} mc
			JOIN 
				(
				SELECT 
					trade_code, 
					MAX(dt) as max_dt
				FROM 
					{table_name}
				WHERE 
					ths_cb_market_implicit_rating_bond is not null
					and ths_cb_market_implicit_rating_bond !='0'        
				GROUP BY 
					trade_code
				) subq
			ON 
				mc.trade_code = subq.trade_code 
				AND mc.dt = subq.max_dt
		) AS derived_table
		ON 
			bond.`债券分类`.trade_code = derived_table.trade_code
		SET 
			bond.`债券分类`.评级 = derived_table.ths_cb_market_implicit_rating_bond
		"""
	_cursor.execute(text(query))
	_cursor.commit()


sql=f"""
	insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select DT,trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
            else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_credit
	where ths_bond_balance_bond>0
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
_cursor.execute(text(sql))
_cursor.commit()
sql=f"""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""CREATE TEMPORARY TABLE temp_table AS
SELECT 
		A.dt,
	B.trade_code,
	CASE
		WHEN B.ths_bond_maturity_theory_bond LIKE '%(%)%' 
			AND SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) REGEXP '^[0-9]+$' 
			AND DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365 >= 0 THEN
			DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365
		ELSE
			DATEDIFF(B.ths_maturity_date_bond, A.DT) / 365
	END AS new_duration
FROM 
	marketinfo3 A
JOIN 
	basicinfo_credit B
ON 
	A.trade_code = B.trade_code
WHERE 
	A.久期 is null;
UPDATE 
marketinfo3 A
JOIN 
	temp_table T
ON 
	A.trade_code = T.trade_code
		and A.dt=T.dt
SET 
	A.久期 = T.new_duration
WHERE 
	A.久期 is null;
"""
_cursor.execute(text(sql))
_cursor.commit()

sql="""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期) 
	select DT,trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
			else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_finance
	where ths_bond_balance_bond>0
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""CREATE TEMPORARY TABLE temp_table AS
SELECT 
		A.dt,
	B.trade_code,
	CASE
		WHEN B.ths_bond_maturity_theory_bond LIKE '%(%)%' 
			AND SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) REGEXP '^[0-9]+$' 
			AND DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365 >= 0 THEN
			DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365
		ELSE
			DATEDIFF(B.ths_maturity_date_bond, A.DT) / 365
	END AS new_duration
FROM 
	marketinfo3 A
JOIN 
	basicinfo_finance B
ON 
	A.trade_code = B.trade_code
WHERE 
	A.久期 is null;"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""
UPDATE 
marketinfo3 A
JOIN 
	temp_table T
ON 
	A.trade_code = T.trade_code
		and A.dt=T.dt
SET 
	A.久期 = T.new_duration
WHERE 
	A.久期 is null;
"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select DT,trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
			else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_abs
	where ths_bond_balance_bond>0
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""CREATE TEMPORARY TABLE temp_table AS
SELECT 
		A.dt,
	B.trade_code,
	CASE
		WHEN B.ths_bond_maturity_theory_bond LIKE '%(%)%' 
			AND SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) REGEXP '^[0-9]+$' 
			AND DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365 >= 0 THEN
			DATEDIFF(DATE_ADD(B.ths_interest_begin_date_bond, INTERVAL CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(B.ths_bond_maturity_theory_bond, '(', -1), '+', 1) AS UNSIGNED) YEAR), A.DT) / 365
		ELSE
			DATEDIFF(B.ths_maturity_date_bond, A.DT) / 365
	END AS new_duration
FROM 
	marketinfo3 A
JOIN 
	basicinfo_abs B
ON 
	A.trade_code = B.trade_code
WHERE 
	A.久期 is null;"""
_cursor.execute(text(sql))
_cursor.commit()
sql="""
UPDATE 
marketinfo3 A
JOIN 
	temp_table T
ON 
	A.trade_code = T.trade_code
		and A.dt=T.dt
SET 
	A.久期 = T.new_duration
WHERE 
	A.久期 is null;
"""
_cursor.execute(text(sql))
_cursor.commit()

queries = [
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT DT, '全部' as 分类,'' AS 子类, '大类' as 分类方式,SUM(ths_bond_balance_bond) as 余额
FROM bond.marketinfo3
where 久期 is not null
GROUP BY DT
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, B.大类 as 分类,'' AS 子类, '大类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
where A.久期 is not null
GROUP BY A.DT,B.大类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '城投' as 分类, C.省 AS 子类,'省' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
INNER JOIN bond.basicinfo_xzqh_ct C ON B.子类=C.`城投区域`
WHERE B.大类='城投' AND C.`省` is not null and C.`省` != ''
and A.久期 is not null
GROUP BY A.DT,C.省
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '城投' as 分类, C.市 AS 子类, '市' as 分类方式,SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
INNER JOIN bond.basicinfo_xzqh_ct C ON B.子类=C.`城投区域`
WHERE B.大类='城投' AND C.`市` is not null and C.`市` != ''
and A.久期 is not null
GROUP BY A.DT,C.市
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '产业' as 分类, C.申万一级 AS 子类,'申万一级' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
WHERE B.大类='产业' AND C.`申万一级` is not null and C.`申万一级` != ''
and A.久期 is not null
GROUP BY A.DT,C.申万一级
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '产业' as 分类, B.子类,'申万行业' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
WHERE B.大类='产业'
and A.久期 is not null
GROUP BY A.DT,B.子类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '产业' as 分类, C.一级分类 AS 子类,'一级分类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
WHERE B.大类='产业' AND C.`一级分类` is not null and C.`一级分类` != ''
and A.久期 is not null
GROUP BY A.DT,C.一级分类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '产业' as 分类, C.二级分类 AS 子类,'二级分类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
WHERE B.大类='产业' AND C.`二级分类` is not null and C.`二级分类` != ''
and A.久期 is not null
GROUP BY A.DT,C.二级分类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '金融' as 分类,B.子类 AS 子类,'金融机构' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
WHERE B.`大类`='金融' AND B.子类 is not null and B.子类 != ''
and A.久期 is not null
GROUP BY A.DT,B.子类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, 'ABS' as 分类,B.子类 AS 子类,'资产' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
WHERE B.大类='ABS' AND B.子类 is not null and B.子类 != ''
and A.久期 is not null
GROUP BY A.DT,B.子类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, '全部' as 分类,B.评级 AS 子类, '评级' as 分类方式,SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
where A.久期 is not null
GROUP BY A.DT,B.评级
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, B.`大类` as 分类,B.评级 AS 子类, '评级' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
WHERE A.久期 is not null
GROUP BY A.DT,B.`大类`,B.评级
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT DT, '全部' as 分类,
case when 久期<0.75 then 0.5
	when 久期<1.5 then 1
	when 久期<2.5 then 2
	when 久期<3.5 then 3
	when 久期<4.5 then 4
	when 久期<6 then 5
	when 久期<8 then 7
	else 10 end AS 子类, '久期' as 分类方式,SUM(ths_bond_balance_bond) as 余额
FROM bond.marketinfo3
where 久期 is not null
GROUP BY DT,子类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
""",
f"""
INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
SELECT A.DT, B.`大类` as 分类,
case when 久期<0.75 then 0.5
	when 久期<1.5 then 1
	when 久期<2.5 then 2
	when 久期<3.5 then 3
	when 久期<4.5 then 4
	when 久期<6 then 5
	when 久期<8 then 7
	else 10 end AS 子类, '久期' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
FROM bond.marketinfo3 A
INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
WHERE 久期 is not null
GROUP BY A.DT,B.`大类`,子类
ON DUPLICATE KEY UPDATE 
    余额 = VALUES(余额)
"""
]
for query in queries:
	_cursor.execute(text(query))
	_cursor.commit()
