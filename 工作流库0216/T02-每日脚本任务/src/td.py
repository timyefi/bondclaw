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


with open(r"code1.json", 'rb') as f:
    encoding = chardet.detect(f.read())['encoding']
with open(r"code1.json", 'r', encoding=encoding) as f:
    df_code = json.load(f)
df_code=df_code['data']
results = []
for df in df_code:
    city_info = {
            "省份": df['enumName'],
            "省份代码": df['enumValue']
        }
    results.append(city_info)
results_df = pd.DataFrame(results)

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine.connect()

def find_dgSj(json_obj, path=[]):
    try:
        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                if key == "cjJg":
                    return value
                else:
                    new_path = path + [key]
                    result = find_dgSj(value, new_path)
                    # print(key)
                    if result is not None:
                        return result
        elif isinstance(json_obj, list):
            for value in json_obj:
                result = find_dgSj(value, path)
                if result is not None:
                    return result
    except Exception as e:
        print(str(e))
        print(f"失败finddgsj")
    return None

def insert_err(code,pagenum):
    global proxies
    global run_count
    global start_time
    try:
        _db = pymysql.connect(host="rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com", user="qye",password="Hz123456", db="bond", charset='utf8')
        _cursor = _db.cursor()
        query = "INSERT IGNORE INTO err_landinfo (code,pagenum) VALUES (%s,%s)"
        data = (code,pagenum)
        _cursor.execute(query, data)
        _db.commit()
    except Exception as e:
        print(str(e))
        print(f"失败i1")
        insert_err(code,pagenum)

def insert_err1(gdGuid):
    global proxies
    global run_count
    global start_time
    try:
        _db = pymysql.connect(host="rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com", user="qye",password="Hz123456", db="bond", charset='utf8')
        _cursor = _db.cursor()
        query = "INSERT IGNORE INTO err_landinfo1 (gdGuid) VALUES (%s)"
        data = (gdGuid)
        _cursor.execute(query, data)
        _db.commit()
    except Exception as e:
        print(str(e))
        print(f"失败i2")
        insert_err1(gdGuid)

def insert_cjjg(gdGuid,df,cjjg):
    global proxies
    global run_count
    global start_time
    try:
        _db = pymysql.connect(host="rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com", user="qye",password="Hz123456", db="bond", charset='utf8')
        _cursor = _db.cursor()
        query = "UPDATE landinfo SET company = %s , cjjg= %s WHERE gdGuid = %s;"
        query1 = "UPDATE landinfo1 SET data = %s WHERE gdGuid = %s;"
        a=json.loads(df)
        if 'srDw' in a['relate'][0]:
            company=a['relate'][0]['srDw']
        elif 'srr' in a['data']:
            company=a['data']['srr']
        else:
            company=''
        data = [company,cjjg,gdGuid]
        data1 = [df,gdGuid]
        _cursor.execute(query, data)
        _cursor.execute(query1, data1)
        _db.commit() 
    except Exception as e:
        print(str(e))
        print(f"失败i3")
        insert_cjjg(gdGuid,df,cjjg)

def insert_whole(df):
    global proxies
    global run_count
    global start_time
    try:
        _db = pymysql.connect(host="rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com", user="qye",password="Hz123456", db="bond", charset='utf8')
        _cursor = _db.cursor()
        query = "INSERT IGNORE INTO landinfo_whole (data) VALUES (%s)"
        data = [df] 
        _cursor.execute(query, data)
        _db.commit() 
    except Exception as e:
        print(str(e))
        print(f"失败i4")
        insert_whole(df)
        
def insert_land(df,df_gd):
    global proxies
    global run_count
    global start_time
    df=df.where(pd.notna(df), None)
    try:
        # 连接到 MySQL 数据库
        _db = pymysql.connect(host="rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com", user="qye", password="Hz123456", db="bond", charset='utf8')
        _cursor = _db.cursor()

        # 定义插入语句
        query = "INSERT IGNORE INTO landinfo (gdGuid, xzqDm, tdZl, gyFs, gyMj, tdYt, qdRq, xzqFullName) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        query1 = "INSERT IGNORE INTO landinfo1 (gdGuid) VALUES (%s)"
        # 遍历 DataFrame 的每一行
        for index, row in df.iterrows():
            if row['gdGuid'] in df_gd:
                continue
            # 获取当前行的数据
            data = (row['gdGuid'], row['xzqDm'], row['tdZl'], row['gyFs'], row['gyMj'], row['tdYt'], row['qdRq'], row['xzqFullName'])
            data1= (row['gdGuid'])
            # 执行插入操作
            _cursor.execute(query, data)
            _cursor.execute(query1, data1)

        # 提交事务
        _db.commit()

    except Exception as e:
        print('失败i5')
        print(e)
        sleep(1)
        insert_land(df)

