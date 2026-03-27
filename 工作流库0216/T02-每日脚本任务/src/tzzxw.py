#上交所
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
from sqlalchemy import text
from datetime import datetime,date, timedelta

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)


from datetime import datetime
def process_df(df):
    """
    对DataFrame中的每一列进行处理，尝试将包含逗号的字符串转换为浮点数。
    
    参数:
    - df: pandas DataFrame
    
    返回:
    - 修改后的DataFrame
    """
    # 遍历DataFrame的每一列
    for column in df.columns:
        # 检查列的数据类型是否为对象（通常是字符串）
        try:
            # 尝试将逗号替换为空，并转换为浮点数
            df[column] = df[column].str.replace(',', '')
            # 然后，使用 pd.to_numeric 将处理后的字符串转换为浮点数
            # errors='coerce' 参数会将无法转换的值设置为 NaN
            df[column] = pd.to_numeric(df[column], errors='raise')
            # print(df[column])

        except:
            # 如果转换失败（比如列中包含无法转换为浮点数的字符串），则忽略
            print(1)
    df = df.fillna(0)
    return df
# 获取当前日期
now = datetime.now()

# 提取年份和月份
year = now.year
month = now.month

for month1 in range(month-2,month):
    year1=year
    if month1==-1:
        month1=11
        year1=year-1
    elif month1==0:
        month1=12
        year1=year-1
# for year1 in range(2019, 2025):
#     for month1 in range(1, 13):
        # if year1 == 2024 or (year1==2023 and month1 >= 11):
        #     break
    trade_date = f'{year1}-{month1}'
    print(trade_date)
    url =f"http://query.sse.com.cn/commonQuery.do?jsonCallBack=jsonpCallback73603&isPagination=false&sqlId=COMMON_BOND_SCSJ_SCTJ_TJYB_CYJG_L&TRADEDATE={trade_date}&_=1715595737219"
    post_dict = {
    'jsonCallBack': 'jsonpCallback73603',
    'isPagination': 'false',
    'sqlId': 'COMMON_BOND_SCSJ_SCTJ_TJYB_CYJG_L',
    'TRADEDATE': trade_date,
    '_': '1715595737219',
    }

    headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Cookie': 'gdp_user_id=gioenc-44e594a8%2Ca026%2C5d8a%2C9dg5%2Cc34c2de37dae; ba17301551dcbaf9_gdp_session_id=6f5f16a8-f1c3-4992-9966-1b9419031d7c; ba17301551dcbaf9_gdp_session_id_sent=6f5f16a8-f1c3-4992-9966-1b9419031d7c; ba17301551dcbaf9_gdp_sequence_ids={%22globalKey%22:4%2C%22VISIT%22:2%2C%22PAGE%22:2%2C%22VIEW_CLICK%22:2}',
    'Host': 'query.sse.com.cn',
    'Referer': 'http://bond.sse.com.cn/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
    }

    try:
        response = requests.post(url, headers=headers, json=post_dict,timeout=20)
        df=pd.DataFrame(json.loads(response.content.decode('utf-8')[len('jsonpCallback73603('):-1])['result'])
        df = process_df(df)
        with sql_engine.begin() as _cursor:
            df.to_sql('investor_sh', con=_cursor, if_exists='append', index=False)
    except:
        pass


#深交所
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
from datetime import datetime,date, timedelta
import random

for month1 in range(month-2,month):
    year1=year
    if month1==-1:
        month1=11
        year1=year-1
    elif month1==0:
        month1=12
        year1=year-1
