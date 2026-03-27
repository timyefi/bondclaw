import os
import sys
import pandas as pd
import logging
from datetime import datetime
import traceback
from sqlalchemy import create_engine, text
from iFinDPy import *
import time
import numpy as np
from typing import List, Dict, Tuple

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

class UnConversionBalanceCollector:
    """专门用于补充未转股余额数据的采集器"""
    
    def __init__(self, config_num: int = 1):
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.engine = self._create_db_engine()
        self.login_status = False
        self.config_num = config_num
        self.connect()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('un_conversion_balance_collector')
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = os.path.join('logs', f'un_conversion_balance_collector_{datetime.now().strftime("%Y%m%d")}.log')
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
                and A.dt>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                and (B.ths_delist_date_bond is null 
                     or B.ths_delist_date_bond > CURDATE())
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
                return df
        except Exception as e:
            self.logger.error(f"获取可转债代码失败: {str(e)}")
            return pd.DataFrame(columns=['trade_code', 'delist_date', 'list_date'])
            
    def get_existing_data_range(self) -> Tuple[str, str, pd.DataFrame]:
        """获取数据库中已有数据的日期范围和代码列表"""
        try:
            # 首先获取所有符合条件的可转债代码
            bond_df = self.get_bond_codes()
            if bond_df.empty:
                return None, None, pd.DataFrame()
            
            # 获取这些代码中需要补充未转股余额的数据范围
            codes_str = "','".join(bond_df['trade_code'].tolist())
            query = f"""
                SELECT 
                    MIN(dt) as min_date,
                    MAX(dt) as max_date
                FROM marketinfo_equity1
                WHERE trade_code IN ('{codes_str}')
                AND un_conversion_balance IS NULL
            """
            
            with self.engine.connect() as conn:
                date_df = pd.read_sql(query, conn)
                
            if date_df.empty or pd.isna(date_df['min_date'].iloc[0]):
                return None, None, pd.DataFrame()
                
            min_date = date_df['min_date'].iloc[0].strftime('%Y-%m-%d')
            max_date = date_df['max_date'].iloc[0].strftime('%Y-%m-%d')
            
            return min_date, max_date, bond_df
            
        except Exception as e:
            self.logger.error(f"获取数据范围失败: {str(e)}\n{traceback.format_exc()}")
            return None, None, pd.DataFrame()
            
    def collect_un_conversion_balance(self, codes: List[str], start_date: str, end_date: str):
        """采集未转股余额数据"""
        try:
            # 合并所有代码为一个字符串
            codes_str = ','.join(codes)
            
            # 获取未转股余额数据
            result = THS_DS(
                codes_str,
                'ths_un_conversion_balance_cbond',
                '',
                '',
                start_date,
                end_date
            )
            
            if result.data is None:
                self.logger.error(f"获取未转股余额数据失败: {result.errmsg}")
                return None
                
            # 重命名列
            df = result.data
            df = df.rename(columns={
                'time': 'dt',
                'thscode': 'trade_code',
                'ths_un_conversion_balance_cbond': 'un_conversion_balance'
            })
            
            return df
            
        except Exception as e:
            self.logger.error(f"采集未转股余额数据时发生错误: {str(e)}\n{traceback.format_exc()}")
            return None
            
    def update_un_conversion_balance(self, df: pd.DataFrame):
        """更新数据库中的未转股余额数据"""
        try:
            # 确保日期列是字符串类型 YYYY-MM-DD
            df['dt'] = pd.to_datetime(df['dt']).dt.strftime('%Y-%m-%d')
            
            # 确保trade_code是字符串类型
            df['trade_code'] = df['trade_code'].astype(str)
            
            # 将特殊值（inf, -inf）转换为None
            df['un_conversion_balance'] = pd.to_numeric(df['un_conversion_balance'], errors='coerce')
            df['un_conversion_balance'] = df['un_conversion_balance'].replace([np.inf, -np.inf], np.nan)
            
            # 构建更新语句
            update_stmt = """
                UPDATE marketinfo_equity1
                SET un_conversion_balance = :un_conversion_balance
                WHERE trade_code = :trade_code
                AND dt = :dt
            """
            
            # 准备更新数据
            update_data = []
            for _, row in df.iterrows():
                if pd.notna(row['un_conversion_balance']):
                    update_data.append({
                        'trade_code': row['trade_code'],
                        'dt': row['dt'],
                        'un_conversion_balance': row['un_conversion_balance']
                    })
            
            # 执行更新
            if update_data:
                with self.engine.begin() as conn:
                    conn.execute(text(update_stmt), update_data)
                    
            self.logger.info(f"已更新 {len(update_data)} 条未转股余额数据")
            
        except Exception as e:
            self.logger.error(f"更新未转股余额数据失败: {str(e)}\n{traceback.format_exc()}")
            
    def run(self):
        """运行数据补充程序"""
        try:
            # 获取需要补充数据的范围
            start_date, end_date, bond_df = self.get_existing_data_range()
            if bond_df.empty:
                self.logger.info("没有需要补充未转股余额的数据")
                return
                
            self.logger.info(f"开始补充未转股余额数据: {len(bond_df)} 个代码, 日期范围: {start_date} 至 {end_date}")
            
            # 批量处理代码
            batch_size = 10
            for i in range(160, len(bond_df), batch_size):
                batch_df = bond_df.iloc[i:i + batch_size]
                try:
                    self.logger.info(f"处理第 {i//batch_size + 1} 批，共 {len(batch_df)} 个代码")
                    
                    # 获取未转股余额数据
                    batch_codes = batch_df['trade_code'].tolist()
                    df = self.collect_un_conversion_balance(batch_codes, start_date, end_date)
                    if df is None or df.empty:
                        continue
                        
                    # 过滤掉摘牌日期之后的数据
                    filtered_data = []
                    for _, row in df.iterrows():
                        code = row['trade_code']
                        date = pd.to_datetime(row['dt'])
                        delist_date = batch_df[batch_df['trade_code'] == code]['delist_date'].iloc[0]
                        
                        if pd.notna(delist_date) and date >= pd.to_datetime(delist_date):
                            continue
                            
                        filtered_data.append(row)
                    
                    if not filtered_data:
                        continue
                        
                    filtered_df = pd.DataFrame(filtered_data)
                    
                    # 更新数据库
                    self.update_un_conversion_balance(filtered_df)
                    
                    # 避免请求过于频繁
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"处理第 {i//batch_size + 1} 批时发生错误: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"补充未转股余额数据时发生错误: {str(e)}\n{traceback.format_exc()}")
        finally:
            if self.login_status:
                THS_iFinDLogout()
                self.logger.info("同花顺数据接口已登出")

def main():
    collector = UnConversionBalanceCollector(config_num=2)
    collector.run()

if __name__ == "__main__":
    main() 