#!/usr/bin/env python3
"""
从指数构成中随机抽取样本的工具
从 bond_index_constituents 表中为每个指数随机抽取指定数量的证券
"""

import pandas as pd
import numpy as np
import sqlalchemy
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class IndexSampler:
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
        
        # 创建抽样成分表
        self.create_sample_table()
    
    def create_sample_table(self):
        """创建抽样成分存储表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bond_index_sample_constituents (
            dt DATE NOT NULL,
            trade_code VARCHAR(20) NOT NULL,
            index_code VARCHAR(100) NOT NULL,
            sample_size INT NOT NULL,
            PRIMARY KEY (dt, trade_code, index_code),
            INDEX idx_dt (dt),
            INDEX idx_trade_code (trade_code),
            INDEX idx_index_code (index_code),
            INDEX idx_sample_size (sample_size)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
        """
        
        try:
            with self.sql_engine.connect() as conn:
                conn.execute(sqlalchemy.text(create_table_sql))
                print("Sample constituents table created or already exists")
        except Exception as e:
            print(f"Error creating sample table: {str(e)}")
    
    def get_latest_constituents_date(self):
        """获取构成数据中的最新日期"""
        try:
            query = "SELECT MAX(dt) as latest_date FROM bond_index_constituents"
            result = pd.read_sql(query, self.sql_engine)
            latest_date = result['latest_date'].iloc[0]
            return latest_date
        except Exception as e:
            print(f"Error getting latest constituents date: {str(e)}")
            return None
    
    def get_constituents_for_date(self, target_date):
        """获取特定日期的所有指数构成"""
        try:
            query = f"""
            SELECT dt, trade_code, index_code
            FROM bond_index_constituents
            WHERE dt = '{target_date}'
            ORDER BY index_code, trade_code
            """
            
            constituents = pd.read_sql(query, self.sql_engine)
            return constituents
        except Exception as e:
            print(f"Error getting constituents for {target_date}: {str(e)}")
            return pd.DataFrame()
    
    def sample_constituents(self, constituents_data, sample_size=50, random_seed=None):
        """对每个指数的构成进行随机抽样"""
        if random_seed is not None:
            np.random.seed(random_seed)
        
        sampled_data = []
        
        # 按指数分组进行抽样
        for index_code in constituents_data['index_code'].unique():
            index_constituents = constituents_data[constituents_data['index_code'] == index_code]
            
            # 如果成分数量少于抽样数量，全部保留
            if len(index_constituents) <= sample_size:
                sample_constituents = index_constituents.copy()
                actual_sample_size = len(index_constituents)
                print(f"  {index_code}: {len(index_constituents)} constituents (all selected)")
            else:
                # 随机抽样
                sample_constituents = index_constituents.sample(n=sample_size, random_state=random_seed)
                actual_sample_size = sample_size
                print(f"  {index_code}: {sample_size} sampled from {len(index_constituents)} constituents")
            
            # 添加抽样大小信息
            sample_constituents = sample_constituents.copy()
            sample_constituents['sample_size'] = actual_sample_size
            
            sampled_data.append(sample_constituents)
        
        if sampled_data:
            return pd.concat(sampled_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def save_samples_to_db(self, sample_data):
        """保存抽样结果到数据库"""
        if sample_data.empty:
            print("No samples to save")
            return
        
        print(f"Saving {len(sample_data)} sample records to database...")
        
        try:
            target_date = str(sample_data['dt'].iloc[0])
            
            with self.sql_engine.connect() as conn:
                # 先清理当天数据
                delete_sql = """
                DELETE FROM bond_index_sample_constituents 
                WHERE dt = :dt
                """
                conn.execute(
                    sqlalchemy.text(delete_sql),
                    {'dt': target_date}
                )
                
                # 批量插入新数据 - 使用pandas to_sql方法
                sample_data.to_sql(
                    name='bond_index_sample_constituents',
                    con=self.sql_engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=5000
                )
                
            print("Samples saved successfully")
        except Exception as e:
            print(f"Error saving samples: {str(e)}")
    
    def sample_for_date(self, target_date, sample_size=50, random_seed=None):
        """为特定日期进行抽样"""
        print(f"Sampling constituents for {target_date} (sample size: {sample_size})...")
        
        try:
            # 获取构成数据
            constituents = self.get_constituents_for_date(target_date)
            
            if constituents.empty:
                print(f"No constituents data found for {target_date}")
                return False
            
            print(f"Found {len(constituents)} total constituents for {len(constituents['index_code'].unique())} indices")
            
            # 进行抽样
            sampled_data = self.sample_constituents(constituents, sample_size, random_seed)
            
            if sampled_data.empty:
                print("No samples generated")
                return False
            
            # 保存到数据库
            self.save_samples_to_db(sampled_data)
            
            print(f"Successfully sampled {len(sampled_data)} constituents for {target_date}")
            return True
            
        except Exception as e:
            print(f"Error sampling for {target_date}: {str(e)}")
            return False
    
    def get_sample_summary(self):
        """获取抽样数据概要"""
        try:
            query = """
            SELECT 
                MIN(dt) as start_date,
                MAX(dt) as end_date,
                COUNT(DISTINCT dt) as date_count,
                COUNT(DISTINCT index_code) as index_count,
                COUNT(DISTINCT trade_code) as bond_count,
                AVG(sample_size) as avg_sample_size,
                COUNT(*) as total_records
            FROM bond_index_sample_constituents
            """
            
            summary = pd.read_sql(query, self.sql_engine)
            return summary
        except Exception as e:
            print(f"Error getting sample summary: {str(e)}")
            return None
    
    def get_samples_for_date(self, target_date, index_code=None):
        """获取特定日期的抽样结果"""
        try:
            where_clause = f"WHERE dt = '{target_date}'"
            if index_code:
                where_clause += f" AND index_code = '{index_code}'"
            
            query = f"""
            SELECT dt, trade_code, index_code, sample_size
            FROM bond_index_sample_constituents
            {where_clause}
            ORDER BY index_code, trade_code
            """
            
            samples = pd.read_sql(query, self.sql_engine)
            return samples
        except Exception as e:
            print(f"Error getting samples for {target_date}: {str(e)}")
            return None
    
    def close_connections(self):
        """关闭数据库连接"""
        if hasattr(self, 'sql_engine'):
            self.sql_engine.dispose()

# 主程序
if __name__ == "__main__":
    # 创建抽样器
    sampler = IndexSampler()
    
    try:
        # 显示当前抽样概要
        summary = sampler.get_sample_summary()
        if summary is not None and not summary.empty:
            print("Current Sample Summary:")
            print(summary.to_string(index=False))
        else:
            print("No existing samples found")
        
        # 解析命令行参数
        target_date = None
        sample_size = 50
        random_seed = None
        
        if len(sys.argv) > 1:
            if sys.argv[1].lower() == 'latest':
                # 使用最新构成数据日期
                latest_date = sampler.get_latest_constituents_date()
                if latest_date:
                    target_date = str(latest_date)
                    print(f"Using latest constituents date: {target_date}")
                else:
                    print("No constituents data found")
                    sys.exit(1)
            else:
                target_date = sys.argv[1]
        else:
            # 默认：使用昨天的日期
            target_date = str(datetime.now().date() - timedelta(days=1))
            print(f"Using yesterday's date: {target_date}")
        
        # 解析抽样大小
        if len(sys.argv) > 2:
            try:
                sample_size = int(sys.argv[2])
            except ValueError:
                print("Invalid sample size, using default 50")
                sample_size = 50
        
        # 解析随机种子
        if len(sys.argv) > 3:
            try:
                random_seed = int(sys.argv[3])
            except ValueError:
                print("Invalid random seed, using None")
                random_seed = None
        
        # 进行抽样
        success = sampler.sample_for_date(target_date, sample_size, random_seed)
        
        if success:
            print(f"\nSampling completed for {target_date}")
            
            # 显示抽样结果概要
            samples = sampler.get_samples_for_date(target_date)
            if samples is not None and not samples.empty:
                print(f"\nSample results for {target_date}:")
                for index_code in samples['index_code'].unique():
                    index_samples = samples[samples['index_code'] == index_code]
                    print(f"  {index_code}: {len(index_samples)} samples")
        else:
            print(f"Sampling failed for {target_date}")
            
    finally:
        sampler.close_connections()
    
    print("\nUsage examples:")
    print("  python3 sample_index_constituents.py                    # Sample yesterday's data (50 samples)")
    print("  python3 sample_index_constituents.py 2025-07-02        # Sample specific date (50 samples)")
    print("  python3 sample_index_constituents.py latest            # Sample latest available date")
    print("  python3 sample_index_constituents.py 2024-01-15 30     # Sample 30 from each index")
    print("  python3 sample_index_constituents.py 2024-01-15 50 123 # Use random seed 123") 