# for year1 in range(2019, 2024):
#     for month1 in range(1, 13):
        # if year1 == 2024 or (year1==2023 and month1 >= 11):
        #     break
    num = random.random()
    num = round(num, 15)
    trade_date = f'{year1}-{month1:02d}'
    print(trade_date)
    url =f"https://bond.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=zqxqcyyb_after&TABKEY=tab1&jyrqStart={trade_date}&jyrqEnd=2016-01&random={num}"
    post_dict = {
    "SHOWTYPE": "JSON",
    "CATALOGID": "zqxqcyyb_after",
    "TABKEY": "tab1",
    "jyrqStart": trade_date,
    "jyrqEnd": trade_date,
    "random": num
    }

    headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Host": "bond.szse.cn",
    "Referer": "https://bond.szse.cn/marketdata/statistics/report/struc/index.html",
    "Sec-Ch-Ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "X-Request-Type": "ajax",
    "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        data = json.loads(response.text)
        dt=data[0]['metadata']['conditions'][0]['defaultValue']
        dt=pd.to_datetime(dt, format='%Y-%m')
        dt=dt+ pd.offsets.MonthEnd(1)
        dt=dt.strftime('%Y-%m-%d')
        # 提取表格数据
        table_data = data[0]['data']
        df=pd.DataFrame(table_data)
        df = process_df(df)
        df['trade_date']=dt
        with sql_engine.begin() as _cursor:
            df.to_sql('investor_sz', con=_cursor, if_exists='append', index=False)
    except:
        pass


#中债
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
import numpy as np
from datetime import datetime,date, timedelta

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
import random


for month1 in range(month-2,month):
    year1=year
    if month1==-1:
        month1=11
        year1=year-1
    elif month1==0:
        month1=12
        year1=year-1
    trade_date = f'{year1}{month1:02d}'
    url =f"https://www.chinabond.com.cn/cbiw/GetMonthReport/GetDataByte"
    post_dict = {
    "sBbly": trade_date,
    "sCode": "06",
    "sWjlx": 3
    }

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Length": "29",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "www.chinabond.com.cn",
        "Origin": "https://www.chinabond.com.cn",
        "Referer": "https://www.chinabond.com.cn/zzsj/zzsj_tjsj/tjsj_tjyb/?level=3",
        "Sec-Ch-Ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.post(url,headers=headers,data= post_dict)
        with open("output.xlsx", "wb") as f:
            f.write(response.content)
        df=pd.read_excel("output.xlsx",header=None)
        mask = np.column_stack([df[col].astype(str).str.contains('国债', na=False) for col in df])
        mask2 = np.column_stack([df[col].astype(str).str.contains('地方政府债', na=False) for col in df])
        mask_total = np.logical_and(mask.any(axis=1), mask2.any(axis=1))

        # 找到第一个满足条件的行的索引
        index = np.where(mask_total)[0][0]

        # 删除这个索引之前的所有行
        df = df.loc[index:]
        df.reset_index(inplace=True,drop=True)
        df.iloc[0, 0]='分类'
        df.columns = df.iloc[0]  # 将第一行的值设置为列名
        df = df.drop(df.index[0]) 

        dt = pd.to_datetime(f"{year1}-{month1}-1")
        dt=dt+ pd.offsets.MonthEnd(1)
        dt=dt.strftime('%Y-%m-%d')
        df['trade_date']=dt
        # df = process_df(df)
        with sql_engine.begin() as _cursor:
            df.to_sql('investor_zz', con=_cursor, if_exists='append', index=False)
    except:
        pass

#上清所
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
import numpy as np
from datetime import datetime,date, timedelta
from io import BytesIO

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
import random

