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
import numpy as np

# 添加交易绝对理性化工具的配置路径
tools_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                '交易绝对理性化工具', 'config')
sys.path.append(tools_config_path)

THS_CONFIG1 = {
    'username': 'hznd002',
    'password': '160401'
}
THS_CONFIG2 = {
    'username': 'nylc082',
    'password': '491448'
}

class THSBondDataCollector:
    """同花顺可转债数据采集器"""
    
    def __init__(self,config_num:int=1):
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.engine = self._create_db_engine()
        self.login_status = False
        self.config_num = config_num
        
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
        
    def _create_db_engine(self,config_num:int=1):
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
                if self.config_num == 1:
                    login_result = THS_iFinDLogin(THS_CONFIG1['username'], THS_CONFIG1['password'])
                else:
                    login_result = THS_iFinDLogin(THS_CONFIG2['username'], THS_CONFIG2['password'])
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
            
    def get_bond_codes(self) -> pd.DataFrame:
        """获取需要采集的可转债代码
        
        Returns:
            pd.DataFrame: 包含 trade_code、delist_date 和 list_date 的 DataFrame
        """
        try:
            query = """
                select distinct A.trade_code,
                B.ths_delist_date_bond as delist_date,
                B.ths_listed_date_bond as list_date
                from bond.marketinfo_equity A
                inner join bond.basicinfo_equity B
                on A.trade_code=B.trade_code
                where A.ths_bond_balance_bond>0
                and A.trade_code not like 'S%%'
                and A.trade_code not like '%%NQ'
                and A.trade_code not like '%%.00'
                and A.trade_code not like '%%ZJEE'
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
                return df
        except Exception as e:
            self.logger.error(f"获取可转债代码失败: {str(e)}")
            return pd.DataFrame(columns=['trade_code', 'delist_date', 'list_date'])
            
    def collect_bond_data(self, bond_codes: List[str], start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """采集单个或少量可转债的数据"""
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
                {'name': 'ths_conver_pb_cbond', 'param': ''},  # 转股市净率
                {'name': 'ths_un_conversion_balance_cbond', 'param': ''}  # 未转股余额
            ]
            
            codes_str = ','.join(bond_codes)
            all_data = []
            
            # 逐个获取指标数据
            for indicator in indicators_config:
                result = THS_DS(
                    codes_str,
                    indicator['name'],
                    indicator['param'],
                    '',
                    start_date,
                    end_date
                )
                
                if result.data is None:
                    self.logger.error(f"获取{indicator['name']}数据失败: {codes_str}, {result.errmsg}")
                    continue
                    
                df = result.data
                if not df.empty:
                    all_data.append(df)
                    
                # 避免请求过于频繁
                time.sleep(0.2)
            
            if not all_data:
                self.logger.warning(f"未获取到任何数据: {codes_str}")
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
                'ths_conver_pb_cbond': 'conv_pb',
                'ths_un_conversion_balance_cbond': 'un_conversion_balance'
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
        """保存数据到数据库，使用 INSERT ... ON DUPLICATE KEY UPDATE 处理重复数据"""
        try:
            # 确保日期列是字符串类型 YYYY-MM-DD
            df['dt'] = pd.to_datetime(df['dt']).dt.strftime('%Y-%m-%d')
            
            # 确保trade_code是字符串类型
            df['trade_code'] = df['trade_code'].astype(str)
            
            update_columns = [col for col in df.columns if col not in ['dt', 'trade_code']]
            # 转换数值列，处理无效数据为 None
            for col in update_columns:
                if col in df.columns:
                    # 先转换为float，无效值设为NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # 将特殊值（inf, -inf）转换为None
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            
            # 构建 ON DUPLICATE KEY UPDATE 子句
            update_stmt = ', '.join([f"{col} = VALUES({col})" for col in update_columns])
            
            # 使用参数字典而不是元组列表
            data_dicts = []
            for _, row in df.iterrows():
                row_dict = {}
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value) or value in [np.inf, -np.inf]:
                        row_dict[col] = None
                    else:
                        row_dict[col] = value
                data_dicts.append(row_dict)
            
            # 构建完整的 INSERT 语句，使用命名参数
            columns = list(df.columns)
            placeholders = [f":{col}" for col in columns]
            insert_stmt = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {update_stmt}
            """
            
            # 执行插入
            with self.engine.begin() as conn:
                conn.execute(text(insert_stmt), data_dicts)
                
        except Exception as e:
            self.logger.error(f"保存数据到数据库失败: {str(e)}\n{traceback.format_exc()}")
            
    def check_existing_data(self, bond_codes: List[str], start_date: str, end_date: str) -> Dict[str, List[str]]:
        """检查数据库中已存在的数据
        
        Returns:
            Dict[str, List[str]]: 键为转债代码，值为该转债已存在数据的日期列表
        """
        try:
            placeholders = ','.join(['%s'] * len(bond_codes))
            query = """
                SELECT trade_code, DATE_FORMAT(dt, '%%Y-%%m-%%d') as dt
                FROM marketinfo_equity1
                WHERE trade_code IN ({})
                AND dt BETWEEN %s AND %s
            """.format(placeholders)
            
            # 将参数转换为元组
            params = tuple(bond_codes) + (start_date, end_date)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            
            # 将结果转换为字典格式
            existing_data = {}
            for code in bond_codes:
                code_data = df[df['trade_code'] == code]
                existing_data[code] = code_data['dt'].tolist()  # 直接使用字符串格式的日期
            
            return existing_data
            
        except Exception as e:
            self.logger.error(f"检查已存在数据失败: {str(e)}\n{traceback.format_exc()}")
            return {code: [] for code in bond_codes}

    def collect_bond_data_batch(self, bond_codes: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """批量采集多个可转债的数据"""
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
                {'name': 'ths_conver_pb_cbond', 'param': ''},  # 转股市净率
                {'name': 'ths_un_conversion_balance_cbond', 'param': ''}  # 未转股余额
            ]
            
            # 合并所有代码为一个字符串，用逗号分隔
            codes_str = ','.join(bond_codes)
            all_data = []
            
            # 逐个获取指标数据
            for indicator in indicators_config:
                result = THS_DS(
                    codes_str,
                    indicator['name'],
                    indicator['param'],
                    '',
                    start_date,
                    end_date
                )
                
                if result.data is None:
                    self.logger.error(f"获取{indicator['name']}数据失败: {codes_str}, {result.errmsg}")
                    continue
                    
                df = result.data
                if not df.empty:
                    all_data.append(df)
                    
                # 避免请求过于频繁
                time.sleep(0.5)
            
            if not all_data:
                self.logger.warning(f"未获取到任何数据: {codes_str}")
                return {}
                
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
                'ths_conver_pb_cbond': 'conv_pb',
                'ths_un_conversion_balance_cbond': 'un_conversion_balance'
            }
            final_df = final_df.rename(columns=rename_dict)
            
            # 按转债代码分组返回
            result_dict = {}
            for code in bond_codes:
                code_data = final_df[final_df['trade_code'] == code]
                if not code_data.empty:
                    result_dict[code] = code_data
            
            return result_dict
            
        except Exception as e:
            self.logger.error(f"批量采集数据时发生错误: {str(e)}\n{traceback.format_exc()}")
            return {}

    def collect_historical_data(self, start_date: str, end_date: str):
        """采集历史数据"""
        
        # 获取可转债代码列表
        bond_df = self.get_bond_codes()
        total_codes = len(bond_df)
        self.logger.info(f"共获取到 {total_codes} 个可转债代码")
        
        # 加载交易日历
        try:
            with open('trading_days_cache_a.json', 'r') as f:
                trading_days = json.load(f)['trading_days']
            # 过滤出指定日期范围内的交易日
            trading_days = [day for day in trading_days 
                          if start_date <= day <= end_date]
            trading_days = sorted(trading_days)
            self.logger.info(f"日期范围内共有 {len(trading_days)} 个交易日")
        except Exception as e:
            self.logger.error(f"加载交易日历失败: {str(e)}")
            return
        
        # 批量处理代码
        batch_size = 100
        total_batches = (total_codes + batch_size - 1) // batch_size
        processed_codes = 0
        total_missing_dates = 0
        
        for i in range(0, len(bond_df), batch_size):
            batch_df = bond_df.iloc[i:i + batch_size]
            batch_num = i // batch_size + 1
            try:
                self.logger.info(f"开始处理第 {batch_num}/{total_batches} 批可转债，共 {len(batch_df)} 个")
                
                # 检查已存在的数据
                batch_codes = batch_df['trade_code'].tolist()
                existing_data = self.check_existing_data(batch_codes, start_date, end_date)
                
                # 过滤出需要更新的代码和日期
                codes_to_update = {}
                batch_missing_dates = 0
                for _, row in batch_df.iterrows():
                    code = row['trade_code']
                    delist_date = pd.to_datetime(row['delist_date']).strftime('%Y-%m-%d') if pd.notna(row['delist_date']) else None
                    list_date = pd.to_datetime(row['list_date']).strftime('%Y-%m-%d') if pd.notna(row['list_date']) else None
                    existing_dates = set(existing_data.get(code, []))
                    
                    # 确定数据采集的起止日期
                    code_start_date = max(list_date, start_date) if list_date else start_date
                    code_end_date = min(end_date, delist_date) if delist_date else end_date
                    
                    # 从交易日列表中筛选需要获取数据的日期
                    dates_to_fetch = [
                        day for day in trading_days
                        if code_start_date <= day <= code_end_date
                        and day not in existing_dates
                    ]
                    
                    if dates_to_fetch:  # 如果有需要获取的日期
                        # 获取日期范围的最小值和最大值
                        min_date = min(dates_to_fetch)
                        max_date = max(dates_to_fetch)
                        codes_to_update[code] = {
                            'start_date': min_date,
                            'end_date': max_date,
                            'missing_dates': set(dates_to_fetch),  # 用于后续过滤
                            'delist_date': delist_date
                        }
                        batch_missing_dates += len(dates_to_fetch)
                
                if not codes_to_update:
                    self.logger.info(f"批次 {batch_num}/{total_batches}: 所有数据都已存在，跳过此批次")
                    processed_codes += len(batch_df)
                    continue
                
                self.logger.info(f"批次 {batch_num}/{total_batches}: 需要更新 {len(codes_to_update)} 个代码，共 {batch_missing_dates} 个缺失日期")
                
                # 对每个代码获取数据
                for idx, (code, info) in enumerate(codes_to_update.items(), 1):
                    self.logger.info(f"批次 {batch_num}/{total_batches} - 处理代码 {code} ({idx}/{len(codes_to_update)})")
                    self.logger.info(f"获取日期范围: {info['start_date']} 至 {info['end_date']}")
                    
                    df = self.collect_bond_data([code], info['start_date'], info['end_date'])
                    
                    if df is not None and not df.empty:
                        saved_dates = 0
                        total_dates = len(info['missing_dates'])
                        # 按日期保存数据
                        for date, group in df.groupby('dt'):
                            # 确保日期是字符串格式
                            date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
                            # 如果该日期不在缺失列表中或超过摘牌日期，跳过
                            if (date_str not in info['missing_dates'] or 
                                (info['delist_date'] and date_str >= info['delist_date'])):
                                continue
                            # 保存到数据库
                            self.save_to_database(group, 'marketinfo_equity1')
                            saved_dates += 1
                        
                        self.logger.info(f"已保存 {saved_dates}/{total_dates} 个日期的数据")
                    else:
                        self.logger.warning(f"代码 {code} 未获取到任何数据")
                    
                    # 避免请求过于频繁
                    time.sleep(0.2)
                
                processed_codes += len(batch_df)
                total_missing_dates += batch_missing_dates
                overall_progress = (processed_codes / total_codes) * 100
                self.logger.info(f"总体进度: {overall_progress:.2f}% ({processed_codes}/{total_codes} 个代码)")
                self.logger.info(f"累计处理缺失日期数: {total_missing_dates}")
                
            except Exception as e:
                self.logger.error(f"处理第 {batch_num}/{total_batches} 批可转债时发生错误: {str(e)}\n{traceback.format_exc()}")
                continue
        
        self.logger.info(f"数据采集完成！共处理 {processed_codes} 个代码，{total_missing_dates} 个缺失日期")

    def __del__(self):
        """析构函数"""
        try:
            if self.login_status:
                THS_iFinDLogout()
                self.logger.info("同花顺数据接口已登出")
        except Exception as e:
            self.logger.error(f"登出同花顺数据接口时发生错误: {str(e)}")

def main():
    collector = THSBondDataCollector(config_num = 1)
    collector.collect_historical_data(start_date='2014-01-01', end_date='2025-01-17')

if __name__ == "__main__":
    main()