def get_list(code,start_date,end_date,pagenum):
    global proxies
    global run_count
    global start_time
    url = "https://api.landchina.com/tGdxm/result/list"
    post_dict = {
    "pageNum": pagenum,
    "pageSize": 40,
    "xzqDm": code,
    "startDate": start_date,
    "endDate": end_date
    }
 
    headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    try:
        response = requests.post(url, headers=headers, json=post_dict,proxies=proxies,timeout=20)
        if 'data' not in response.text:
            if 'hasNextPage' not in response.text or 'list' not in response.text:
                return ''
            else:
                print(f"无'data'信息{code}-{pagenum}")
                sleep(1)
                run_count+=1
                if run_count<=10:
                    get_list(code,start_date, end_date,pagenum,proxies)
                else:
                    elapsed_time = time.time() - start_time
                    if elapsed_time>=60:
                        start_time= time.time()
                        run_count=0
                    else:
                        if run_count>5:
                            sys.exit(1)
                    sleep(10)
                    response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                    proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                    proxies = {'http': proxy, 'https': proxy}
                    get_list(code,start_date, end_date,pagenum,proxies)
        else:
            return response
    except Exception as e:
        sleep(1)
        print('失败get_list')
        print(e)
        

def get_content(gdGuid):
    global proxies
    global run_count
    global start_time
    url = "https://api.landchina.com/tGdxm/result/detail"
    post_dict = {
    "gdGuid": gdGuid
    }
 
    headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    run_count1=0
    while run_count1<=25:
        run_count1+=1
        try:
            response = requests.post(url, headers=headers, json=post_dict, proxies=proxies, timeout=10)
            sleep(random.uniform(1, 3))
            if '5c8f40a2-bd2b-4119-a404-af3283225661' in response.text:
                try:
                    if run_count1<=10:
                        continue
                    else:
                        if run_count>10:
                            sys.exit(1)
                        sleep(30)
                        response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                        proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                        proxies = {'http': proxy, 'https': proxy} 
                        run_count+=1
                except Exception as e:
                    print(e)
                    print('失败getcontent1')
                continue
            if 'gdGuid' in response.text:
                try:
                    cjjg=find_dgSj(response.json())
                except Exception as e:
                    cjjg=0
                    print(e)
                    print('失败getcontent2')
            return json.dumps(response.json()),cjjg
            # Process the response as usual...
        except Exception as e:
            print(e)
            print('失败getcontent3')
            return '',''


