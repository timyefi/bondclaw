import pandas as pd
import numpy as np
import sqlalchemy
import psycopg2
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
import warnings
import os
import gc
from tqdm import tqdm
import pyarrow.parquet as pq
import pyarrow as pa
import sys
warnings.filterwarnings('ignore')

class BondIndexSystem:
    def __init__(self, cache_dir='cache'):
        # MySQL数据库连接 (bond数据库) - 添加连接池和超时设置
        self.sql_engine = sqlalchemy.create_engine(
            'mysql+pymysql://hz_work:Hzinsights2015@rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com:3306/bond',
            poolclass=sqlalchemy.pool.NullPool,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                'connect_timeout': 60,
                'read_timeout': 60,
                'write_timeout': 60
            }
        )
        
        # PostgreSQL数据库连接 (tsdb数据库)
        self.pg_conn = psycopg2.connect(
            host="139.224.107.113",
            port=18032,
            user="postgres",
            password="hzinsights2015",
            database="tsdb"
        )
        
        # 缓存目录设置
        self.cache_dir = cache_dir
        self._create_cache_dirs()
        
    def _create_cache_dirs(self):
        """创建缓存目录结构"""
        dirs = [
            self.cache_dir,
            os.path.join(self.cache_dir, 'yield_data'),
            os.path.join(self.cache_dir, 'grouped_data'),
            os.path.join(self.cache_dir, 'price_data'),
            os.path.join(self.cache_dir, 'indices_data')
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _get_cache_path(self, category, filename):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, category, filename)
    
    def _cache_exists(self, cache_path):
        """检查缓存文件是否存在"""
        return os.path.exists(cache_path)
    
    def _load_from_cache(self, cache_path):
        """从缓存加载数据"""
        if self._cache_exists(cache_path):
            print(f"Loading from cache: {cache_path}")
            return pd.read_parquet(cache_path)
        return None
    
    def _save_to_cache(self, data, cache_path):
        """保存数据到缓存"""
        print(f"Saving to cache: {cache_path}")
        data.to_parquet(cache_path, index=False)
    
    def get_bond_classification(self, force_refresh=False):
        """获取债券分类信息"""
        cache_path = self._get_cache_path('', 'bond_classification.parquet')
        
        if not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None:
                credit_bonds = cached_data[cached_data['bond_type'] == 'credit']['trade_code'].tolist()
                finance_bonds = cached_data[cached_data['bond_type'] == 'finance']['trade_code'].tolist()
                return credit_bonds, finance_bonds
        
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
        
        # 合并并保存到缓存
        credit_bonds['bond_type'] = 'credit'
        finance_bonds['bond_type'] = 'finance'
        all_bonds = pd.concat([credit_bonds, finance_bonds], ignore_index=True)
        self._save_to_cache(all_bonds, cache_path)
        
        return credit_bonds['trade_code'].tolist(), finance_bonds['trade_code'].tolist()
    
    def get_yield_data_by_date_range(self, start_date, end_date, force_refresh=False):
        """按日期范围获取收益率数据"""
        cache_filename = f"yield_data_{start_date}_{end_date}.parquet"
        cache_path = self._get_cache_path('yield_data', cache_filename)
        
        if not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None:
                return cached_data
        
        print(f"Getting yield data for {start_date} to {end_date}...")
        
        query = f"""
        SELECT dt, trade_code, stdyield, balance
        FROM hzcurve_credit
        WHERE dt >= '{start_date}' AND dt <= '{end_date}'
        AND target_term = 3
        AND stdyield IS NOT NULL
        ORDER BY dt, stdyield DESC
        """
        
        yield_data = pd.read_sql(query, self.pg_conn)
        
        # 获取债券分类
        credit_bonds, finance_bonds = self.get_bond_classification()
        
        # 标记债券类型
        yield_data['bond_type'] = 'unknown'
        yield_data.loc[yield_data['trade_code'].isin(credit_bonds), 'bond_type'] = 'credit'
        yield_data.loc[yield_data['trade_code'].isin(finance_bonds), 'bond_type'] = 'finance'
        
        # 移除未分类的债券
        yield_data = yield_data[yield_data['bond_type'] != 'unknown']
        
        # 优化数据类型以节省内存
        yield_data['dt'] = pd.to_datetime(yield_data['dt'])
        yield_data['stdyield'] = yield_data['stdyield'].astype('float32')
        yield_data['balance'] = yield_data['balance'].astype('float64')
        yield_data['bond_type'] = yield_data['bond_type'].astype('category')
        
        self._save_to_cache(yield_data, cache_path)
        return yield_data
    
    def get_all_yield_data(self, start_date=None, end_date=None, batch_days=30, force_refresh=False):
        """分批获取所有收益率数据"""
        if start_date is None:
            # 获取数据的最早日期
            query = "SELECT MIN(dt) as min_date FROM hzcurve_credit WHERE target_term = 3"
            result = pd.read_sql(query, self.pg_conn)
            start_date = result['min_date'].iloc[0].strftime('%Y-%m-%d')
        
        if end_date is None:
            # 获取数据的最晚日期
            query = "SELECT MAX(dt) as max_date FROM hzcurve_credit WHERE target_term = 3"
            result = pd.read_sql(query, self.pg_conn)
            end_date = result['max_date'].iloc[0].strftime('%Y-%m-%d')
        
        print(f"Processing data from {start_date} to {end_date}")
        
        # 生成日期范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        all_data = []
        current_date = start_dt
        
        with tqdm(total=(end_dt - start_dt).days, desc="Loading yield data") as pbar:
            while current_date <= end_dt:
                batch_end = min(current_date + timedelta(days=batch_days-1), end_dt)
                
                batch_start_str = current_date.strftime('%Y-%m-%d')
                batch_end_str = batch_end.strftime('%Y-%m-%d')
                
                batch_data = self.get_yield_data_by_date_range(
                    batch_start_str, batch_end_str, force_refresh
                )
                
                if not batch_data.empty:
                    all_data.append(batch_data)
                
                pbar.update((batch_end - current_date).days + 1)
                current_date = batch_end + timedelta(days=1)
                
                # 强制垃圾回收
                gc.collect()
        
        if all_data:
            print("Combining all yield data...")
            combined_data = pd.concat(all_data, ignore_index=True)
            del all_data  # 释放内存
            gc.collect()
            return combined_data
        else:
            return pd.DataFrame()
    
    def create_percentile_groups_by_date(self, date, yield_data, force_refresh=False):
        """为单个日期创建分位数分组"""
        cache_filename = f"grouped_{date.strftime('%Y-%m-%d')}.parquet"
        cache_path = self._get_cache_path('grouped_data', cache_filename)
        
        if not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None:
                return cached_data
        
        daily_data = yield_data[yield_data['dt'] == date]
        if daily_data.empty:
            return pd.DataFrame()
        
        grouped_data = []
        
        for bond_type in ['credit', 'finance']:
            type_data = daily_data[daily_data['bond_type'] == bond_type].copy()
            
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
                            'dt': date,
                            'trade_code': row['trade_code'],
                            'bond_type': bond_type,
                            'percentile_group': f"{start_pct}-{end_pct}",
                            'stdyield': row['stdyield'],
                            'balance': row['balance']
                        })
        
        if grouped_data:
            result_df = pd.DataFrame(grouped_data)
            # 优化数据类型
            result_df['bond_type'] = result_df['bond_type'].astype('category')
            result_df['percentile_group'] = result_df['percentile_group'].astype('category')
            result_df['stdyield'] = result_df['stdyield'].astype('float32')
            result_df['balance'] = result_df['balance'].astype('float64')
            
            self._save_to_cache(result_df, cache_path)
            return result_df
        else:
            return pd.DataFrame()
    
    def create_all_percentile_groups(self, yield_data, force_refresh=False):
        """创建所有日期的分位数分组"""
        print("Creating percentile groups...")
        
        unique_dates = sorted(yield_data['dt'].unique())
        all_grouped_data = []
        
        with tqdm(unique_dates, desc="Processing dates") as pbar:
            for date in pbar:
                pbar.set_description(f"Processing {date.strftime('%Y-%m-%d')}")
                
                grouped_data = self.create_percentile_groups_by_date(
                    date, yield_data, force_refresh
                )
                
                if not grouped_data.empty:
                    all_grouped_data.append(grouped_data)
                
                # 定期清理内存
                if len(all_grouped_data) % 100 == 0:
                    gc.collect()
        
        if all_grouped_data:
            print("Combining all grouped data...")
            combined_data = pd.concat(all_grouped_data, ignore_index=True)
            del all_grouped_data
            gc.collect()
            return combined_data
        else:
            return pd.DataFrame()
    
    def get_price_data_by_date_range(self, start_date, end_date, bond_type, force_refresh=False):
        """按日期范围获取价格数据并缓存"""
        cache_filename = f"price_data_{bond_type}_{start_date}_{end_date}.parquet"
        cache_path = self._get_cache_path('price_data', cache_filename)
        
        if not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None:
                return cached_data
        
        print(f"Fetching price data for {bond_type} from {start_date} to {end_date}...")
        
        table_name = 'marketinfo_credit' if bond_type == 'credit' else 'marketinfo_finance'
        
        query = f"""
        SELECT DT, TRADE_CODE, ths_bond_balance_bond, 
               ths_valuate_full_price_cb_bond, ths_evaluate_net_price_cb_bond
        FROM {table_name}
        WHERE DT >= '{start_date}' AND DT <= '{end_date}'
        AND ths_bond_balance_bond IS NOT NULL
        AND ths_valuate_full_price_cb_bond IS NOT NULL
        AND ths_evaluate_net_price_cb_bond IS NOT NULL
        ORDER BY DT, TRADE_CODE
        """
        
        try:
            # 重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    price_data = pd.read_sql(query, self.sql_engine)
                    break
                except Exception as retry_e:
                    if retry == max_retries - 1:
                        raise retry_e
                    print(f"Retry {retry + 1}/{max_retries} for price data query")
                    import time
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error fetching price data: {e}")
            # 如果是连接错误，尝试重新创建连接
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                try:
                    print("Attempting to recreate MySQL connection...")
                    self.sql_engine = sqlalchemy.create_engine(
                        'mysql+pymysql://hz_work:Hzinsights2015@rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com:3306/bond',
                        poolclass=sqlalchemy.pool.NullPool,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        connect_args={
                            'connect_timeout': 60,
                            'read_timeout': 60,
                            'write_timeout': 60
                        }
                    )
                    # 重新尝试查询
                    price_data = pd.read_sql(query, self.sql_engine)
                except Exception as conn_e:
                    print(f"Failed to recreate connection and retry: {conn_e}")
                    return pd.DataFrame()
            else:
                return pd.DataFrame()
        
        if not price_data.empty:
            price_data.columns = ['dt', 'trade_code', 'balance', 'full_price', 'net_price']
            
            # 优化数据类型
            price_data['dt'] = pd.to_datetime(price_data['dt'])
            price_data['balance'] = price_data['balance'].astype('float64')
            price_data['full_price'] = price_data['full_price'].astype('float32')
            price_data['net_price'] = price_data['net_price'].astype('float32')
            
            self._save_to_cache(price_data, cache_path)
            return price_data
        else:
            print(f"No price data found for {bond_type} in date range {start_date} to {end_date}")
            return pd.DataFrame()
    
    def get_all_price_data(self, start_date=None, end_date=None, batch_days=30, force_refresh=False):
        """分批获取所有价格数据"""
        if start_date is None:
            start_date = '2014-01-01'  # 设置默认开始日期
        if end_date is None:
            end_date = '2025-12-31'   # 设置默认结束日期
        
        print(f"Loading price data from {start_date} to {end_date}")
        
        # 生成日期范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        all_price_data = {'credit': [], 'finance': []}
        current_date = start_dt
        
        with tqdm(total=(end_dt - start_dt).days, desc="Loading price data") as pbar:
            while current_date <= end_dt:
                batch_end = min(current_date + timedelta(days=batch_days-1), end_dt)
                
                batch_start_str = current_date.strftime('%Y-%m-%d')
                batch_end_str = batch_end.strftime('%Y-%m-%d')
                
                # 分别获取信用债和金融债的价格数据
                for bond_type in ['credit', 'finance']:
                    batch_data = self.get_price_data_by_date_range(
                        batch_start_str, batch_end_str, bond_type, force_refresh
                    )
                    
                    if not batch_data.empty:
                        all_price_data[bond_type].append(batch_data)
                
                pbar.update((batch_end - current_date).days + 1)
                current_date = batch_end + timedelta(days=1)
                
                # 强制垃圾回收
                gc.collect()
        
        # 合并数据
        combined_price_data = {}
        for bond_type in ['credit', 'finance']:
            if all_price_data[bond_type]:
                print(f"Combining {bond_type} price data...")
                combined_price_data[bond_type] = pd.concat(all_price_data[bond_type], ignore_index=True)
                del all_price_data[bond_type]  # 释放内存
            else:
                combined_price_data[bond_type] = pd.DataFrame()
        
        gc.collect()
        return combined_price_data
    
    def calculate_indices_by_date(self, date, grouped_data, price_data_dict, force_refresh=False):
        """计算单个日期的指数"""
        cache_filename = f"indices_{date.strftime('%Y-%m-%d')}.parquet"
        cache_path = self._get_cache_path('indices_data', cache_filename)
        
        if not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None:
                return cached_data
        
        daily_grouped = grouped_data[grouped_data['dt'] == date]
        if daily_grouped.empty:
            return pd.DataFrame()
        
        all_indices = []
        
        for bond_type in ['credit', 'finance']:
            type_data = daily_grouped[daily_grouped['bond_type'] == bond_type]
            if type_data.empty:
                continue
            
            # 从预加载的价格数据中筛选当日数据
            if bond_type not in price_data_dict or price_data_dict[bond_type].empty:
                continue
                
            daily_price_data = price_data_dict[bond_type][
                price_data_dict[bond_type]['dt'] == date
            ]
            
            if daily_price_data.empty:
                continue
            
            # 合并数据
            merged_data = type_data.merge(
                daily_price_data, on=['dt', 'trade_code'], how='inner', suffixes=('_yield', '_price')
            )
            
            if merged_data.empty:
                continue
            
            # 使用价格数据中的balance（更准确的市场数据）
            merged_data['balance'] = merged_data['balance_price']
            
            for percentile_group in merged_data['percentile_group'].unique():
                group_data = merged_data[merged_data['percentile_group'] == percentile_group]
                
                if group_data.empty or group_data['balance'].sum() == 0:
                    continue
                
                # 计算加权平均
                weights = group_data['balance'] / group_data['balance'].sum()
                
                full_price_index = (group_data['full_price'] * weights).sum()
                net_price_index = (group_data['net_price'] * weights).sum()
                
                all_indices.extend([
                    {
                        'dt': date,
                        'index_code': f"{bond_type.title()}_{percentile_group}_Full",
                        'index_value': full_price_index,
                        'index_type': 'full_price'
                    },
                    {
                        'dt': date,
                        'index_code': f"{bond_type.title()}_{percentile_group}_Net",
                        'index_value': net_price_index,
                        'index_type': 'net_price'
                    }
                ])
        
        if all_indices:
            result_df = pd.DataFrame(all_indices)
            result_df['index_type'] = result_df['index_type'].astype('category')
            result_df['index_value'] = result_df['index_value'].astype('float32')
            
            self._save_to_cache(result_df, cache_path)
            return result_df
        else:
            return pd.DataFrame()
    
    def calculate_all_indices(self, grouped_data, price_data_dict, force_refresh=False):
        """计算所有指数"""
        print("Calculating indices...")
        
        unique_dates = sorted(grouped_data['dt'].unique())
        all_indices = []
        
        with tqdm(unique_dates, desc="Calculating indices") as pbar:
            for date in pbar:
                pbar.set_description(f"Calculating {date.strftime('%Y-%m-%d')}")
                
                indices_data = self.calculate_indices_by_date(
                    date, grouped_data, price_data_dict, force_refresh
                )
                
                if not indices_data.empty:
                    all_indices.append(indices_data)
                
                # 定期清理内存
                if len(all_indices) % 50 == 0:
                    gc.collect()
        
        if all_indices:
            print("Combining all indices data...")
            combined_data = pd.concat(all_indices, ignore_index=True)
            del all_indices
            gc.collect()
            return combined_data
        else:
            return pd.DataFrame()
    
    def create_interactive_chart(self, indices_data, output_file='bond_indices_dashboard.html'):
        """创建交互式图表"""
        print("Creating interactive chart...")
        
        # 转换日期格式
        indices_data['dt'] = pd.to_datetime(indices_data['dt'])
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Credit Bond Indices - Full Price', 'Credit Bond Indices - Net Price',
                          'Finance Bond Indices - Full Price', 'Finance Bond Indices - Net Price'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 定义颜色
        colors = px.colors.qualitative.Set3
        
        # 绘制信用债全价指数
        credit_full = indices_data[
            (indices_data['index_code'].str.contains('Credit')) & 
            (indices_data['index_type'] == 'full_price')
        ]
        
        for i, index_code in enumerate(credit_full['index_code'].unique()):
            data = credit_full[credit_full['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # 绘制信用债净价指数
        credit_net = indices_data[
            (indices_data['index_code'].str.contains('Credit')) & 
            (indices_data['index_type'] == 'net_price')
        ]
        
        for i, index_code in enumerate(credit_net['index_code'].unique()):
            data = credit_net[credit_net['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # 绘制金融债全价指数
        finance_full = indices_data[
            (indices_data['index_code'].str.contains('Finance')) & 
            (indices_data['index_type'] == 'full_price')
        ]
        
        for i, index_code in enumerate(finance_full['index_code'].unique()):
            data = finance_full[finance_full['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 绘制金融债净价指数
        finance_net = indices_data[
            (indices_data['index_code'].str.contains('Finance')) & 
            (indices_data['index_type'] == 'net_price')
        ]
        
        for i, index_code in enumerate(finance_net['index_code'].unique()):
            data = finance_net[finance_net['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text="Bond Indices Dashboard",
            title_x=0.5,
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified'
        )
        
        # 添加范围选择器
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=3, label="3m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    type="date",
                    row=i, col=j
                )
        
        # 保存HTML文件
        pyo.plot(fig, filename=output_file, auto_open=False)
        print(f"Interactive chart saved as {output_file}")
        
        return fig
    
    def run_full_analysis(self, start_date=None, end_date=None, 
                         output_file='bond_indices_dashboard.html',
                         force_refresh=False, batch_days=30):
        """运行完整分析"""
        print("Starting bond index analysis with caching support...")
        
        try:
            # 步骤1: 获取收益率数据
            print("\n=== Step 1: Loading yield data ===")
            yield_data = self.get_all_yield_data(start_date, end_date, batch_days, force_refresh)
            print(f"Retrieved {len(yield_data)} yield records")
            
            if yield_data.empty:
                print("No yield data found!")
                return pd.DataFrame(), pd.DataFrame()
            
            # 步骤2: 创建分位数分组
            print("\n=== Step 2: Creating percentile groups ===")
            grouped_data = self.create_all_percentile_groups(yield_data, force_refresh)
            print(f"Created {len(grouped_data)} grouped records")
            
            # 释放yield_data内存
            del yield_data
            gc.collect()
            
            if grouped_data.empty:
                print("No grouped data created!")
                return pd.DataFrame(), pd.DataFrame()
            
            # 步骤3: 加载价格数据
            print("\n=== Step 3: Loading price data ===")
            price_data_dict = self.get_all_price_data(start_date, end_date, batch_days, force_refresh)
            print(f"Loaded price data - Credit: {len(price_data_dict['credit'])} records, Finance: {len(price_data_dict['finance'])} records")
            
            # 步骤4: 计算指数
            print("\n=== Step 4: Calculating indices ===")
            indices_data = self.calculate_all_indices(grouped_data, price_data_dict, force_refresh)
            print(f"Calculated {len(indices_data)} index points")
            
            # 释放价格数据内存
            del price_data_dict
            gc.collect()
            
            if indices_data.empty:
                print("No indices calculated!")
                return indices_data, grouped_data
            
            # 步骤5: 创建交互式图表
            print("\n=== Step 5: Creating interactive chart ===")
            fig = self.create_interactive_chart(indices_data, output_file)
            
            # 步骤6: 保存最终结果
            print("\n=== Step 6: Saving final results ===")
            final_indices_path = self._get_cache_path('', 'final_indices_data.parquet')
            final_grouped_path = self._get_cache_path('', 'final_grouped_data.parquet')
            
            self._save_to_cache(indices_data, final_indices_path)
            self._save_to_cache(grouped_data, final_grouped_path)
            
            # 保存CSV文件
            indices_data.to_csv('bond_indices_data.csv', index=False)
            grouped_data.to_csv('bond_grouped_data.csv', index=False)
            
            print("Analysis completed successfully!")
            print(f"Cache directory: {self.cache_dir}")
            print(f"Interactive chart: {output_file}")
            
            return indices_data, grouped_data
            
        except Exception as e:
            print(f"Error in analysis: {str(e)}")
            raise
        
        finally:
            # 关闭数据库连接
            if hasattr(self, 'pg_conn'):
                self.pg_conn.close()
    
    def get_progress_info(self):
        """获取处理进度信息"""
        cache_files = {
            'bond_classification': self._get_cache_path('', 'bond_classification.parquet'),
            'yield_data_files': len([f for f in os.listdir(self._get_cache_path('yield_data', '')) if f.endswith('.parquet')]) if os.path.exists(self._get_cache_path('yield_data', '')) else 0,
            'grouped_data_files': len([f for f in os.listdir(self._get_cache_path('grouped_data', '')) if f.endswith('.parquet')]) if os.path.exists(self._get_cache_path('grouped_data', '')) else 0,
            'indices_data_files': len([f for f in os.listdir(self._get_cache_path('indices_data', '')) if f.endswith('.parquet')]) if os.path.exists(self._get_cache_path('indices_data', '')) else 0,
            'final_indices': self._get_cache_path('', 'final_indices_data.parquet'),
            'final_grouped': self._get_cache_path('', 'final_grouped_data.parquet')
        }
        
        progress = {}
        for key, path in cache_files.items():
            if isinstance(path, int):
                progress[key] = path
            else:
                progress[key] = os.path.exists(path)
        
        return progress

# 主程序
if __name__ == "__main__":
    print("Starting Bond Index Analysis System...")
    print("Python version:", sys.version)
    
    try:
        # 创建分析系统
        print("Initializing BondIndexSystem...")
        bond_system = BondIndexSystem()
        print("BondIndexSystem initialized successfully!")
        
        # 显示当前进度
        print("Current progress:")
        progress = bond_system.get_progress_info()
        for key, value in progress.items():
            print(f"  {key}: {value}")
        
        print("\nStarting analysis...")
        
        # 运行完整分析
        # 参数说明:
        # start_date, end_date: 日期范围 (可选)
        # force_refresh: 是否强制刷新缓存
        # batch_days: 每批处理的天数
        
        indices_data, grouped_data = bond_system.run_full_analysis(
            start_date='2024-08-01',
            end_date='2025-07-03',
            force_refresh=False,
            batch_days=30
        )
        
        # 显示结果概要
        if not indices_data.empty:
            print("\n" + "="*50)
            print("ANALYSIS SUMMARY")
            print("="*50)
            print(f"Date range: {indices_data['dt'].min()} to {indices_data['dt'].max()}")
            print(f"Number of indices: {len(indices_data['index_code'].unique())}")
            print(f"Total data points: {len(indices_data)}")
            
            print("\nIndex codes:")
            for code in sorted(indices_data['index_code'].unique()):
                count = len(indices_data[indices_data['index_code'] == code])
                print(f"  {code}: {count} data points")
            
            print(f"\nFiles saved:")
            print(f"  - bond_indices_data.csv")
            print(f"  - bond_grouped_data.csv") 
            print(f"  - bond_indices_dashboard.html")
            print(f"  - Cache directory: {bond_system.cache_dir}/")
            
            print("\n" + "="*50)
            print("Analysis completed successfully!")
            print("="*50)
        else:
            print("No data was processed. Please check the database connections and data availability.")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 