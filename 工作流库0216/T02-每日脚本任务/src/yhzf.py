# -*- coding: utf-8 -*-
"""
金融资负数据取数脚本（简化版）
功能：每月20-30号更新上月数据，基金净申购每天更新
"""

import pandas as pd
import sqlalchemy
from sqlalchemy import text
from datetime import datetime, timedelta
from iFinDPy import *
from WindPy import w

# 数据库连接
sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://hz_work:Hzinsights2015@rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com:3306/yq'
)

# 初始化Wind和同花顺
w.start()
THS_iFinDLogin('nylc082','491448')

def get_last_month_date():
    """获取上个月的最后一天日期"""
    today = datetime.now()
    # 获取本月第一天
    first_day_this_month = today.replace(day=1)
    # 上个月最后一天 = 本月第一天 - 1天
    last_month_end = first_day_this_month - timedelta(days=1)
    return last_month_end

def is_update_period():
    """检查是否在每月20-30号的更新期间"""
    today = datetime.now()
    day = today.day
    return 17 <= day <= 30

def update_financial_data(code, data_type, target_date):
    """
    更新金融资负数据
    
    参数:
    code: 数据代码
    data_type: 1表示Wind接口，2表示同花顺接口
    target_date: 目标日期（上个月最后一天）
    """
    try:
        target_date_str = target_date.strftime('%Y-%m-%d')
        print(f"Fetching data: {code}, Date: {target_date_str}")
        
        if data_type == 1:
            # Wind EDB接口
            error_code, wsd_data = w.edb(code, target_date_str, target_date_str, usedf=True)
            
            if error_code == 0 and not wsd_data.empty:
                # 处理Wind返回的数据
                if wsd_data.index[0] == code:
                    # 单值数据
                    value = wsd_data['CLOSE'].iloc[0]
                else:
                    # 时间序列数据
                    wsd_data.index = pd.to_datetime(wsd_data.index)
                    # 获取目标日期的数据
                    if target_date in wsd_data.index:
                        value = wsd_data.loc[target_date, 'CLOSE']
                    else:
                        # 如果目标日期没有数据，获取最近的有效数据
                        valid_data = wsd_data.dropna()
                        if not valid_data.empty:
                            value = valid_data['CLOSE'].iloc[-1]
                        else:
                            print(f"  No valid data for {code}")
                            return False
                
                # 更新到数据库
                update_database(code, target_date, value)
                return True
            else:
                print(f"  Wind API error: {error_code}")
                return False
                
        else:
            # 同花顺接口
            df = THS_EDB(code, '', target_date_str, target_date_str)
            
            if df.data is not None:
                df = df.data
                if not df.empty and 'time' in df.columns and 'value' in df.columns:
                    # 确保日期类型正确
                    df['time'] = pd.to_datetime(df['time'])
                    # 获取目标日期的数据
                    target_data = df[df['time'].dt.date == target_date.date()]
                    
                    if not target_data.empty:
                        value = target_data['value'].iloc[0]
                        # 更新到数据库
                        update_database(code, target_date, value)
                        return True
                    else:
                        # 如果目标日期没有数据，获取最近的有效数据
                        df = df.dropna(subset=['value'])
                        if not df.empty:
                            value = df['value'].iloc[-1]
                            # 更新到数据库
                            update_database(code, target_date, value)
                            return True
                        else:
                            print(f"  No valid data for {code}")
                            return False
                else:
                    print(f"  THS returned data format is incorrect")
                    return False
            else:
                print(f"  THS API did not return data")
                return False
                
    except Exception as e:
        print(f"  Error fetching data: {e}")
        return False

def update_database(code, date, value):
    """更新数据到金融资负表"""
    try:
        with sql_engine.begin() as connection:
            # 检查列是否存在，如果不存在则添加
            inspector = sqlalchemy.inspect(sql_engine)
            columns = [col['name'] for col in inspector.get_columns('金融资负')]
            
            if code not in columns:
                # 添加新列
                connection.execute(text(f"ALTER TABLE 金融资负 ADD COLUMN {code} FLOAT"))
                print(f"  Added new column: {code}")
            
            # 检查日期记录是否存在
            check_query = "SELECT COUNT(*) as count FROM 金融资负 WHERE dt = :dt"
            result = pd.read_sql(text(check_query), connection, params={'dt': date})
            
            if result.iloc[0]['count'] > 0:
                # 更新现有记录
                update_query = f"UPDATE 金融资负 SET {code} = :value WHERE dt = :dt"
                connection.execute(text(update_query), {'value': value, 'dt': date})
            else:
                # 插入新记录
                insert_query = f"INSERT INTO 金融资负 (dt, {code}) VALUES (:dt, :value) on duplicate key update {code} = :value"
                connection.execute(text(insert_query), {'dt': date, 'value': value})
            
            print(f"  Data updated successfully: {code} = {value}")
            return True
            
    except Exception as e:
        print(f"  Error updating database: {e}")
        return False

