import pandas as pd
import sqlalchemy
import pymysql
from sqlalchemy import text

# 创建数据库连接
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


# 查询数据
query = "SELECT dt, 理财规模 FROM 理财规模"
df = pd.read_sql(query, _cursor)
print(df)

# 将日期列转换为datetime类型
df['dt'] = pd.to_datetime(df['dt']).dt.date

# 设置日期列为索引
df.set_index('dt', inplace=True)

# 生成完整的日期范围
full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')

# 重新索引数据框，填充缺失值
df = df.reindex(full_range).interpolate(method='linear')

# 重置索引
df.reset_index(inplace=True)
df.rename(columns={'index': 'dt'}, inplace=True)
print(df)

# 更新数据库
# 使用INSERT语句逐行插入数据
for _, row in df.iterrows():
    insert_query = text(f"INSERT INTO yq.理财规模 (dt, 理财规模) VALUES (:dt, :规模) on duplicate key update 理财规模=VALUES(理财规模)")
    _cursor.execute(insert_query, {'dt': row['dt'], '规模': row['理财规模']})
# # 修改表结构 - 更正后的代码
# alter_table_query = text("ALTER TABLE 理财规模 MODIFY COLUMN dt DATE PRIMARY KEY")
# _cursor.execute(alter_table_query)
