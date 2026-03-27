#内部数据库取数
import pandas as pd
import sqlalchemy
from datetime import datetime, date, timedelta, time
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def log_progress(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

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

log_progress("开始处理信用债数据...")

with sql_engine.connect() as conn:
    sql="""select distinct dt from bond.marketinfo_abs
    where dt not in (select distinct dt from bond.marketinfo3 where `ths_bond_balance_bond` is not null)"""
    dt_list=pd.read_sql(sql,conn)
    dt_list=dt_list['dt'].tolist()

# 添加检查dt_list是否为空的逻辑
if not dt_list:
    log_progress("没有新的数据需要处理")
else:
    sql=f"""
	insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select DT,A.trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
            else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_credit A
	inner join basicinfo_all B on A.trade_code=B.trade_code
	where ths_bond_balance_bond>0
    and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
    with sql_engine.connect() as conn:
        conn.execute(text(sql))

sql="""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select A.DT,A.trade_code,A.ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
			else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_credit A
	inner join basicinfo_all B on A.trade_code=B.trade_code
	inner join marketinfo3 C on A.trade_code=C.trade_code and A.dt=C.dt
	where A.ths_bond_balance_bond>0
	and (C.ths_bond_balance_bond is NULL or C.久期 is NULL)
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
log_progress("完成信用债基础数据插入")

sql=f"""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
log_progress("完成信用债久期临时表创建")
sql1="""CREATE TEMPORARY TABLE temp_table AS
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
	A.久期 is null"""

sql2="""
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
	A.久期 is null
"""
with sql_engine.connect() as conn:
	conn.execute(text(sql1))
	conn.execute(text(sql2))
log_progress("开始处理金融债数据...")
# 添加检查dt_list是否为空的逻辑
if not dt_list:
    log_progress("没有新的数据需要处理")
else:
    sql=f"""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期) 
        select DT,A.trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
                else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
        from bond.marketinfo_finance A
        inner join basicinfo_all B on A.trade_code=B.trade_code
        where ths_bond_balance_bond>0
        and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
        ON DUPLICATE KEY UPDATE 
        ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
        久期 = VALUES(久期)
        """
    with sql_engine.connect() as conn:
        conn.execute(text(sql))

sql="""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select A.DT,A.trade_code,A.ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
			else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_finance A
	inner join basicinfo_all B on A.trade_code=B.trade_code
	inner join marketinfo3 C on A.trade_code=C.trade_code and A.dt=C.dt
	where A.ths_bond_balance_bond>0
	and (C.ths_bond_balance_bond is NULL or C.久期 is NULL)
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
log_progress("完成金融债数据插入")
sql="""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
sq11="""CREATE TEMPORARY TABLE temp_table AS
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
	A.久期 is null"""

sql2="""
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
with sql_engine.connect() as conn:
	conn.execute(text(sq11))
	conn.execute(text(sql2))

log_progress("开始处理ABS数据...")
# 添加检查dt_list是否为空的逻辑
if not dt_list:
    log_progress("没有新的数据需要处理")
else:
    sql=f"""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
        select DT,A.trade_code,ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
                else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
        from bond.marketinfo_abs A
        inner join basicinfo_all B on A.trade_code=B.trade_code
        where ths_bond_balance_bond>0
        and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
        ON DUPLICATE KEY UPDATE 
        ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
        久期 = VALUES(久期)
        """
    with sql_engine.connect() as conn:
        conn.execute(text(sql))

sql="""insert into bond.marketinfo3 (DT,trade_code,ths_bond_balance_bond,久期)
	select A.DT,A.trade_code,A.ths_bond_balance_bond,case when ths_evaluate_modified_dur_cb_bond_exercise>0 then ths_evaluate_modified_dur_cb_bond_exercise
			else ths_evaluate_interest_durcb_bond_exercise+ths_evaluate_interest_durcb_bond_exercise end as 久期
	from bond.marketinfo_abs A
	inner join basicinfo_all B on A.trade_code=B.trade_code
	inner join marketinfo3 C on A.trade_code=C.trade_code and A.dt=C.dt
	where A.ths_bond_balance_bond>0
	and (C.ths_bond_balance_bond is NULL or C.久期 is NULL)
	ON DUPLICATE KEY UPDATE 
    ths_bond_balance_bond = VALUES(ths_bond_balance_bond),
    久期 = VALUES(久期)
	"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
log_progress("完成ABS数据插入")
sql="""DROP TEMPORARY TABLE IF EXISTS temp_table;"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
sql1="""CREATE TEMPORARY TABLE temp_table AS
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

sql2="""
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
with sql_engine.connect() as conn:
	conn.execute(text(sql1))
	conn.execute(text(sql2))

sql="""select distinct dt from bond.marketinfo_abs
where dt not in (select distinct dt from bond.marketinfo3 where 隐含评级 is not null)"""
with sql_engine.connect() as conn:
	dt_list=pd.read_sql(sql,conn)
dt_list=dt_list['dt'].tolist()

log_progress("开始处理隐含评级数据...")
# 添加检查dt_list是否为空的逻辑	
if not dt_list:
    log_progress("没有新的数据需要处理")