end_date = datetime.now()
start_date = end_date - timedelta(days=3)
dt=start_date.strftime("%Y-%m-%d")
end_date = end_date + timedelta(days=3)
# 将日期时间格式化为 "YYYY-MM-DD HH:MM:SS" 格式
end_date = end_date.strftime("%Y-%m-%d 00:00:00")
# 计算下一天的日期
start_date = start_date.strftime("%Y-%m-%d 00:00:00")
df_gd=pd.read_sql(f"""select distinct gdGuid from bond.landinfo where qdRq>'{dt}'""",_cursor)
df_gd=df_gd['gdGuid'].tolist()
# 初始化 proxies 变量
proxies = {}
chongfu=0
run_count = 0
start_time = time.time()
if __name__ == '__main__':
    df_jl=pd.DataFrame()
    new_df1=results_df
    for code in results_df['省份代码']:
        pagecount=1000
        pagenum=1
        while pagenum>0 and pagecount>0:
            try:
                response=get_list(code,start_date, end_date,pagenum)
                new_df=pd.DataFrame(response.json()['data']['list'])
                if 'null' in response.text or 'None' in response.text or response.json()['data']['list']==[]:
                    print(f'{code}-{pagenum}无内容')
                    insert_err(code,pagenum)
                    if response.json()['data']['hasNextPage']==False:
                        pagenum=0
                        print(f"开始找下一code")
                    else:
                        pagenum+=1
                        pagecount=pagecount-1
                        print(f"开始找{code}-{pagenum}")
                    continue
                elif new_df.iloc[0,0]==new_df1.iloc[0,0]:
                    print(f"出现重复结果{code}-{pagenum}")
                    chongfu+=1
                    if chongfu<=3:
                        # pagenum=pagenum-1
                        try:
                            run_count+=1
                            elapsed_time = time.time() - start_time
                            if elapsed_time>=60:
                                start_time= time.time()
                                run_count=0
                            else:
                                if run_count>=10:
                                    sys.exit(1)
                            start_time = time.time()
                            response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                            proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                            proxies = {'http': proxy, 'https': proxy} 
                            sleep(1)
                        except Exception as e:
                            print(e)
                            print('失败w1')
                            sleep(1)
                    else:
                        pagenum=0
                        chongfu=0
                        print(f"开始找下一code")
                    continue
                else:
                    insert_land(new_df,df_gd)
                    print(f'{code}-{pagenum}搞定')
                    new_df1=new_df
                    sleep(random.uniform(5, 10)) 
                    if response.json()['data']['hasNextPage']==False:
                        pagenum=0
                        print(f"开始找下一code")
                    else:
                        pagenum+=1
                        pagecount=pagecount-1
                        print(f"开始找{code}-{pagenum}")
                     
            except Exception as e:
                print(e)
                print(f"失败w2")
                try:
                    run_count+=1
                    elapsed_time = time.time() - start_time
                    if elapsed_time>=60:
                        start_time= time.time()
                        run_count=0
                    else:
                        if run_count>=10:
                            sys.exit(1)
                    response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                    proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                    proxies = {'http': proxy, 'https': proxy} 
                    sleep(1)
                except Exception as e:
                    print(e)
                    print('失败w3')
                    sleep(1)

df_jl=pd.read_sql("""select distinct gdGuid from bond.landinfo1 WHERE data is NULL""",_cursor)  
if __name__ == '__main__':
    total_df=pd.DataFrame()
    count_1=0
    test=0
    test1=0
    pickle_num=1
    
    for index, gdGuid in enumerate(df_jl['gdGuid']):
        count_2=0
        print(index)
        is_done=0
        while is_done==0:
            count_2+=1
            try:
                new_df=''
                new_df,cjjg=get_content(gdGuid)
                if new_df=='':
                    try:
                        if count_2<=10:
                            continue
                        else:
                            if run_count>10:
                                sys.exit(1)
                            sleep(30)
                            response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                            proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                            proxies = {'http': proxy, 'https': proxy} 
                            run_count+=1
                    except Exception as e:
                        print('失败w1')
                        print(e)
                    continue
            except Exception as e:
                print(e)
                print(f"失败w2")
                try:
                    if count_2<=10:
                        continue
                    else:
                        if run_count>10:
                            sys.exit(1)
                        sleep(30)
                        response = requests.get('http://pandavip.xiongmaodaili.com/xiongmao-web/sdApi/sdl?secret=b725545f43b16507ef7fd77200c5ee82&orderNo=SDL20231217071812wQPYpvaU&count=1&isTxt=0&proxyType=1&noTime=1&removal=0&provinceIds=&cityIds=&returnAccount=1', timeout=1)
                        proxy='http://'+response.json()['obj'][0]['ip']+':'+response.json()['obj'][0]['port']
                        proxies = {'http': proxy, 'https': proxy} 
                        run_count+=1
                except Exception as e:
                    print(e)
                    print(f"失败w3")
            if new_df!='':
                try:
                    insert_cjjg(gdGuid,new_df,cjjg)
                    count_1+=1
                    run_count=0
                    print(f'{index}插入成功-{count_1}')
                    is_done=1
                except Exception as e:
                    print(str(e))
                    print(f"失败w4")
            else:
                test=0
                insert_err1(gdGuid)
                is_done=1