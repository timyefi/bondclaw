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

# 读取已标注的下行周期
cycles = pd.read_csv('收益率下行周期标注.csv')
print("\n已标注的下行周期：")
print(cycles)

# 定义债券分类
RATE_BONDS = ['国债', '国开', '口行', '农发', '地方债']
FINANCE_BONDS = ['存单', '普通金融债', '二永']
CREDIT_BONDS = ['城投', '产业']

# 定义期限分类
TERMS = {
    '短期': '0-1',
    '中短期': '1-3',
    '中长期': '3-5',
    '长期': '5-10'
}

# 定义评级序列
RATING_FINANCE = ['AAA', 'AA+', 'AA', 'AA-']
RATING_CHENGTOU = ['AAA', 'AA+', 'AA', 'AA(2)', 'AA-']
RATING_INDUSTRY = ['AAA', 'AA+', 'AA', 'AA-']

def get_bond_data(start_date, end_date, bond_type, term=None, rating=None):
    """获取指定条件的债券收益率数据"""
    # 构建基础查询
    query = f"""
    SELECT 
        A.dt,
        A.CLOSE AS yield_rate,
        LEFT(SUBSTRING_INDEX(B.SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(B.SEC_NAME, ':', -1)) - 1) * (
            (RIGHT(B.SEC_NAME, 1) = '天') / 365 + (RIGHT(B.SEC_NAME, 1) = '月') / 12 + (RIGHT(B.SEC_NAME, 1) = '年')
        ) AS term_years,
        B.classify2,
        B.SEC_NAME
    FROM bond.marketinfo_curve A
    INNER JOIN bond.basicinfo_curve B
    ON A.trade_code = B.TRADE_CODE
    WHERE A.dt BETWEEN '{start_date}' AND '{end_date}'
    """
    
    # 根据债券类型添加条件
    if bond_type == '国债':
        query += " AND B.classify2 = '中债国债到期收益率'"
    elif bond_type == '国开':
        query += " AND B.classify2 = '中债国开债到期收益率'"
    elif bond_type == '口行':
        query += " AND B.classify2 = '中债进出口行债到期收益率'"
    elif bond_type == '农发':
        query += " AND B.classify2 = '中债农发行债到期收益率'"
    elif bond_type == '地方债':
        query += " AND B.classify2 = '财政部-中国地方政府债券收益率'"
    elif bond_type == '城投':
        query += " AND B.classify2 LIKE '中债城投债到期收益率%%'"
    elif bond_type == '产业':
        query += " AND B.classify2 LIKE '银行间产业债到期收益率%%'"
    elif bond_type == '普通金融债':
        query += " AND B.classify2 LIKE '中债商业银行普通债到期收益率%%'"
    elif bond_type == '二永':
        query += " AND B.classify2 LIKE '中债商业银行二级资本债到期收益率%%'"
    elif bond_type == '存单':
        query += " AND B.classify2 LIKE '中债商业银行同业存单到期收益率%%'"

    # 添加评级条件
    if rating:
        query += f" AND B.classify2 LIKE '%%({rating})%%'"

    query += " ORDER BY A.dt"
    
    # 获取数据
    df = pd.read_sql(query, sql_engine)
    
    # 根据期限分类数据
    if term:
        if term == '0-1':
            df = df[df['term_years'] <= 1]
        elif term == '1-3':
            df = df[(df['term_years'] > 1) & (df['term_years'] <= 3)]
        elif term == '3-5':
            df = df[(df['term_years'] > 3) & (df['term_years'] <= 5)]
        elif term == '5-10':
            df = df[(df['term_years'] > 5) & (df['term_years'] <= 10)]
        elif term == '超长期':
            df = df[df['term_years'] > 20]  # 超长期定义为20年以上
    
    return df if not df.empty else pd.DataFrame()

def get_all_bond_data(cycle_id, start_date, end_date):
    """获取某个周期内所有类型债券的收益率数据"""
    all_data = []
    
    # 1. 获取利率债数据
    for bond_type in RATE_BONDS:
        # 常规期限
        for term_name, term_value in TERMS.items():
            df = get_bond_data(start_date, end_date, bond_type, term=term_value)
            if not df.empty:
                df['bond_type'] = bond_type
                df['term'] = term_name
                df['rating'] = 'NA'
                all_data.append(df)
        
        # 超长期（仅国债和地方债）
        if bond_type in ['国债', '地方债']:
            df = get_bond_data(start_date, end_date, bond_type, term='超长期')
            if not df.empty:
                df['bond_type'] = bond_type
                df['term'] = '超长期'
                df['rating'] = 'NA'
                all_data.append(df)
    
    # 2. 获取金融债数据
    for bond_type in FINANCE_BONDS:
        for term_name, term_value in TERMS.items():
            for rating in RATING_FINANCE:
                df = get_bond_data(start_date, end_date, bond_type, term=term_value, rating=rating)
                if not df.empty:
                    df['bond_type'] = bond_type
                    df['term'] = term_name
                    df['rating'] = rating
                    all_data.append(df)
    
    # 3. 获取信用债数据
    for bond_type in CREDIT_BONDS:
        for term_name, term_value in TERMS.items():
            ratings = RATING_CHENGTOU if bond_type == '城投' else RATING_INDUSTRY
            for rating in ratings:
                df = get_bond_data(start_date, end_date, bond_type, term=term_value, rating=rating)
                if not df.empty:
                    df['bond_type'] = bond_type
                    df['term'] = term_name
                    df['rating'] = rating
                    all_data.append(df)
    
    # 合并所有数据
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        # 按日期、债券类型、期限和评级分组求均值
        combined_data = combined_data.groupby(['dt', 'bond_type', 'term', 'rating'])['yield_rate'].mean().reset_index()
        combined_data['cycle_id'] = cycle_id
        return combined_data
    return pd.DataFrame()

# 获取所有周期的数据
all_cycles_data = []
for _, cycle in cycles.iterrows():
    print(f"\n处理周期 {cycle['cycle']}: {cycle['start_date']} - {cycle['end_date']}")
    cycle_data = get_all_bond_data(
        cycle_id=cycle['cycle'],
        start_date=cycle['start_date'],
        end_date=cycle['end_date']
    )
    if not cycle_data.empty:
        all_cycles_data.append(cycle_data)

# 合并所有周期数据
if all_cycles_data:
    final_data = pd.concat(all_cycles_data, ignore_index=True)
    
    # 保存数据
    final_data.to_csv('债券收益率数据.csv', index=False, encoding='utf-8-sig')
    print("\n数据已保存到'债券收益率数据.csv'")
    
    # 显示数据统计信息
    print("\n数据统计：")
    print(f"总记录数：{len(final_data)}")
    print("\n按债券类型统计：")
    print(final_data.groupby('bond_type').size())
    print("\n按期限统计：")
    print(final_data.groupby('term').size())
    print("\n按评级统计：")
    print(final_data.groupby('rating').size()) 