def update_fund_data():
    """更新基金净申购数据（每天运行）"""
    try:
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        codes = ['511090.SH', '511130.SH']
        
        print(f"Updating fund net subscription data: {today_str}")
        
        for code in codes:
            wsd_data = w.wsd(code, "mf_netinflow", today_str, today_str, "unit=1")
            
            if wsd_data.ErrorCode == 0 and wsd_data.Data[0]:
                jsg = wsd_data.Data[0][0]
                if not pd.isna(jsg):
                    df = pd.DataFrame({
                        'dt': [today_str],
                        'trade_code': [code],
                        '净申购': [jsg]
                    })
                    
                    with sql_engine.begin() as connection:
                        try:
                            df.to_sql("基金净申购", con=connection, index=False, if_exists='append')
                            print(f"  {code} Fund net subscription data updated successfully: {jsg}")
                        except Exception as e:
                            print(f"  {code} Data may already exist: {e}")
                else:
                    print(f"  {code} No valid data")
            else:
                print(f"  Wind API failed to get {code} data: {wsd_data.ErrorCode}")
                
    except Exception as e:
        print(f"Error updating fund net subscription data: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("Financial Asset-Liability Data Fetching Program (Simplified)")
    print("=" * 50)
    
    # 1. 基金净申购数据每天更新
    print("1. Updating fund net subscription data...")
    update_fund_data()
    
    # 2. 金融资负数据仅在每月20-30号更新
    print("\n2. Checking if financial asset-liability data needs to be updated...")
    if is_update_period():
        print("  Currently in the update period (20th-30th of each month), starting to update financial asset-liability data...")
        
        # 获取上个月最后一天
        target_date = get_last_month_date()
        print(f"  Target update date: {target_date.strftime('%Y-%m-%d')}")
        
        # Wind数据代码列表
        wind_codes = [
            "M0001538","M0001527","M0251904","M0001528","M0001529","M0001530",
            "M0062047","M0062845","M0062846","M0251905","M0001533","M0001534",
            "M0251906","M0251907","M0062848","M0001536","M0001537","M0001557",
            "M0001539","M0061954","M0001540","M0251908","M0001542","M0001545",
            "M0251909","M0001543","M0001547","M0001541","M0001544","M0001548",
            "M0001549","M0001550","M0001551","M0251910","M0251911","M0001552",
            "M0251912","M0061955","M0001554","M0150191","M0062849","M0001556",
            "M0251956","M0251940","M0251941","M0251942","M0251943","M0251944",
            "M0251945","M0251946","M0251947","M0251948","M0251949","M0251950",
            "M0251951","M0251952","M0251953","M0251954","M0251955","M0251977",
            "M0251957","M0251958","M0251959","M0251960","M0251961","M0251962",
            "M0251963","M0251964","M0251965","M0333070","M0333071","M0251966",
            "M0333072","M0251967","M0251968","M0251969","M0251970","M0251971",
            "M0251972","M0251973","M0333073","M0251974","M0251975","M0251976",
            "M0048455","M0048441","M0252060","M0062879","M0048445","M0252061",
            "M0252062","M0062881","M0062876","M0048442","M0048443","M0048444",
            "M0062878","M0252063","M0252064","M0252065","M0252066","M0048451",
            "M0252068","M0048452","M0048453","M0048454","M0048471","M0048456",
            "M0061993","M0048457","M0048466","M0061994","M0061995","M0061996",
            "M0048468","M0150196","M0062883","M0252069","M0048469","M0048470",
            "M0009940","M0043410","M0043412","M0043411","M0043413","M0009947",
            "M0009969","M0043417","M0043418","M0009978","M0043419","M0001380",
            "M0001382","M0001384","M0001386","M0010131","M0001485","M0001486",
            "M0001487","M0001488","M0001489","M0001490","M0001491","M0001492",
            "M0001494","M0001493","M0001495","M0001496","M0001497","M0001504",
            "M0001498","M0001499","M0001500","M5639029","M5639030","M5639031",
            "M5639032","M5639033","M5639034","M5639035","J3426133","M0010125",
            "M5525755","M5525756","M5525757","M5525758","M5525759","M5525760",
            "M5525761","M5525762","M6179494","M6094230","M6094231","Y7375557",
            "M0001705","M0001724","M5449834","M5524595","M5207551",'M0001680',
            'M0001684','M0001685','M0001686','M0001687','M0001688','M0001689',
            'M0001690','M0068054','M0001697','M0001698','M0001699','M0001700',
            'M0001701','M0001702'
        ]
        
        # 同花顺数据代码列表
        ths_codes = [
            'S004345997','S004346069','S004346029','S004345944','S004346101'
        ]
        
        # 更新Wind数据
        print("  Updating Wind data...")
        success_count = 0
        for code in wind_codes:
            if update_financial_data(code, 1, target_date):
                success_count += 1
            # 添加延迟避免请求过于频繁
            import time
            time.sleep(0.1)
        
        print(f"  Wind data update completed, Success: {success_count}/{len(wind_codes)}")
        
        # 更新同花顺数据
        print("  Updating THS data...")
        success_count = 0
        for code in ths_codes:
            if update_financial_data(code, 2, target_date):
                success_count += 1
            # 添加延迟避免请求过于频繁
            import time
            time.sleep(0.1)
        
        print(f"  THS data update completed, Success: {success_count}/{len(ths_codes)}")
        
    else:
        print("  Currently not in the update period (20th-30th of each month), skipping financial asset-liability data update")
    
    print("\nData fetching program execution completed!")

if __name__ == "__main__":
    main()