import pandas as pd
import numpy as np
import sqlalchemy
import psycopg2
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BondIndexDailyUpdate:
    def __init__(self):
        # MySQL数据库连接 (bond数据库)
        self.sql_engine = sqlalchemy.create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s' % (
                'hz_work',
                'Hzinsights2015',
                'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                '3306',
                'bond',
            ), poolclass=sqlalchemy.pool.NullPool
        )
        
        # PostgreSQL数据库连接 (tsdb数据库)
        self.pg_conn = psycopg2.connect(
            host="139.224.201.106",
            port=18032,
            user="postgres",
            password="hzinsights2015",
            database="tsdb"
        )
        
        # 创建指数存储表
        self.create_index_table()
        
        # 创建指数构成存储表
        self.create_index_constituents_table()
        
    def create_index_table(self):
        """创建指数存储表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bond_indices (
            dt DATE NOT NULL,
            index_code VARCHAR(100) NOT NULL,
            index_value DOUBLE NOT NULL,
            index_type VARCHAR(20) NOT NULL,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (dt, index_code),
            INDEX idx_dt (dt),
            INDEX idx_code (index_code),
            INDEX idx_type (index_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
        """
        
        try:
            with self.sql_engine.connect() as conn:
                conn.execute(sqlalchemy.text(create_table_sql))
                print("Index table created or already exists")
        except Exception as e:
            print(f"Error creating table: {str(e)}")
    
    def create_index_constituents_table(self):
        """创建指数构成存储表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bond_index_constituents (
            dt DATE NOT NULL,
            trade_code VARCHAR(20) NOT NULL,
            index_code VARCHAR(100) NOT NULL,
            PRIMARY KEY (dt, trade_code,index_code),
            INDEX idx_dt (dt),
            INDEX idx_trade_code (trade_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
        """
        
        try:
            with self.sql_engine.connect() as conn:
                conn.execute(sqlalchemy.text(create_table_sql))
                print("Index constituents table created or already exists")
        except Exception as e:
            print(f"Error creating constituents table: {str(e)}")
    
    def get_bond_classification(self):
        """获取债券分类信息"""
        print("Getting bond classification...")
        
        # 获取信用债列表
        credit_query = """
        SELECT trade_code
        FROM basicinfo_credit
        WHERE ths_is_issuing_failure_bond != '是'
        """
        
        # 获取金融债列表  
        finance_query = """
        SELECT trade_code
        FROM basicinfo_finance
        WHERE ths_is_issuing_failure_bond != '是'
        """
        
        credit_bonds = pd.read_sql(credit_query, self.pg_conn)
        finance_bonds = pd.read_sql(finance_query, self.pg_conn)
        
        return credit_bonds['trade_code'].tolist(), finance_bonds['trade_code'].tolist()
    
    def get_yield_data_for_date(self, target_date):
        """获取特定日期的收益率数据"""
        print(f"Getting yield data for {target_date}...")
        
        query = f"""
        SELECT dt, trade_code, stdyield, balance
        FROM hzcurve_credit
        WHERE dt = '{target_date}'
        AND target_term = 3
        AND stdyield IS NOT NULL
        ORDER BY stdyield DESC
        """
        
        yield_data = pd.read_sql(query, self.pg_conn)
        
        if yield_data.empty:
            print(f"No data found for {target_date}")
            return pd.DataFrame()
        
        # 获取债券分类
        credit_bonds, finance_bonds = self.get_bond_classification()
        
        # 标记债券类型
        yield_data['bond_type'] = 'unknown'
        yield_data.loc[yield_data['trade_code'].isin(credit_bonds), 'bond_type'] = 'credit'
        yield_data.loc[yield_data['trade_code'].isin(finance_bonds), 'bond_type'] = 'finance'
        
        # 移除未分类的债券
        yield_data = yield_data[yield_data['bond_type'] != 'unknown']
        
        return yield_data
    
    def create_percentile_groups_for_date(self, yield_data, target_date):
        """为特定日期创建分位数分组"""
        print(f"Creating percentile groups for {target_date}...")
        
        grouped_data = []
        
        for bond_type in ['credit', 'finance']:
            type_data = yield_data[yield_data['bond_type'] == bond_type].copy()
            
            if len(type_data) == 0:
                continue
            
            # 按收益率降序排列
            type_data = type_data.sort_values('stdyield', ascending=True)
            
            # 计算分位数
            n_bonds = len(type_data)
            
            for i in range(10):
                start_pct = i * 10
                end_pct = (i + 1) * 10
                
                start_idx = int(n_bonds * start_pct / 100)
                end_idx = int(n_bonds * end_pct / 100)
                
                if start_idx >= n_bonds:
                    continue
                if end_idx > n_bonds:
                    end_idx = n_bonds
                
                group_data = type_data.iloc[start_idx:end_idx]
                
                if len(group_data) > 0:
                    for _, row in group_data.iterrows():
                        grouped_data.append({
                            'dt': target_date,
                            'trade_code': row['trade_code'],
                            'bond_type': bond_type,
                            'percentile_group': f"{start_pct}-{end_pct}",
                            'stdyield': row['stdyield'],
                            'balance': row['balance']
                        })
        
        return pd.DataFrame(grouped_data)
    
    def get_price_data_for_date(self, grouped_data, bond_type, target_date):
        """获取特定日期的价格数据"""
        print(f"Getting price data for {bond_type} on {target_date}...")
        
        trade_codes = grouped_data[grouped_data['bond_type'] == bond_type]['trade_code'].unique()
        
        if len(trade_codes) == 0:
            return pd.DataFrame()
        
        # 构建查询条件
        table_name = 'marketinfo_credit' if bond_type == 'credit' else 'marketinfo_finance'
        
        # 分批查询以避免SQL语句过长
        batch_size = 100
        all_price_data = []
        
        for i in range(0, len(trade_codes), batch_size):
            batch_codes = trade_codes[i:i+batch_size]
            # 直接构建SQL，避免参数化查询的问题
            code_list = "','".join([str(code) for code in batch_codes])
            
            query = f"""
            SELECT DT, TRADE_CODE, ths_bond_balance_bond, 
                   ths_valuate_full_price_cb_bond, ths_evaluate_net_price_cb_bond
            FROM {table_name}
            WHERE TRADE_CODE IN ('{code_list}')
            AND DT = '{target_date}'
            AND ths_bond_balance_bond IS NOT NULL
            AND ths_valuate_full_price_cb_bond IS NOT NULL
            AND ths_evaluate_net_price_cb_bond IS NOT NULL
            """
            
            batch_data = pd.read_sql(query, self.sql_engine)
            all_price_data.append(batch_data)
        
        if all_price_data:
            price_data = pd.concat(all_price_data, ignore_index=True)
            price_data.columns = ['dt', 'trade_code', 'balance', 'full_price', 'net_price']
            return price_data
        else:
            return pd.DataFrame()
    
    def calculate_indices_for_date(self, grouped_data, target_date):
        """计算特定日期的指数"""
        print(f"Calculating indices for {target_date}...")
        
        all_indices = []
        all_constituents = []
        
        for bond_type in ['credit', 'finance']:
            # 获取价格数据
            price_data = self.get_price_data_for_date(grouped_data, bond_type, target_date)
            
            if price_data.empty:
                continue
            
            # 合并分组数据和价格数据，重命名price_data的balance字段以避免冲突
            price_data_renamed = price_data.rename(columns={'balance': 'bond_balance'})
            merged_data = grouped_data[grouped_data['bond_type'] == bond_type].merge(
                price_data_renamed, on=['dt', 'trade_code'], how='inner'
            )
            
            for percentile_group in merged_data['percentile_group'].unique():
                group_data = merged_data[merged_data['percentile_group'] == percentile_group]
                
                if group_data['bond_balance'].sum() == 0:
                    continue
                
                # 计算加权平均
                weights = group_data['bond_balance'] / group_data['bond_balance'].sum()
                
                full_price_index = (group_data['full_price'] * weights).sum()
                net_price_index = (group_data['net_price'] * weights).sum()
                
                # 保存指数数据
                full_index_code = f"{bond_type.title()}_{percentile_group}_Full"
                net_index_code = f"{bond_type.title()}_{percentile_group}_Net"
                
                all_indices.append({
                    'dt': target_date,
                    'index_code': full_index_code,
                    'index_value': full_price_index,
                    'index_type': 'full_price'
                })
                
                all_indices.append({
                    'dt': target_date,
                    'index_code': net_index_code,
                    'index_value': net_price_index,
                    'index_type': 'net_price'
                })
                
                # 保存构成数据
                for idx, row in group_data.iterrows():
                    weight = weights.loc[idx]
                    
                    # 对于每个证券，添加到全价指数和净价指数的构成中
                    all_constituents.append({
                        'dt': target_date,
                        'trade_code': row['trade_code'],
                        'index_code': full_index_code
                    })
                    
                    all_constituents.append({
                        'dt': target_date,
                        'trade_code': row['trade_code'],
                        'index_code': net_index_code
                    })
        
        return pd.DataFrame(all_indices), pd.DataFrame(all_constituents)
    
    def save_indices_to_db(self, indices_data):
        """保存指数数据到数据库"""
        if indices_data.empty:
            print("No indices to save")
            return
        
        print(f"Saving {len(indices_data)} index records to database...")
        
        try:
            target_date = str(indices_data['dt'].iloc[0])
            
            with self.sql_engine.connect() as conn:
                # 先清理当天数据
                delete_sql = """
                DELETE FROM bond_indices 
                WHERE dt = :dt
                """
                conn.execute(
                    sqlalchemy.text(delete_sql),
                    {'dt': target_date}
                )
                
                # 批量插入新数据 - 使用pandas to_sql方法
                indices_data.to_sql(
                    name='bond_indices',
                    con=self.sql_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )
                
            print("Indices saved successfully")
        except Exception as e:
            print(f"Error saving indices: {str(e)}")
    
    def save_constituents_to_db(self, constituents_data):
        """保存指数构成数据到数据库"""
        if constituents_data.empty:
            print("No constituents to save")
            return
        
        print(f"Saving {len(constituents_data)} constituent records to database...")
        
        try:
            target_date = str(constituents_data['dt'].iloc[0])
            
            with self.sql_engine.connect() as conn:
                # 先清理当天数据
                delete_sql = """
                DELETE FROM bond_index_constituents 
                WHERE dt = :dt
                """
                conn.execute(
                    sqlalchemy.text(delete_sql),
                    {'dt': target_date}
                )
                
                # 批量插入新数据 - 使用pandas to_sql方法
                constituents_data.to_sql(
                    name='bond_index_constituents',
                    con=self.sql_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=5000
                )
                
            print("Constituents saved successfully")
        except Exception as e:
            print(f"Error saving constituents: {str(e)}")
    
    def get_latest_index_date(self):
        """获取数据库中最新的指数日期"""
        try:
            query = "SELECT MAX(dt) as latest_date FROM bond_indices"
            result = pd.read_sql(query, self.sql_engine)
            latest_date = result['latest_date'].iloc[0]
            return latest_date
        except Exception as e:
            print(f"Error getting latest index date: {str(e)}")
            return None
    
    def get_available_dates_from_yield_data(self, start_date=None, end_date=None):
        """获取收益率数据中可用的日期"""
        date_filter = ""
        if start_date and end_date:
            date_filter = f"WHERE dt >= '{start_date}' AND dt <= '{end_date}'"
        elif start_date:
            date_filter = f"WHERE dt >= '{start_date}'"
        elif end_date:
            date_filter = f"WHERE dt <= '{end_date}'"
        
        query = f"""
        SELECT DISTINCT dt
        FROM hzcurve_credit
        {date_filter}
        {'AND' if date_filter else 'WHERE'} target_term = 3
        AND stdyield IS NOT NULL
        ORDER BY dt
        """
        
        dates = pd.read_sql(query, self.pg_conn)
        return dates['dt'].tolist()
    
    def update_daily_indices(self, target_date=None):
        """更新日指数"""
        if target_date is None:
            target_date = datetime.now().date() - timedelta(days=1)  # 前一个工作日
        
        print(f"Updating indices for {target_date}...")
        
        try:
            # 获取收益率数据
            yield_data = self.get_yield_data_for_date(target_date)
            
            if yield_data.empty:
                print(f"No yield data available for {target_date}")
                return False
            
            # 创建分位数分组
            grouped_data = self.create_percentile_groups_for_date(yield_data, target_date)
            
            if grouped_data.empty:
                print(f"No grouped data created for {target_date}")
                return False
            
            # 计算指数
            indices_data, constituents_data = self.calculate_indices_for_date(grouped_data, target_date)
            
            if indices_data.empty:
                print(f"No indices calculated for {target_date}")
                return False
            
            # 保存到数据库
            self.save_indices_to_db(indices_data)
            self.save_constituents_to_db(constituents_data)
            
            print(f"Successfully updated {len(indices_data)} indices and {len(constituents_data)} constituents for {target_date}")
            return True
            
        except Exception as e:
            print(f"Error updating indices for {target_date}: {str(e)}")
            return False
    
    def backfill_historical_indices(self, start_date=None, end_date=None):
        """补充历史指数数据"""
        print("Starting historical index backfill...")
        
        # 获取可用日期
        available_dates = self.get_available_dates_from_yield_data(start_date, end_date)
        
        if not available_dates:
            print("No available dates for backfill")
            return
        
        print(f"Found {len(available_dates)} dates to process")
        
        success_count = 0
        error_count = 0
        
        for date in available_dates:
            print(f"\nProcessing {date}...")
            try:
                if self.update_daily_indices(date):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"Error processing {date}: {str(e)}")
                error_count += 1
        
        print(f"\nBackfill completed:")
        print(f"  Successful: {success_count}")
        print(f"  Errors: {error_count}")
    
    def get_index_summary(self):
        """获取指数数据概要"""
        try:
            query = """
            SELECT 
                MIN(dt) as start_date,
                MAX(dt) as end_date,
                COUNT(DISTINCT dt) as date_count,
                COUNT(DISTINCT index_code) as index_count,
                COUNT(*) as total_records
            FROM bond_indices
            """
            
            summary = pd.read_sql(query, self.sql_engine)
            return summary
        except Exception as e:
            print(f"Error getting index summary: {str(e)}")
            return None
    
    def get_constituents_summary(self):
        """获取指数构成数据概要"""
        try:
            query = """
            SELECT 
                MIN(dt) as start_date,
                MAX(dt) as end_date,
                COUNT(DISTINCT dt) as date_count,
                COUNT(DISTINCT index_code) as index_count,
                COUNT(DISTINCT trade_code) as bond_count,
                COUNT(*) as total_records
            FROM bond_index_constituents
            """
            
            summary = pd.read_sql(query, self.sql_engine)
            return summary
        except Exception as e:
            print(f"Error getting constituents summary: {str(e)}")
            return None
    
    def get_index_constituents(self, target_date, index_code=None):
        """获取特定日期的指数构成"""
        try:
            where_clause = f"WHERE dt = '{target_date}'"
            if index_code:
                where_clause += f" AND index_code = '{index_code}'"
            
            query = f"""
            SELECT dt, trade_code, index_code
            FROM bond_index_constituents
            {where_clause}
            ORDER BY index_code, trade_code
            """
            
            constituents = pd.read_sql(query, self.sql_engine)
            return constituents
        except Exception as e:
            print(f"Error getting index constituents: {str(e)}")
            return None
    
    def close_connections(self):
        """关闭数据库连接"""
        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()