for month1 in range(month-2,month):
    year1=year
    if month1==-1:
        month1=11
        year1=year-1
    elif month1==0:
        month1=12
        year1=year-1
    trade_date = f'{year1}-{month1:02d}'
    url =f"https://www.shclearing.com.cn/shchapp/web/sdocClient/monthListPage"
    post_dict = {
    "title": '',
    "operTime": trade_date,
    "channelId": "ff80808140a43ba80140a45b17320007",
    "limit": 10,
    "start": 0
    }

    headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Length": "83",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "SESSION=NjI2YjQ1OGItNDY2Ny00ODQ4LWE2NDYtYmJlM2Y1MjY2ZTk1; https_waf_cookie=0b4d6496-f988-472be47cdc8658af95a06d686d0bbb7fdca2",
    "Host": "www.shclearing.com.cn",
    "Origin": "https://www.shclearing.com.cn",
    "Referer": "https://www.shclearing.com.cn/sjtj/tjyb/",
    "Sec-Ch-Ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
    }
    try:
        response = requests.post(url,headers=headers,data= post_dict)
        data=json.loads(response.text)
        indices = [0, 6, 5]
        for index in indices:
            try:
                url = 'https://www.shclearing.com.cn/shchapp/web/' + data['data'][index]['downloadExcelUrl']
                break  # 如果成功获取，就跳出循环
            except Exception as e:
                print(f"Failed to get url from data['data'][{index}]['downloadExcelUrl']: {e}")
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Cookie': 'SESSION=NjI2YjQ1OGItNDY2Ny00ODQ4LWE2NDYtYmJlM2Y1MjY2ZTk1; https_waf_cookie=0b4d6496-f988-472be47cdc8658af95a06d686d0bbb7fdca2',
            'Host': 'www.shclearing.com.cn',
            'Referer': 'https://www.shclearing.com.cn/sjtj/tjyb/',
            'Sec-Ch-Ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
        }
    
        # 发送 GET 请求
        response = requests.get(url, headers=headers,timeout=30)

        # 确保请求成功
        response.raise_for_status()

        # 将响应内容读取为 Excel 文件
        data = BytesIO(response.content)

        sheet_names = ["表五", "表5", "投资者持有结构"]

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(data, sheet_name=sheet_name)
                break  # 如果成功读取，就跳出循环
            except Exception as e:
                print(f"Failed to read sheet {sheet_name}: {e}")
                continue
        df.fillna('',inplace=True)
        # df.iloc[2]=df.iloc[2]+df.iloc[3]
        # df.drop(df.index[[0,1,3]], axis=0, inplace=True)
        # df.drop(df.index[0], axis=0, inplace=True)
        df.replace('\n', '', regex=True, inplace=True)
        df.replace('公司信用类债券','',regex=True, inplace=True)
        df.reset_index(inplace=True,drop=True)
        # df = df.drop(df.columns[0],axis=1)
        df.iloc[0, 0]='分类'
        df.columns = df.iloc[0]  # 将第一行的值设置为列名
        
        sql="""
        SHOW COLUMNS FROM yq.investor_sq;
        """
        with sql_engine.begin() as _cursor:
            df0=pd.read_sql(sql,_cursor)
        list0=df0['Field'].tolist()
        print(list0)
        columns0=df.columns.tolist()

        # 假设df和df0已经定义好
        for col_idx, col in enumerate(df.columns):  # 遍历df的每一列
            for element in df.iloc[:,col_idx]:  # 遍历当前列的所有元素
                if element in list0 and element !='' and element is not None:
                    columns0[col_idx]=element
                    print(columns0)
                    break  # 匹配后跳出内层循环，避免对同一列多次重命名
        columns0[1]='分类'
        df.columns=columns0

        def find_first_occurrence(df, search_text='合计'):
            for idx, row in df.iterrows():
                for col_index, cell_value in enumerate(row):
                    if search_text in str(cell_value):
                        return idx, col_index  # 返回匹配的行索引和列名
            return None, None  # 如果没有找到匹配项，则返回两个None

        match_row, match_col = find_first_occurrence(df)

        if match_row is not None and match_col is not None:
            # 根据找到的位置切片DataFrame
            df.reset_index(drop=True, inplace=True)
            df = df.iloc[match_row:, match_col:]
            # 重置索引和列名  
        else:
            print("未找到'合计'所在的单元格")

        dt = pd.to_datetime(f"{year1}-{month1}-1")
        dt=dt+ pd.offsets.MonthEnd(1)
        dt=dt.strftime('%Y-%m-%d')
        df['trade_date']=dt
        # df = process_df(df)
        with sql_engine.begin() as _cursor:
            df.to_sql('investor_sq', con=_cursor, if_exists='append', index=False)

    except Exception as e:
        print(e)
        continue


sql="""UPDATE investor_sq
SET 分类 = REPLACE(REPLACE(分类, '　', ''), ' ', '');"""
with sql_engine.begin() as _cursor:
    _cursor.execute(text(sql))