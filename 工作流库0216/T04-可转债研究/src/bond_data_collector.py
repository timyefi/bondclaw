import os
import sys
import pandas as pd
import logging
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
import traceback
from sqlalchemy import create_engine, text
from iFinDPy import *
import time

# 添加交易绝对理性化工具的配置路径
tools_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                '交易绝对理性化工具', 'config')
sys.path.append(tools_config_path)

THS_CONFIG = {
    'username': 'hznd002',
    'password': '160401'
}
# THS_CONFIG = {
#     'username': 'nylc082',
#     'password': '491448'
# }

class THSBondDataCollector:
    """同花顺可转债数据采集器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.engine = self._create_db_engine()
        self.login_status = False
        
        # 创建数据存储目录
        self.raw_data_dir = os.path.join('data', 'raw')
        self.processed_data_dir = os.path.join('data', 'processed')
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        # 交易日历缓存
        self._trading_days_cache = set()
        self._cache_file = 'trading_days_cache_a.json'
        self._load_trading_days_cache()
        
        # 初始化连接
        self.connect()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('bond_collector')
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = os.path.join('logs', f'bond_collector_{datetime.now().strftime("%Y%m%d")}.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
        
    def _load_config(self) -> dict:
        """加载配置"""
        return {
            'db': {
                'user': 'hz_work',
                'password': 'Hzinsights2015',
                'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                'port': '3306',
                'database': 'yq'
            }
        }
        
    def _create_db_engine(self):
        """创建数据库引擎"""
        db_config = self.config['db']
        conn_str = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        return create_engine(conn_str)
        
    def connect(self):
        """连接同花顺数据接口"""

        try:
            # 如果已经登录，先登出
            if self.login_status:
                THS_iFinDLogout()
                self.login_status = False
                
            # 尝试登录
            retry_count = 0
            while not self.login_status and retry_count < 3:
                login_result = THS_iFinDLogin(THS_CONFIG['username'], THS_CONFIG['password'])
                if login_result == 0:
                    self.login_status = True
                    self.logger.info("同花顺数据接口连接成功")
                    break
                else:
                    retry_count += 1
                    self.logger.error(f"同花顺数据接口连接失败，错误码：{login_result}，第{retry_count}次重试")
                    time.sleep(5)  # 等待5秒后重试
                    
            if not self.login_status:
                raise Exception("同花顺数据接口连接失败，请检查账号密码是否正确")
                
        except Exception as e:
            self.logger.error(f"连接同花顺数据接口时发生错误: {str(e)}")
            raise
            
    def _load_trading_days_cache(self):
        """从文件加载交易日缓存"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self._trading_days_cache = set(cache_data['trading_days'])
                self.logger.info(f"已加载{len(self._trading_days_cache)}个交易日记录")
        except Exception as e:
            self.logger.error(f"加载交易日缓存失败: {str(e)}")
            self._trading_days_cache = set()
            
    def _save_trading_days_cache(self):
        """保存交易日缓存到文件"""
        try:
            cache_data = {
                'trading_days': list(self._trading_days_cache),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self._cache_file, 'w') as f:
                json.dump(cache_data, f)
            self.logger.debug("交易日缓存已保存")
        except Exception as e:
            self.logger.error(f"保存交易日缓存失败: {str(e)}")
            
    def get_bond_codes(self) -> List[str]:
        """获取需要采集的可转债代码"""
        try:
            query = """
                select distinct trade_code
                from bond.marketinfo_equity 
                where ths_bond_balance_bond>0
                and dt>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
                return df['trade_code'].tolist()
        except Exception as e:
            self.logger.error(f"获取可转债代码失败: {str(e)}")
            return []
            
    def collect_bond_data(self, bond_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """采集单个可转债的数据"""
        try:
            # 分别获取每个指标
            indicators_config = [
                {'name': 'ths_bond_close_cbond', 'param': '103'},  # 收盘价需要参数103
                {'name': 'ths_new_bond_amt_cbond', 'param': ''},  # 成交额
                {'name': 'ths_pure_bond_premium_rate_cbond', 'param': ''},  # 纯债溢价率
                {'name': 'ths_pure_bond_ytm_cbond', 'param': ''},  # 纯债到期收益率
                {'name': 'ths_conversion_premium_rate_cbond', 'param': ''},  # 转股溢价率
                {'name': 'ths_conver_pe_cbond', 'param': ''},  # 转股市盈率
                {'name': 'ths_stock_pe_cbond', 'param': ''},  # 正股市盈率
                {'name': 'ths_stock_pb_cbond', 'param': ''},  # 正股市净率
                {'name': 'ths_conver_pb_cbond', 'param': ''}  # 转股市净率
            ]
            
            all_data = []
            
            # 逐个获取指标数据
            for indicator in indicators_config:
                result = THS_DS(
                    bond_code,
                    indicator['name'],
                    indicator['param'],
                    '',
                    start_date,
                    end_date
                )
                
                if result.data is None:
                    self.logger.error(f"获取{indicator['name']}数据失败: {bond_code}, {result.errmsg}")
                    continue
                    
                df = result.data
                if not df.empty:
                    all_data.append(df)
                    
                # 避免请求过于频繁
                time.sleep(0.5)
            
            if not all_data:
                self.logger.warning(f"未获取到任何数据: {bond_code}")
                return None
                
            # 合并所有数据
            final_df = all_data[0]
            for df in all_data[1:]:
                final_df = pd.merge(final_df, df, on=['time', 'thscode'], how='outer')
            
            # 重命名列
            rename_dict = {
                'time': 'dt',
                'thscode': 'trade_code',
                'ths_bond_close_cbond': 'close',
                'ths_new_bond_amt_cbond': 'amount',
                'ths_pure_bond_premium_rate_cbond': 'pure_premium',
                'ths_pure_bond_ytm_cbond': 'ytm',
                'ths_conversion_premium_rate_cbond': 'conv_premium',
                'ths_conver_pe_cbond': 'conv_pe',
                'ths_stock_pe_cbond': 'stock_pe',
                'ths_stock_pb_cbond': 'stock_pb',
                'ths_conver_pb_cbond': 'conv_pb'
            }
            final_df = final_df.rename(columns=rename_dict)
        
            
            return final_df
            
        except Exception as e:
            self.logger.error(f"采集数据时发生错误: {str(e)}\n{traceback.format_exc()}")
            return None
            
    def save_to_file(self, df: pd.DataFrame, bond_code: str, date: str):
        """保存数据到本地文件"""
        try:
            filename = os.path.join(self.raw_data_dir, f"{date}_{bond_code}.csv")
            df.to_csv(filename, index=False)
            self.logger.info(f"数据已保存到文件: {filename}")
        except Exception as e:
            self.logger.error(f"保存数据到文件失败: {str(e)}")
            
    def save_to_database(self, df: pd.DataFrame, table_name: str):
        """保存数据到数据库"""
        try:
            with self.engine.begin() as conn:
                df.to_sql(table_name, conn, if_exists='append', index=False)
            self.logger.info(f"数据已保存到数据库表: {table_name}")
        except Exception as e:
            self.logger.error(f"保存数据到数据库失败: {str(e)}")
            
    def collect_historical_data(self, days: int = 365):
        """采集历史数据"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 获取可转债代码列表
        bond_codes = self.get_bond_codes()
        self.logger.info(f"共获取到 {len(bond_codes)} 个可转债代码")
        
        for bond_code in bond_codes:
            try:
                self.logger.info(f"开始处理可转债: {bond_code}")
                
                # 采集数据
                df = self.collect_bond_data(bond_code, start_date, end_date)
                if df is None or df.empty:
                    continue
                    
                # 按日期保存数据
                for date, group in df.groupby('date'):
                    # 保存到文件
                    self.save_to_file(group, bond_code, date)
                    
                    # 保存到数据库
                    self.save_to_database(group, 'bond_daily_data')
                    
                # 避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"处理可转债 {bond_code} 时发生错误: {str(e)}")
                continue
                
    def __del__(self):
        """析构函数"""
        try:
            if self.login_status:
                THS_iFinDLogout()
                self.logger.info("同花顺数据接口已登出")
        except Exception as e:
            self.logger.error(f"登出同花顺数据接口时发生错误: {str(e)}")