else:
    sql=f"""
    INSERT INTO bond.marketinfo3 ( dt,trade_code, 隐含评级 ) 
SELECT
A.dt,
A.trade_code,
A.ths_cb_market_implicit_rating_bond AS 隐含评级 
FROM
bond.marketinfo_credit A
inner join basicinfo_all B on A.trade_code=B.trade_code
where A.ths_cb_market_implicit_rating_bond is not null
and A.ths_cb_market_implicit_rating_bond !=''
and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
UNION
SELECT
A.dt,
A.trade_code,
A.ths_cb_market_implicit_rating_bond AS 隐含评级 
FROM
	bond.marketinfo_finance A
	inner join basicinfo_all B on A.trade_code=B.trade_code
where A.ths_cb_market_implicit_rating_bond is not null
and A.ths_cb_market_implicit_rating_bond !=''
and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
UNION
SELECT
A.dt,
A.trade_code,
A.ths_cb_market_implicit_rating_bond AS 隐含评级 
FROM
	bond.marketinfo_abs A
	inner join basicinfo_all B on A.trade_code=B.trade_code
where A.ths_cb_market_implicit_rating_bond is not null
and A.ths_cb_market_implicit_rating_bond !=''
and A.dt in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
on DUPLICATE key UPDATE 隐含评级=VALUES(隐含评级)
"""
    with sql_engine.connect() as conn:
        conn.execute(text(sql))
log_progress("完成隐含评级数据插入")

log_progress("开始处理信用债规模统计...")
sql="""select distinct dt from bond.marketinfo3
where dt not in (select distinct dt from bond.信用债规模)"""
with sql_engine.connect() as conn:
	dt_list=pd.read_sql(sql,conn)
dt_list=dt_list['dt'].tolist()
# 添加检查dt_list是���为空的逻辑
if not dt_list:
    log_progress("没有新的数据需要处理")
else:
    queries = [
    f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT DT, '全部' as 分类,'' AS 子类, '大类' as 分类方式,SUM(ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3
	where 久期 is not null
	and DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY DT
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, B.大类 as 分类,'' AS 子类, '大类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	where A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.大类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '城投' as 分类, C.省 AS 子类,'省' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	INNER JOIN bond.basicinfo_xzqh_ct C ON B.子类=C.`城投区域`
	WHERE B.大类='城投' AND C.`省` is not null and C.`省` != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,C.省
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '城投' as 分类, C.市 AS 子类, '市' as 分类方式,SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	INNER JOIN bond.basicinfo_xzqh_ct C ON B.子类=C.`城投区域`
	WHERE B.大类='城投' AND C.`市` is not null and C.`市` != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,C.市
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '产业' as 分类, C.申万一级 AS 子类,'申万一级' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
	WHERE B.大类='产业' AND C.`申万一级` is not null and C.`申万一级` != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,C.申万一级
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '产业' as 分类, B.子类,'申万行业' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
		WHERE B.大类='产业'
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.子类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '产业' as 分类, C.一级分类 AS 子类,'一级分类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
	WHERE B.大类='产业' AND C.`一级分类` is not null and C.`一级分类` != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,C.一级分类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '产业' as 分类, C.二级分类 AS 子类,'二级分类' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	INNER JOIN bond.basicinfo_industrytype1 C ON B.子类=C.申万行业
	WHERE B.大类='产业' AND C.`二级分类` is not null and C.`二级分类` != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,C.二级分类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '金融' as 分类,B.子类 AS 子类,'金融机构' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	WHERE B.`大类`='金融' AND B.子类 is not null and B.子类 != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.子类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, 'ABS' as 分类,B.子类 AS 子类,'资产' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	WHERE B.大类='ABS' AND B.子类 is not null and B.子类 != ''
	and A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.子类
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, '全部' as 分类,B.外评 AS 子类, '评级' as 分类方式,SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	where A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.外评
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	""",
	f"""
	INSERT INTO bond.信用债规模 (DT, 分类,子类, 分类方式,余额)
	SELECT A.DT, B.`大类` as 分类,B.外评 AS 子类, '评级' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.basicinfo_all B ON A.trade_code=B.trade_code
	WHERE A.久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.`大类`,B.外评
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
		else 10 end AS 子类1, '久期' as 分类方式,SUM(ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3
	where 久期 is not null
	and DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY DT,子类1
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
		else 10 end AS 子类1, '久期' as 分类方式, SUM(A.ths_bond_balance_bond) as 余额
	FROM bond.marketinfo3 A
	INNER JOIN bond.债券分类 B ON A.trade_code=B.trade_code
	WHERE 久期 is not null
	and A.DT in {tuple(dt_list) if len(dt_list) > 1 else f"('{dt_list[0]}')" }
	GROUP BY A.DT,B.`大类`,子类1
	ON DUPLICATE KEY UPDATE 
		余额 = VALUES(余额)
	"""]
    for i, query in enumerate(queries, 1):
        log_progress(f"执行规模统计查询 {i}/{len(queries)}")
        with sql_engine.connect() as conn:
            conn.execute(text(query))
log_progress("完成信用债规模统计")

log_progress("开始清理临时数据...")
sql="""delete from bond.信用债规模
WHERE DT='2023-6-25'
	"""
with sql_engine.connect() as conn:
	conn.execute(text(sql))
log_progress("完成临时数据清理")
log_progress("所有数据处理完成!")