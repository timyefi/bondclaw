import pandas as pd
import numpy as np
from db_pool import DatabaseConnection
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from decimal import Decimal
from tqdm import tqdm
import time
import os
from pathlib import Path

class IndexSampleConfig:
    """指数样本配置管理"""
    def __init__(self):
        # 债性分类指数样本配置
        self.nature_samples = {
            '偏债型': {'target':50},  # 固定目标样本数
            '平衡型': {'target': 50},
            '偏股型': {'target': 50}
        }
        
        # 溢价分类指数样本配置
        self.premium_samples = {
            '双低': {'target': 10},
            '低价高溢': {'target': 10},
            '高价低溢': {'target': 20},
            '双高': {'target': 10},
            '普通型': {'target':100}
        }
        
        # 行业指数样本配置
        self.industry_target = 10  # 行业固定目标样本数
        
        # 样本补充策略配置
        self.adjustment_steps = [
            {'premium_range': 2},    # 第一步：放宽溢价率±2%
            {'premium_range': 5},    # 第二步：放宽溢价率±5%
            {'turnover_rate': 0.3},  # 第三步：降低换手率要求到0.3%
            {'turnover_rate': 0.1},  # 第四步：进一步降低换手率到0.1%
            {'dynamic_minimum': True} # 最后：完全放开条件
        ]