# 主程序
if __name__ == "__main__":
    # 创建更新系统
    updater = BondIndexDailyUpdate()
    
    try:
        # 显示当前指数概要
        summary = updater.get_index_summary()
        if summary is not None and not summary.empty:
            print("Current Index Summary:")
            print(summary.to_string(index=False))
        else:
            print("No existing indices found")
        
        # 显示构成数据概要
        constituents_summary = updater.get_constituents_summary()
        if constituents_summary is not None and not constituents_summary.empty:
            print("\nCurrent Constituents Summary:")
            print(constituents_summary.to_string(index=False))
        else:
            print("No existing constituents found")
        
        # 选择运行模式
        import sys
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == 'daily':
                # 每日更新模式
                target_date = None
                if len(sys.argv) > 2:
                    target_date = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
                
                updater.update_daily_indices(target_date)
                
            elif mode == 'backfill':
                # 历史数据补充模式
                start_date = sys.argv[2] if len(sys.argv) > 2 else None
                end_date = sys.argv[3] if len(sys.argv) > 3 else None
                
                updater.backfill_historical_indices(start_date, end_date)
                
            else:
                print("Unknown mode. Use 'daily' or 'backfill'")
        else:
            # 默认：更新昨天的数据
            print("\nRunning daily update for yesterday...")
            updater.update_daily_indices()
            
    finally:
        updater.close_connections()
    
    print("\nUsage examples:")
    print("  python bond_system_2.py daily                    # Update for yesterday")
    print("  python bond_system_2.py daily 2024-01-15        # Update for specific date")
    print("  python bond_system_2.py backfill                # Backfill all available data")
    print("  python bond_system_2.py backfill 2023-01-01     # Backfill from date")
    print("  python bond_system_2.py backfill 2023-01-01 2023-12-31  # Backfill date range") 
    print("\nTo query index constituents in Python:")
    print("  from 2_daily_bond_index_update import BondIndexDailyUpdate")
    print("  updater = BondIndexDailyUpdate()")
    print("  constituents = updater.get_index_constituents('2024-01-15')")
    print("  specific_index = updater.get_index_constituents('2024-01-15', 'Credit_0-10_Full')") 