class BondIndustryIndex:
    def __init__(self):
        self.logger = self._setup_logger()
        # 样本管理参数
        self.ma_window = 60  # 60个交易日移动平均
        self.min_continuous_days = 20  # 入池要求连续达标天数
        self.min_turnover_rate = 0.5  # 最低日均换手率(%)
        self.weight_cap = 0.10  # 单只债券权重上限
        # 缓存目录
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
        # 样本配置
        self.sample_config = IndexSampleConfig()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # 清除已存在的处理器
        logger.handlers.clear()
        
        # 创建文件处理器
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(
            log_dir / f'bond_index_{current_time}.log',
            encoding='utf-8'
        )
        
        # 创建控制台处理器，只显示重要信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _log_time(func):
        """装饰器：记录函数执行时间"""
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            self.logger.debug(f"开始执行: {func.__name__}")
            result = func(self, *args, **kwargs)
            end_time = time.time()
            self.logger.debug(f"完成执行: {func.__name__}, 耗时: {end_time - start_time:.2f}秒")
            return result
        return wrapper

    def _get_cache_path(self, data_type: str, start_date: str, end_date: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{data_type}_{start_date}_{end_date}.parquet"
    
    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        if cache_path.exists():
            try:
                self.logger.info(f"从缓存加载数据: {cache_path}")
                return pd.read_parquet(cache_path)
            except Exception as e:
                self.logger.warning(f"加载缓存失败: {e}")
                return None
        return None
    
    def _save_to_cache(self, df: pd.DataFrame, cache_path: Path):
        """保存数据到缓存"""
        try:
            self.logger.info(f"保存数据到缓存: {cache_path}")
            df.to_parquet(cache_path)
        except Exception as e:
            self.logger.warning(f"保存缓存失败: {e}")
    
    def _get_industry_bonds(self) -> pd.DataFrame:
        """获取所有可转债的行业分类信息"""
        cache_path = self._get_cache_path('industry_bonds', 'all', 'all')
        
        # 尝试从缓存加载
        df = self._load_from_cache(cache_path)
        if df is not None:
            return df
            
        # 从数据库获取
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT
                    A.trade_code,
                    A.ths_bond_short_name_bond,
                    A.ths_object_the_sw_bond,
                    A.ths_stock_code_cbond
                FROM bond.basicinfo_equity A
                WHERE A.trade_code NOT LIKE '%%NQ'
                AND A.ths_object_the_sw_bond IS NOT NULL
            """)
            columns = ['trade_code', 'ths_bond_short_name_bond', 'ths_object_the_sw_bond', 'ths_stock_code_cbond']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            
        # 保存到缓存
        self._save_to_cache(df, cache_path)
        return df
    
    def _get_bond_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取可转债市场数据"""
        cache_path = self._get_cache_path('bond_market', start_date, end_date)
        
        # 尝试从缓存加载
        df = self._load_from_cache(cache_path)
        if df is not None:
            return df
            
        # 从数据库获取
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                A.dt,
                A.trade_code,
                A.close as close,
                    A.amount as amount,
                    B.ths_bond_balance_bond as balance,
                    A.un_conversion_balance as un_conversion_balance
                FROM yq.marketinfo_equity1 A
                INNER JOIN bond.marketinfo_equity B
                ON A.trade_code=B.trade_code
                AND A.dt=B.dt
                WHERE B.ths_bond_balance_bond > 0
                AND A.trade_code NOT LIKE '%%NQ'
                AND A.dt BETWEEN %s AND %s
            """, (start_date, end_date))
            columns = ['dt', 'trade_code', 'close', 'amount', 'balance', 'un_conversion_balance']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            
        # 保存到缓存
        self._save_to_cache(df, cache_path)
        return df
    
    def _get_stock_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取正股市场数据"""
        cache_path = self._get_cache_path('stock_market', start_date, end_date)
        
        # 尝试从缓存加载
        df = self._load_from_cache(cache_path)
        if df is not None:
            return df
            
        # 从数据库获取
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    A.dt,
                    c.trade_code,
                    A.close as close,
                    A.AMT as amount,
                    A.MKT_CAP_ARD as balance,
                    B.ths_stock_code_cbond,
                    A.MKT_FREESHARES as un_conversion_balance
                FROM stock.marketinfo A
                INNER JOIN bond.basicinfo_equity B
                ON A.trade_code=B.ths_stock_code_cbond
                INNER JOIN bond.marketinfo_equity C
                ON B.trade_code=C.trade_code
                AND A.dt=C.dt
                WHERE C.ths_bond_balance_bond > 0
                AND B.trade_code NOT LIKE '%%NQ'
                AND A.dt BETWEEN %s AND %s
            """, (start_date, end_date))
            columns = ['dt', 'trade_code', 'close', 'amount', 'balance', 'ths_stock_code_cbond', 'un_conversion_balance']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            
        # 保存到缓存
        self._save_to_cache(df, cache_path)
        return df
    
    def _split_industry_levels(self, industry_bonds: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """将行业分类拆分为三个层级"""
        def split_industry(industry_str: str) -> List[str]:
            if pd.isna(industry_str):
                return ['Unknown'] * 3
            parts = industry_str.split('--')
            return parts + ['Unknown'] * (3 - len(parts))
        
        industry_bonds[['level1', 'level2', 'level3']] = pd.DataFrame(
            industry_bonds['ths_object_the_sw_bond'].apply(split_industry).tolist()
        )
        
        # return {
        #     'level1': industry_bonds[['trade_code', 'level1']],
        #     'level2': industry_bonds[['trade_code', 'level2']],
        #     'level3': industry_bonds[['trade_code', 'level3']]
        # }
        return {
            'level1': industry_bonds[['trade_code', 'level1']]
        }

    
    def _calculate_turnover_rate(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """计算换手率
        换手率 = 成交金额总和/未转股余额总和
        """
        market_data['turnover_rate'] = (market_data['amount'] / market_data['un_conversion_balance']) * 100
        return market_data
    
    def _get_bond_characteristics_batch(self, start_date: str, end_date: str) -> pd.DataFrame:
        """批量获取指定时间段的可转债特性数据"""
        cache_path = self._get_cache_path('bond_chars', start_date, end_date)
        
        # 尝试从缓存加载
        df = self._load_from_cache(cache_path)
        if df is not None:
            return df
            
        # 从数据库获取
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    dt,
                    trade_code,
                    close,
                    amount,
                    conv_premium as ths_conversion_premium_rate_cbond,
                    pure_premium as ths_pure_bond_premium_rate_cbond,
                    ytm as ths_pure_bond_ytm_cbond
                FROM yq.marketinfo_equity1
                WHERE dt BETWEEN %s AND %s
                AND trade_code NOT LIKE '%%NQ'
            """, (start_date, end_date))
            columns = ['dt', 'trade_code', 'close', 'amount', 'ths_conversion_premium_rate_cbond', 
                      'ths_pure_bond_premium_rate_cbond', 'ths_pure_bond_ytm_cbond']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            df['ths_pure_bond_premium_rate_cbond'] = self._calculate_parity_premium(df)
            
        # 保存到缓存
        self._save_to_cache(df, cache_path)
        return df
    
    def _calculate_parity_premium(self, df: pd.DataFrame) -> pd.Series:
        """计算平价溢价率"""
        return ((1 + df['ths_pure_bond_premium_rate_cbond']) / (1 + df['ths_conversion_premium_rate_cbond']) - 1) * 100
    
    
    def _classify_bonds_batch(self, bonds_data: pd.DataFrame) -> pd.DataFrame:
        """
        对债券进行分类，使用独立的布尔列标记不同分类
        """
        # 创建副本避免修改原始数据
        bonds_data = bonds_data.copy()
        
        # 1. 债性分类
        bonds_data['偏债型'] = bonds_data['ths_pure_bond_premium_rate_cbond'] < -10
        bonds_data['平衡型'] = (bonds_data['ths_pure_bond_premium_rate_cbond'] >= -10) & \
                            (bonds_data['ths_pure_bond_premium_rate_cbond'] <= 10)
        bonds_data['偏股型'] = bonds_data['ths_pure_bond_premium_rate_cbond'] > 10
        
        # 2. 溢价分类
        bonds_data['双低'] = (bonds_data['close'] <= 110) & \
                           (bonds_data['ths_conversion_premium_rate_cbond'] <= 20)
        bonds_data['低价高溢'] = (bonds_data['close'] <= 110) & \
                             (bonds_data['ths_conversion_premium_rate_cbond'] > 20)
        bonds_data['高价低溢'] = (bonds_data['close'] > 110) & \
                             (bonds_data['ths_conversion_premium_rate_cbond'] <= 20)
        bonds_data['双高'] = (bonds_data['close'] > 110) & \
                           (bonds_data['ths_conversion_premium_rate_cbond'] > 20)
        bonds_data['普通型'] = ~(bonds_data['双低'] | bonds_data['低价高溢'] | \
                             bonds_data['高价低溢'] | bonds_data['双高'])
        
        # 确保返回所有必要的列，包括level1
        required_columns = ['trade_code', '偏债型', '平衡型', '偏股型', 
                           '双低', '低价高溢', '高价低溢', '双高', '普通型']
        
        # 如果level1列存在，则保留它
        if 'level1' in bonds_data.columns:
            required_columns.append('level1')
        
        return bonds_data[required_columns]

    def _calculate_index_batch(self, market_data: pd.DataFrame, group_data: pd.DataFrame, 
                             group_by: str) -> pd.DataFrame:
        """批量计算指数，使用优化的聚合操作"""
        # 确保dt列的类型一致性
        market_data = market_data.copy()
        group_data = group_data.copy()
        
        # 转换为datetime类型
        market_data['dt'] = pd.to_datetime(market_data['dt'])
        group_data['dt'] = pd.to_datetime(group_data['dt'])
        
        # 合并数据
        merged_data = pd.merge(market_data, group_data, on=['dt', 'trade_code'], how='inner')
        merged_data = merged_data.dropna(subset=['close', 'balance'])
        
        # 转换数据类型并预计算
        merged_data['close'] = merged_data['close'].astype(float)
        merged_data['balance'] = merged_data['balance'].astype(float)
        merged_data['weighted_close'] = merged_data['close'] * merged_data['balance']
        
        # 计算换手率
        if 'amount' in merged_data.columns and 'un_conversion_balance' in merged_data.columns:
            merged_data['turnover_rate'] = (merged_data['amount'] / merged_data['un_conversion_balance']) * 100
        merged_data['turnover_rate'] = merged_data['turnover_rate'].fillna(0)
        
        # 使用agg替代apply，提高性能
        result = merged_data.groupby(['dt', group_by]).agg({
            'weighted_close': 'sum',
            'balance': 'sum',
            'trade_code': 'count',
            'turnover_rate': 'mean'
        }).reset_index()
        
        # 计算加权平均价格
        result['close'] = result['weighted_close'] / result['balance']
        result = result.drop('weighted_close', axis=1)
        
        # 重命名列
        result = result.rename(columns={
            'balance': 'total_balance',
            'trade_code': 'component_count'
        })
        
        return result
    
    def _generate_index_codes(self, names: List[str], prefix: str) -> Dict[str, str]:
        """生成指数代码"""
        return {
            name: f'{prefix}{str(i+1).zfill(3)}'
            for i, name in enumerate(sorted(names))
        }
    
    def _save_index_info(self, index_codes: Dict[str, str], index_type: str):
        """保存指数基本信息到数据库"""
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            for name, code in index_codes.items():
                # 生成中文指数名称
                if name in ['双低', '低价高溢', '高价低溢', '双高', '偏债型', '偏股型', '平衡型']:
                    index_name = f"{'可转债' if index_type == 'BOND' else '转债正股'}{name}指数"
                else:
                    # 行业指数保持原样
                    index_name = f"{'可转债' if index_type == 'BOND' else '转债正股'}{name}指数"
                
                cursor.execute("""
                    INSERT INTO bond.basicinfo_ebindex 
                    (trade_code, index_name, index_type, category)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    index_name = VALUES(index_name),
                    index_type = VALUES(index_type),
                    category = VALUES(category)
                """, (
                    code,
                    index_name,
                    index_type,
                    name
                ))
            conn.commit()
    
    @_log_time
    def _save_index_market_data(self, index_data: pd.DataFrame, index_code: str):
        """批量保存指数行情数据"""
        self.logger.info(f"保存指数 {index_code} 的市场数据，共 {len(index_data)} 条记录")
        
        # 准备批量插入的数据
        values = [
            (index_code, row['dt'], float(row['close']), float(row['total_balance']),
             int(row['component_count']), float(row['turnover_rate']) if pd.notnull(row.get('turnover_rate')) else None)
            for _, row in index_data.iterrows()
        ]
        
        # 使用executemany批量插入
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                    INSERT INTO bond.marketinfo_ebindex 
                (trade_code, dt, close, total_balance, component_count, turnover_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    close = VALUES(close),
                    total_balance = VALUES(total_balance),
                component_count = VALUES(component_count),
                turnover_rate = VALUES(turnover_rate)
            """, values)
            conn.commit()
    
    def generate_historical_index(self, start_date: str, end_date: str):
        """生成历史指数数据"""
        self.logger.info(f"开始生成历史指数数据: {start_date} 到 {end_date}")
        total_start_time = time.time()
        
        # 1. 获取数据
        self.logger.info("Step 1/6: 获取基础数据")
        data_start = time.time()
        industry_bonds = self._get_industry_bonds()
        market_data = self._get_bond_market_data(start_date, end_date)
        chars_data = self._get_bond_characteristics_batch(start_date, end_date)
        stock_market_data = self._get_stock_market_data(start_date, end_date)
        
        self.logger.info(f"数据获取完成，耗时: {time.time() - data_start:.2f}秒")
        self.logger.info(f"可转债数量: {len(market_data['trade_code'].unique())}, 交易天数: {len(market_data['dt'].unique())}")
        
        # 2. 生成行业分类
        self.logger.info("Step 2/6: 生成行业分类")
        category_start = time.time()
        industry_levels = self._split_industry_levels(industry_bonds)
        self.logger.info(f"行业分类完成，耗时: {time.time() - category_start:.2f}秒")
        self.logger.info(f"行业数量: {industry_levels['level1'].nunique()}")
        
        # 3. 获取合格样本
        self.logger.info("Step 2/6: 获取合格样本")
        sample_start = time.time()
        qualified_samples = self._get_qualified_samples(market_data, chars_data, industry_bonds)
        
        if qualified_samples.empty:
            self.logger.error("未找到合格样本")
            return
        
        self.logger.info(f"样本筛选完成，耗时: {time.time() - sample_start:.2f}秒")
        self.logger.info(f"合格样本数量: {len(qualified_samples['trade_code'].unique())}")
        
        # 4. 生成分类数据
        self.logger.info("Step 3/6: 生成分类数据")
        category_start = time.time()
        
        # 4.1 债性分类数据
        nature_data = []
        for nature_type in ['偏债型', '平衡型', '偏股型']:
            type_data = qualified_samples[qualified_samples[nature_type]].copy()
            type_data['category'] = nature_type
            nature_data.append(type_data[['dt', 'trade_code', 'category']])
        nature_data = pd.concat(nature_data, ignore_index=True)
        
        # 4.2 溢价分类数据
        premium_data = []
        for premium_type in ['双低', '低价高溢', '高价低溢', '双高', '普通型']:
            type_data = qualified_samples[qualified_samples[premium_type]].copy()
            type_data['category'] = premium_type
            premium_data.append(type_data[['dt', 'trade_code', 'category']])
        premium_data = pd.concat(premium_data, ignore_index=True)
        
        # 4.3 行业分类数据
        industry_data = qualified_samples[['dt', 'trade_code', 'level1']].copy()
        
        self.logger.info(f"分类数据生成完成，耗时: {time.time() - category_start:.2f}秒")
        
        # 5. 计算指数
        self.logger.info("Step 4/6: 计算可转债指数")
        bond_index_start = time.time()
        
        # 5.0 计算可转债总体指数
        all_bonds_data = qualified_samples[['dt', 'trade_code']].copy()
        all_bonds_data['category'] = '全部'
        bond_all_index = self._calculate_index_batch(market_data, all_bonds_data, 'category')
        
        # 5.1 计算可转债行业指数
        bond_industry_index = self._calculate_index_batch(market_data, industry_data, 'level1')
        
        # 5.2 计算可转债债性分类指数
        bond_nature_index = self._calculate_index_batch(market_data, nature_data, 'category')
        
        # 5.3 计算可转债溢价分类指数
        bond_premium_index = self._calculate_index_batch(market_data, premium_data, 'category')
        
        self.logger.info(f"可转债指数计算完成，耗时: {time.time() - bond_index_start:.2f}秒")
        
        # 6. 计算正股指数
        self.logger.info("Step 5/6: 计算正股指数")
        stock_index_start = time.time()
        
        if not stock_market_data.empty:
            # 6.0 计算正股总体指数
            stock_all_index = self._calculate_index_batch(stock_market_data, all_bonds_data, 'category')
            
            # 6.1 计算行业正股指数
            stock_industry_index = self._calculate_index_batch(stock_market_data, industry_data, 'level1')
            
            # 6.2 计算债性分类正股指数
            stock_nature_index = self._calculate_index_batch(stock_market_data, nature_data, 'category')
            
            # 6.3 计算溢价分类正股指数
            stock_premium_index = self._calculate_index_batch(stock_market_data, premium_data, 'category')
            
            self.logger.info(f"正股指数计算完成，耗时: {time.time() - stock_index_start:.2f}秒")
        
        # 7. 保存数据
        self.logger.info("Step 6/6: 保存指数数据")
        save_start = time.time()
        
        # 7.0 保存可转债总体指数
        all_index_codes = {'全部': 'HZEB000'}
        self._save_index_info(all_index_codes, 'BOND')
        self.logger.info("开始保存可转债总体指数")
        self._save_index_market_data(bond_all_index, 'HZEB000')
        
        # 7.1 保存可转债行业指数
        industry_codes = self._generate_index_codes(
            bond_industry_index['level1'].unique(),
            'HZEB'
        )
        self._save_index_info(industry_codes, 'BOND')
        self.logger.info(f"开始保存 {len(industry_codes)} 个可转债行业指数")
        for industry_name, index_code in tqdm(industry_codes.items(), desc="保存可转债行业指数"):
            industry_index_data = bond_industry_index[bond_industry_index['level1'] == industry_name]
            self._save_index_market_data(industry_index_data, index_code)
        
        # 7.2 保存可转债债性分类指数
        nature_codes = self._generate_index_codes(
            bond_nature_index['category'].unique(),
            'HZEBP'
        )
        self._save_index_info(nature_codes, 'BOND')
        self.logger.info(f"开始保存 {len(nature_codes)} 个可转债债性分类指数")
        for category_name, index_code in tqdm(nature_codes.items(), desc="保存可转债债性分类指数"):
            category_index_data = bond_nature_index[bond_nature_index['category'] == category_name]
            self._save_index_market_data(category_index_data, index_code)
        
        # 7.3 保存可转债溢价分类指数
        premium_codes = self._generate_index_codes(
            bond_premium_index['category'].unique(),
            'HZEBPP'
        )
        self._save_index_info(premium_codes, 'BOND')
        self.logger.info(f"开始保存 {len(premium_codes)} 个可转债溢价分类指数")
        for category_name, index_code in tqdm(premium_codes.items(), desc="保存可转债溢价分类指数"):
            category_index_data = bond_premium_index[bond_premium_index['category'] == category_name]
            self._save_index_market_data(category_index_data, index_code)
        
        # 7.4 保存正股指数（如果有数据）
        if not stock_market_data.empty:
            # 保存正股总体指数
            stock_all_index_codes = {'全部': 'HZEBS000'}
            self._save_index_info(stock_all_index_codes, 'STOCK')
            self.logger.info("开始保存正股总体指数")
            self._save_index_market_data(stock_all_index, 'HZEBS000')
            
            # 保存正股行业指数
            stock_industry_codes = self._generate_index_codes(
                stock_industry_index['level1'].unique(),
                'HZEBS'
            )
            self._save_index_info(stock_industry_codes, 'STOCK')
            self.logger.info(f"开始保存 {len(stock_industry_codes)} 个正股行业指数")
            for industry_name, index_code in tqdm(stock_industry_codes.items(), desc="保存正股行业指数"):
                industry_index_data = stock_industry_index[stock_industry_index['level1'] == industry_name]
                self._save_index_market_data(industry_index_data, index_code)
            
            # 保存正股债性分类指数
            stock_nature_codes = self._generate_index_codes(
                stock_nature_index['category'].unique(),
                'HZEBSP'
            )
            self._save_index_info(stock_nature_codes, 'STOCK')
            self.logger.info(f"开始保存 {len(stock_nature_codes)} 个正股债性分类指数")
            for category_name, index_code in tqdm(stock_nature_codes.items(), desc="保存正股债性分类指数"):
                category_index_data = stock_nature_index[stock_nature_index['category'] == category_name]
                self._save_index_market_data(category_index_data, index_code)
            
            # 保存正股溢价分类指数
            stock_premium_codes = self._generate_index_codes(
                stock_premium_index['category'].unique(),
                'HZEBSPP'
            )
            self._save_index_info(stock_premium_codes, 'STOCK')
            self.logger.info(f"开始保存 {len(stock_premium_codes)} 个正股溢价分类指数")
            for category_name, index_code in tqdm(stock_premium_codes.items(), desc="保存正股溢价分类指数"):
                category_index_data = stock_premium_index[stock_premium_index['category'] == category_name]
                self._save_index_market_data(category_index_data, index_code)
        
        self.logger.info(f"数据保存完成，耗时: {time.time() - save_start:.2f}秒")
        total_time = time.time() - total_start_time
        self.logger.info(f"历史指数数据生成完成，总耗时: {total_time:.2f}秒")
        
        # 输出性能统计
        self.logger.info("\n性能统计:")
        self.logger.info(f"数据获取: {(time.time() - data_start)/total_time*100:.1f}%")
        self.logger.info(f"样本筛选: {(time.time() - sample_start)/total_time*100:.1f}%")
        self.logger.info(f"分类生成: {(time.time() - category_start)/total_time*100:.1f}%")
        self.logger.info(f"指数计算: {(time.time() - bond_index_start)/total_time*100:.1f}%")
        self.logger.info(f"数据保存: {(time.time() - save_start)/total_time*100:.1f}%")

    def generate_daily_index(self, date: Optional[str] = None):
        """生成当日指数数据"""
        if date is None:
            # 获取最近的交易日
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(dt) as last_trade_date
                    FROM yq.marketinfo_equity1
                """)
                last_trade_date = cursor.fetchone()[0]
                date = last_trade_date.strftime('%Y-%m-%d') if last_trade_date else None
                
        if date:
            self.logger.info(f"开始生成 {date} 的指数数据")
            self.generate_historical_index(date, date)
            self.logger.info("当日指数数据生成完成")
        else:
            self.logger.warning("未找到有效的交易日期")

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """向量化计算移动平均"""
        metrics = ['close', 'ths_conversion_premium_rate_cbond', 
                  'ths_pure_bond_premium_rate_cbond', 'turnover_rate']
        
        # 一次性计算所有指标的移动平均
        ma_df = df.groupby('trade_code')[metrics].transform(
            lambda x: x.rolling(window=self.ma_window, min_periods=1).mean()
        )
        
        # 重命名列
        ma_columns = {col: f'{col}_ma60' for col in metrics}
        ma_df.rename(columns=ma_columns, inplace=True)
        
        # 合并原始数据和移动平均
        return pd.concat([df, ma_df], axis=1)
    
    def _check_continuous_qualification(self, df: pd.DataFrame, condition: pd.Series) -> pd.Series:
        """向量化检查连续达标天数"""
        # 按债券分组，确保不同债券之间的数据不会互相影响
        result = pd.Series(False, index=df.index)
        
        for code in df['trade_code'].unique():
            # 获取该债券的数据，并按日期排序
            bond_data = condition[df['trade_code'] == code].sort_index()
            if bond_data.empty:
                continue
                
            # 计算状态变化（只在有效数据之间计算）
            valid_data = bond_data.dropna()
            if len(valid_data) == 0:
                continue
                
            # 计算状态变化
            changes = (valid_data != valid_data.shift()).astype(int)
            groups = changes.cumsum()
            
            # 计算每组连续True的天数
            counts = valid_data.groupby(groups).cumsum()
            
            # 更新结果（只更新有效数据的结果）
            result[valid_data.index] = counts >= self.min_continuous_days
            
            # 调试日志
            if code == df['trade_code'].iloc[0]:
                self.logger.debug(f"\n债券 {code} 的连续性检查:")
                self.logger.debug(f"总记录数: {len(bond_data)}")
                self.logger.debug(f"有效记录数: {len(valid_data)}")
                self.logger.debug(f"满足条件的记录数: {len(valid_data[valid_data])}")
                self.logger.debug(f"最大连续天数: {counts.max() if not counts.empty else 0}")
                if len(counts[counts > 0]) > 0:
                    self.logger.debug(f"连续天数分布:\n{counts[counts > 0].value_counts().sort_index()}")
                    self.logger.debug(f"状态变化次数: {len(changes[changes == 1])}")
        
        return result

    def _get_quarterly_candidates(self, df: pd.DataFrame, quarter_start: str, quarter_end: str) -> pd.DataFrame:
        """获取季度候选样本
        
        Args:
            df: 包含所有数据的DataFrame
            quarter_start: 季度开始日期
            quarter_end: 季度结束日期
        
        Returns:
            DataFrame: 包含候选样本的基本信息和平均未转股余额
        """
        # 获取季度数据
        quarter_data = df[
            (df['dt'] >= quarter_start) & 
            (df['dt'] <= quarter_end)
        ]
        
        # 检查首末两日是否有数据
        start_day_data = quarter_data[quarter_data['dt'] == quarter_start]
        end_day_data = quarter_data[quarter_data['dt'] == quarter_end]
        
        # 获取在首末两日都有未转股余额>0的样本
        valid_start = set(start_day_data[start_day_data['un_conversion_balance'] > 0]['trade_code'])
        valid_end = set(end_day_data[end_day_data['un_conversion_balance'] > 0]['trade_code'])
        valid_codes = valid_start.intersection(valid_end)
        
        if not valid_codes:
            return pd.DataFrame()
        
        # 获取最后一天的行业分类信息
        last_day_industry = end_day_data[['trade_code', 'level1']].drop_duplicates()
        
        # 计算季度平均未转股余额
        avg_balance = quarter_data[quarter_data['trade_code'].isin(valid_codes)].groupby('trade_code').agg({
            'un_conversion_balance': 'mean',
            'turnover_rate': 'mean',
            'close': 'last',
            'ths_pure_bond_premium_rate_cbond': 'last',
            'ths_conversion_premium_rate_cbond': 'last'
        }).reset_index()
        
        # 合并行业信息
        avg_balance = pd.merge(avg_balance, last_day_industry, on='trade_code', how='left')
        
        return avg_balance.sort_values('un_conversion_balance', ascending=False)

    def _select_samples_by_balance(self, candidates: pd.DataFrame, quarter_start: str, quarter_end: str, target_count: int) -> pd.DataFrame:
        """
        从候选样本中选择指定数量的样本，基于季度首末日未转股余额和平均未转股余额
        
        Args:
            candidates: 候选样本数据
            quarter_start: 季度开始日期
            quarter_end: 季度结束日期
            target_count: 目标样本数量
        
        Returns:
            选中的样本数据
        """
        # 获取候选样本的代码列表
        candidate_codes = set(candidates['trade_code'])
        
        # 从季度数据中获取这些样本的数据
        quarter_data = self.current_quarter_data[
            self.current_quarter_data['trade_code'].isin(candidate_codes)
        ]
        
        # 1. 获取首末日数据
        first_day = quarter_data[quarter_data['dt'] == quarter_start]
        last_day = quarter_data[quarter_data['dt'] == quarter_end]
        
        # 2. 筛选两天都有效的样本
        valid_first = first_day[first_day['un_conversion_balance'] > 0]['trade_code']
        valid_last = last_day[last_day['un_conversion_balance'] > 0]['trade_code']
        valid_codes = set(valid_first).intersection(set(valid_last))
        
        if not valid_codes:
            return pd.DataFrame()
        
        # 3. 计算平均未转股余额
        valid_data = quarter_data[quarter_data['trade_code'].isin(valid_codes)]
        avg_balance = valid_data.groupby('trade_code')['un_conversion_balance'].mean()
        
        # 4. 按平均未转股余额排序并选择目标数量
        selected_codes = avg_balance.sort_values(ascending=False).head(target_count).index
        
        return candidates[candidates['trade_code'].isin(selected_codes)]

    def _get_qualified_samples(self, market_data: pd.DataFrame, chars_data: pd.DataFrame, industry_bonds: pd.DataFrame) -> pd.DataFrame:
        """获取合格样本"""
        # 1. 合并数据
        df = pd.merge(market_data, chars_data, on=['dt', 'trade_code'], how='inner', suffixes=('', '_chars'))
        df = pd.merge(df, industry_bonds[['trade_code', 'ths_object_the_sw_bond']], 
                     on='trade_code', how='left')
        df['level1'] = df['ths_object_the_sw_bond'].apply(
            lambda x: x.split('--')[0] if pd.notnull(x) else 'Unknown'
        )
        
        # 2. 计算换手率
        df['turnover_rate'] = (df['amount'] / df['un_conversion_balance']) * 100
        
        # 3. 获取季度日期
        df['dt'] = pd.to_datetime(df['dt'])
        df_dates = pd.DataFrame({'dt': df['dt'].unique()}).sort_values('dt')
        df_dates['year_quarter'] = df_dates['dt'].dt.to_period('Q')
        quarter_dates = df_dates.groupby('year_quarter').agg({
            'dt': ['first', 'last']
        }).reset_index()
        quarter_dates.columns = ['year_quarter', 'start_date', 'end_date']
        
        # 4. 初始化结果列表
        final_samples = []
        
        # 5. 按季度处理样本
        for _, quarter in quarter_dates.iterrows():
            quarter_start = quarter['start_date'].strftime('%Y-%m-%d')
            quarter_end = quarter['end_date'].strftime('%Y-%m-%d')
            
            # 获取季度数据
            quarter_data = df[
                (df['dt'] >= quarter_start) & 
                (df['dt'] <= quarter_end)
            ]
            
            # 5.1 对季度数据进行清洗（只在样本选择时应用）
            clean_quarter_data = quarter_data[
                (quarter_data['close'] > 0) & 
                (quarter_data['close'] < 300) &  
                (quarter_data['turnover_rate'].notna()) & 
                (quarter_data['turnover_rate'] < 200) &
                (quarter_data['ths_conversion_premium_rate_cbond'].notna()) &
                (quarter_data['ths_conversion_premium_rate_cbond'] > -80) &
                (quarter_data['ths_conversion_premium_rate_cbond'] < 300) &
                (quarter_data['ths_pure_bond_premium_rate_cbond'].notna()) &
                (quarter_data['ths_pure_bond_premium_rate_cbond'] > -80) &
                (quarter_data['ths_pure_bond_premium_rate_cbond'] < 300)
            ]
            
            # 5.2 获取季度候选样本
            quarter_candidates = self._get_quarterly_candidates(clean_quarter_data, quarter_start, quarter_end)
            if quarter_candidates.empty:
                continue
            
            # 5.3 对候选样本进行分类
            classified_candidates = self._classify_bonds_batch(quarter_candidates)
            
            # 6. 处理季度内每日数据
            for current_date, day_data in quarter_data.groupby('dt'):
                # 获取当日有效的样本
                valid_samples = day_data[day_data['trade_code'].isin(classified_candidates['trade_code'])]
                
                if not valid_samples.empty:
                    # 创建当日样本数据
                    day_qualified = valid_samples.copy()
                    
                    # 从classified_candidates中获取分类信息
                    classification_info = classified_candidates[['trade_code', '偏债型', '平衡型', '偏股型', 
                                                              '双低', '低价高溢', '高价低溢', '双高', '普通型']]
                    
                    # 合并分类信息和行业信息
                    day_qualified = pd.merge(day_qualified, classification_info, on='trade_code', how='left')
                    
                    final_samples.append(day_qualified)
        
        # 7. 合并所有日期的样本
        if final_samples:
            qualified = pd.concat(final_samples, ignore_index=True)
            # 选择需要的列
            return qualified[['dt', 'trade_code', 'close', 'amount', 'un_conversion_balance', 
                            'ths_pure_bond_premium_rate_cbond', 'ths_conversion_premium_rate_cbond',
                            '偏债型', '平衡型', '偏股型', '双低', '低价高溢', '高价低溢', '双高', '普通型', 'level1']]
        else:
            return pd.DataFrame()

    def _get_candidates_with_criteria(self, day_data: pd.DataFrame, category_type: str, 
                                    category: str, criteria: dict) -> pd.DataFrame:
        """根据不同标准获取候选样本"""
        # 基础筛选条件
        base_conditions = (day_data['turnover_rate'].notna()) & (day_data['close'] > 0)
        
        # 根据分类类型应用不同的筛选条件
        if category_type == 'nature':
            # 债性分类的筛选条件
            if criteria.get('premium_range'):
                range_value = criteria['premium_range']
                if category == '偏债型':
                    conditions = base_conditions & (day_data['ths_pure_bond_premium_rate_cbond'] < (-5 + range_value))
                elif category == '偏股型':
                    conditions = base_conditions & (day_data['ths_pure_bond_premium_rate_cbond'] > (10 - range_value))
                else:  # 平衡型
                    conditions = base_conditions & \
                               (day_data['ths_pure_bond_premium_rate_cbond'] >= (-5 - range_value)) & \
                               (day_data['ths_pure_bond_premium_rate_cbond'] <= (10 + range_value))
            else:
                conditions = base_conditions
                
        elif category_type == 'premium':
            # 溢价分类的筛选条件
            if criteria.get('premium_range'):
                range_value = criteria['premium_range']
                if category == '双低':
                    conditions = base_conditions & \
                               (day_data['close'] <= (110 + range_value)) & \
                               (day_data['ths_conversion_premium_rate_cbond'] <= (20 + range_value))
                elif category == '低价高溢':
                    conditions = base_conditions & \
                               (day_data['close'] <= (110 + range_value)) & \
                               (day_data['ths_conversion_premium_rate_cbond'] >= (40 - range_value))
                elif category == '高价低溢':
                    conditions = base_conditions & \
                               (day_data['close'] >= (125 - range_value)) & \
                               (day_data['ths_conversion_premium_rate_cbond'] <= (20 + range_value))
                elif category == '双高':
                    conditions = base_conditions & \
                               (day_data['close'] >= (125 - range_value)) & \
                               (day_data['ths_conversion_premium_rate_cbond'] >= (40 - range_value))
                else:  # 普通型
                    # 普通型是不满足其他类型条件的债券
                    other_conditions = \
                        ((day_data['close'] <= 110) & (day_data['ths_conversion_premium_rate_cbond'] <= 20)) | \
                        ((day_data['close'] <= 110) & (day_data['ths_conversion_premium_rate_cbond'] >= 40)) | \
                        ((day_data['close'] >= 125) & (day_data['ths_conversion_premium_rate_cbond'] <= 20)) | \
                        ((day_data['close'] >= 125) & (day_data['ths_conversion_premium_rate_cbond'] >= 40))
                    conditions = base_conditions & ~other_conditions
            else:
                conditions = base_conditions
                
        else:  # 行业分类
            # 行业分类主要依赖于换手率和规模条件
            conditions = base_conditions & \
                        (day_data['level1'] == category)  # 确保属于指定行业
        
        # 应用换手率条件
        if criteria.get('turnover_rate'):
            conditions = conditions & (day_data['turnover_rate'] >= criteria['turnover_rate'])
        elif not criteria.get('dynamic_minimum'):  # 如果不是动态调整阶段，使用默认换手率
            conditions = conditions & (day_data['turnover_rate'] >= self.min_turnover_rate)
        
        # 获取符合条件的样本并按流动性和规模排序
        candidates = day_data[conditions].sort_values(
            ['turnover_rate', 'un_conversion_balance'],
            ascending=[False, False]
        )
        
        # 获取目标样本数
        if category_type == 'nature':
            target = self.sample_config.nature_samples[category]['target']
        elif category_type == 'premium':
            target = self.sample_config.premium_samples[category]['target']
        else:  # 行业分类
            target = self.sample_config.industry_target
        
        # 如果候选样本数量超过目标数，只返回目标数量的样本
        if len(candidates) > target:
            candidates = candidates.head(target)
        
        return candidates
    
    def _supplement_samples(self, day_data: pd.DataFrame, current_samples: set,
                          category_type: str, category: str, date_str: str) -> set:
        """补充样本至最低要求数量，包含动态调整机制"""
        # 获取目标配置
        if category_type == 'nature':
            config = self.sample_config.nature_samples.get(category, {})
        elif category_type == 'premium':
            config = self.sample_config.premium_samples.get(category, {})
        else:  # 行业分类
            config = {'target': self.sample_config.industry_target, 
                     'minimum': self.sample_config.industry_target}
        
        target = config['target']
        absolute_minimum = config['minimum']
        current_count = len(current_samples)
        
        # 如果当前样本数已达到目标数量，直接返回
        if current_count >= target:
            return current_samples
        
        # 如果当前样本数未达到最低要求，保留所有现有样本
        all_candidates = set()
        
        # 逐步尝试不同的放宽策略
        for step in self.sample_config.adjustment_steps:
            candidates = self._get_candidates_with_criteria(
                day_data, category_type, category, step
            )
            new_candidates = set(candidates['trade_code'])
            all_candidates.update(new_candidates)
            
            # 合并现有样本和新候选样本
            combined_samples = current_samples.union(all_candidates)
            combined_count = len(combined_samples)
            
            if combined_count >= target:
                # 达到目标数量
                self.logger.info(f"{date_str} {category}样本数达到目标值({combined_count}/{target})")
                return combined_samples
            elif combined_count >= absolute_minimum:
                # 达到最低要求
                self.logger.warning(
                    f"{date_str} {category}样本数({combined_count})未达理想值({target})，"
                    f"但超过最低要求({absolute_minimum})"
                )
                return combined_samples
        
        # 所有策略都尝试后的处理
        combined_samples = current_samples.union(all_candidates)
        combined_count = len(combined_samples)
        
        if combined_count > 0:
            self.logger.warning(
                f"{date_str} {category}样本数严重不足，仅找到{combined_count}只，"
                f"低于最低要求({absolute_minimum})，将动态调整指数要求"
            )
            self._record_sample_adjustment(date_str, category_type, category, target, combined_count)
            return combined_samples
        else:
            self.logger.error(f"{date_str} {category}无法找到任何合格样本")
            return current_samples
    
    def _record_sample_adjustment(self, date_str: str, category_type: str, 
                                category: str, target: int, actual: int):
        """记录样本数量调整情况"""
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bond.index_sample_adjustment
                (dt, category_type, category, target_count, actual_count)
                VALUES (%s, %s, %s, %s, %s)
            """, (date_str, category_type, category, target, actual))
            conn.commit()

if __name__ == "__main__":
    # 初始化指数计算器
    index_calculator = BondIndustryIndex()
    
    # 清空指数相关表
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        # 1. 先禁用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 2. 清空表
        cursor.execute("TRUNCATE TABLE bond.marketinfo_ebindex")
        cursor.execute("TRUNCATE TABLE bond.basicinfo_ebindex")
        
        # 3. 重新启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        print("已清空指数相关表")
    
    today = datetime.now().strftime('%Y-%m-%d')
    # 生成历史指数
    index_calculator.generate_historical_index('2014-01-01', today)
    
    # # 生成当日指数
    # index_calculator.generate_daily_index() 

    import pandas as pd
import numpy as np
from db_pool import DatabaseConnection
import logging
from datetime import datetime
from tqdm import tqdm
import time

class BondTypeIndexCalculator:
    def __init__(self):
        self.logger = self._setup_logger()
        # 样本管理参数
        self.ma_window = 60  # 60个交易日移动平均
        self.min_continuous_days = 20  # 入池要求连续达标天数
        self.min_turnover_rate = 0.5  # 最低日均换手率(%)
        self.weight_cap = 0.10  # 单只债券权重上限
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _get_bond_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取可转债市场数据"""
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    A.dt,
                    A.trade_code,
                    A.close as close,
                    A.amount as amount,
                    B.ths_bond_balance_bond as balance,
                    A.un_conversion_balance as un_conversion_balance
                FROM yq.marketinfo_equity1 A
                INNER JOIN bond.marketinfo_equity B
                ON A.trade_code=B.trade_code
                AND A.dt=B.dt
                WHERE B.ths_bond_balance_bond > 0
                AND A.trade_code NOT LIKE '%%NQ'
                AND A.dt BETWEEN %s AND %s
            """, (start_date, end_date))
            columns = ['dt', 'trade_code', 'close', 'amount', 'balance', 'un_conversion_balance']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
        return df
    
    def _get_bond_characteristics(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取可转债特性数据"""
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    dt,
                    trade_code,
                    close,
                    amount,
                    pure_premium as ths_pure_bond_premium_rate_cbond,
                    conv_premium as ths_conversion_premium_rate_cbond
                FROM yq.marketinfo_equity1
                WHERE dt BETWEEN %s AND %s
                AND trade_code NOT LIKE '%%NQ'
            """, (start_date, end_date))
            columns = ['dt', 'trade_code', 'close', 'amount', 
                      'ths_pure_bond_premium_rate_cbond', 'ths_conversion_premium_rate_cbond']
            data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)
    
    def _get_stock_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取正股市场数据"""
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    A.dt,
                    C.trade_code as bond_code,
                    A.trade_code as stock_code,
                    A.close as close,
                    A.AMT as amount,
                    A.MKT_CAP_ARD as balance,
                    A.MKT_FREESHARES as un_conversion_balance
                FROM stock.marketinfo A
                INNER JOIN bond.basicinfo_equity B
                ON A.trade_code=B.ths_stock_code_cbond
                INNER JOIN bond.marketinfo_equity C
                ON B.trade_code=C.trade_code
                AND A.dt=C.dt
                WHERE C.ths_bond_balance_bond > 0
                AND B.trade_code NOT LIKE '%%NQ'
                AND A.dt BETWEEN %s AND %s
            """, (start_date, end_date))
            columns = ['dt', 'bond_code', 'stock_code', 'close', 'amount', 'balance', 'un_conversion_balance']
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
        return df
    
    def _calculate_parity_premium(self, df: pd.DataFrame) -> pd.Series:
        """计算平价溢价率"""
        return (1 + df['ths_pure_bond_premium_rate_cbond']) / (1 + df['ths_conversion_premium_rate_cbond']) - 1
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均"""
        metrics = ['parity_premium_rate', 'turnover_rate']
        
        # 计算移动平均
        ma_df = df.groupby('trade_code')[metrics].transform(
            lambda x: x.rolling(window=self.ma_window, min_periods=1).mean()
        )
        
        # 重命名列
        ma_columns = {col: f'{col}_ma60' for col in metrics}
        ma_df.rename(columns=ma_columns, inplace=True)
        
        return pd.concat([df, ma_df], axis=1)
    
    def _check_continuous_qualification(self, df: pd.DataFrame, condition: pd.Series) -> pd.Series:
        """检查连续达标天数"""
        changes = (condition != condition.shift()).astype(int)
        groups = changes.cumsum()
        counts = condition.groupby([df['trade_code'], groups]).transform('cumsum')
        return counts >= self.min_continuous_days
    
    def _get_qualified_samples(self, market_data: pd.DataFrame, chars_data: pd.DataFrame) -> pd.DataFrame:
        """获取偏债型合格样本"""
        # 1. 合并数据
        df = pd.merge(market_data, chars_data, on=['dt', 'trade_code'], how='inner', suffixes=('', '_chars'))
        
        # 2. 计算换手率
        df['turnover_rate'] = (df['amount'] / df['un_conversion_balance']) * 100
        
        # 3. 计算平价溢价率
        df['parity_premium_rate'] = self._calculate_parity_premium(df)
        
        # 4. 计算移动平均
        df = self._calculate_moving_averages(df)
        
        # 5. 计算偏债型条件
        condition = df['parity_premium_rate'] < -20
        
        # 6. 检查连续达标
        df['qualified'] = self._check_continuous_qualification(df, condition)
        
        # 7. 检查流动性
        df['liquidity_qualified'] = df['turnover_rate_ma60'] >= self.min_turnover_rate
        
        # 8. 筛选合格样本
        qualified = df[df['qualified'] & df['liquidity_qualified']]
        
        return qualified[['dt', 'trade_code', 'close', 'amount', 'balance', 'turnover_rate']]
    
    def _calculate_index(self, samples: pd.DataFrame) -> pd.DataFrame:
        """计算指数"""
        if samples.empty:
            return pd.DataFrame()
        
        # 确保数值类型为float
        numeric_columns = ['close', 'amount', 'balance', 'turnover_rate']
        for col in numeric_columns:
            if col in samples.columns:
                samples[col] = samples[col].astype(float)
        
        # 计算加权因子
        samples['weight'] = samples['balance'] / samples.groupby('dt')['balance'].transform('sum')
        samples['weight'] = samples.groupby('dt')['weight'].transform(
            lambda x: np.minimum(x, self.weight_cap) / np.minimum(x, self.weight_cap).sum()
        )
        
        # 计算指数
        result = samples.groupby('dt').agg({
            'close': lambda x: np.average(x, weights=samples.loc[x.index, 'weight']),
            'balance': 'sum',
            'trade_code': 'count',
            'turnover_rate': 'mean'
        }).reset_index()
        
        # 重命名列
        result = result.rename(columns={
            'balance': 'total_balance',
            'trade_code': 'component_count'
        })
        
        return result.sort_values('dt')
    
    def _save_index_market_data(self, index_data: pd.DataFrame, index_code: str):
        """保存指数数据"""
        if index_data.empty:
            self.logger.warning(f"无数据需要保存: {index_code}")
            return
        
        self.logger.info(f"保存 {index_code} 指数数据，共 {len(index_data)} 条记录")
        
        values = [
            (index_code, row['dt'], float(row['close']), float(row['total_balance']),
             int(row['component_count']), float(row['turnover_rate']))
            for _, row in index_data.iterrows()
        ]
        
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO bond.marketinfo_ebindex 
                (trade_code, dt, close, total_balance, component_count, turnover_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                close = VALUES(close),
                total_balance = VALUES(total_balance),
                component_count = VALUES(component_count),
                turnover_rate = VALUES(turnover_rate)
            """, values)
            conn.commit()
    
    def _get_qualified_stocks(self, stock_market_data: pd.DataFrame, qualified_bonds: pd.DataFrame) -> pd.DataFrame:
        """获取合格正股样本"""
        # 1. 筛选对应的正股
        df = stock_market_data[
            stock_market_data['bond_code'].isin(qualified_bonds['trade_code'])
        ].rename(columns={'stock_code': 'trade_code'})
        
        # 2. 计算换手率
        df['turnover_rate'] = (df['amount'] / df['un_conversion_balance']) * 100
        
        # 3. 计算移动平均
        ma_df = df.groupby('trade_code')['turnover_rate'].transform(
            lambda x: x.rolling(window=self.ma_window, min_periods=1).mean()
        )
        df['turnover_rate_ma60'] = ma_df
        
        # 4. 检查流动性
        df['liquidity_qualified'] = df['turnover_rate_ma60'] >= self.min_turnover_rate
        
        # 5. 筛选合格样本
        qualified = df[df['liquidity_qualified']]
        
        return qualified[['dt', 'trade_code', 'close', 'amount', 'balance', 'turnover_rate']]

    def update_indices(self, start_date: str, end_date: str):
        """更新偏债型指数及其正股指数数据"""
        total_start_time = time.time()
        self.logger.info(f"开始更新偏债型指数及其正股指数数据: {start_date} 到 {end_date}")
        
        # 1. 获取数据
        self.logger.info("获取市场数据...")
        bond_market_data = self._get_bond_market_data(start_date, end_date)
        chars_data = self._get_bond_characteristics(start_date, end_date)
        stock_market_data = self._get_stock_market_data(start_date, end_date)
        
        # 2. 获取合格样本
        self.logger.info("筛选合格样本...")
        qualified_bonds = self._get_qualified_samples(bond_market_data, chars_data)
        self.logger.info(f"合格可转债数量: {qualified_bonds['trade_code'].nunique()}")
        
        # 3. 获取对应的正股数据
        self.logger.info("获取正股数据...")
        qualified_stocks = self._get_qualified_stocks(stock_market_data, qualified_bonds)
        self.logger.info(f"对应正股数量: {qualified_stocks['trade_code'].nunique()}")
        
        # 4. 计算指数
        self.logger.info("计算可转债指数...")
        bond_index = self._calculate_index(qualified_bonds)
        self.logger.info(f"可转债指数数据条数: {len(bond_index)}")
        
        self.logger.info("计算正股指数...")
        stock_index = self._calculate_index(qualified_stocks)
        self.logger.info(f"正股指数数据条数: {len(stock_index)}")
        
        # 5. 保存数据
        self.logger.info("保存数据...")
        self._save_index_market_data(bond_index, 'HZEBP001')
        self._save_index_market_data(stock_index, 'HZEBSP001')
        
        total_time = time.time() - total_start_time
        self.logger.info(f"指数数据更新完成，总耗时: {total_time:.2f}秒")

if __name__ == "__main__":
    # 示例使用
    calculator = BondTypeIndexCalculator()
    today = datetime.now().strftime('%Y-%m-%d')
    calculator.update_indices('2015-01-18', today) 