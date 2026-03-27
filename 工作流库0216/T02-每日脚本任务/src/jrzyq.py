# 获取模块的绝对路径

import sys
import shutil
import random
import sqlalchemy
from sqlalchemy import text
import urllib.parse
from datetime import date, datetime, timedelta
import pandas as pd
import re
import string
import urllib.request
import requests
from urllib import parse
from time import sleep
import os
import json

from fuzzywuzzy import fuzz
from multiprocessing import Pool
from tqdm import tqdm
module_path = r"C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\代码库"

# 检查模块路径是否已经在 sys.path 中，避免重复添加
if module_path not in sys.path:
    # 将模块路径添加到 sys.path 开头，确保优先加载这个路径的模块
    sys.path.insert(0, module_path)
import timai
from timai import get_html_text_and_images, client_hz, summarize_content, automaton, filter_sensitive_words

folder_path = r'D:\2024年\企业预警通\新建未找到文件夹\新建未找到文件夹\新建未找到文件夹'
sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)

sql = """
SELECT A.trade_code,A.fileName,
A.公司名称 as company
from yq.23年财报文件 A
where A.fileName !=''
"""

with sql_engine.begin() as connection:
    df = pd.read_sql(sql, connection)


def sanitize_filename(filename):
    """清理文件名，使其符合Windows文件命名规范"""
    # 替换不允许的字符为下划线
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 注意：此处未处理可能存在的结束点字符（.）连续情况，根据需要进一步处理
    return sanitized


def ocr_database(originfilename, beizhu):
    sql = """
  UPDATE 23年财报文件
  set ocr= :beizhu
  where fileName = :originfilename
  """
    # 构建参数字典
    params = {
        "originfilename": originfilename,
        "beizhu": beizhu
    }
    with sql_engine.begin() as connection:
        connection.execute(text(sql), params)


def download_PDF(fileUrl, fileName):  # 下载pdf
    file_path = os.path.join(folder_path, fileName+".pdf")
    # 检查文件是否已存在，如果存在则不下载
    if os.path.exists(file_path):
        print(f"{fileName}File already exists!")
    else:
        r = requests.get(fileUrl)
        with open(file_path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded: {fileName}.pdf\n")


def update_database(list_keywords, TypeInfo, happenDate, ContentInfo, ai_sum):
    sql = """
  INSERT ignore INTO 金融债舆情监控 (list_keywords,TypeInfo,happenDate,ContentInfo,ai_sum)
  VALUES (:list_keywords, :TypeInfo, :happenDate, :ContentInfo, :ai_sum)
  """
    # 构建参数字典
    params = {
        "list_keywords": list_keywords,
        "TypeInfo": TypeInfo,
        "happenDate": happenDate,
        "ContentInfo": ContentInfo,
        "ai_sum": ai_sum
    }
    with sql_engine.begin() as connection:
        connection.execute(text(sql), params)


def update_database1(trade_code, fileUrl, fileName):
    sql = """
  UPDATE 23年财报文件
  set fileUrl= :fileUrl, fileName= :fileName, ocr='已重下'
  where trade_code = :trade_code
  """
    # 构建参数字典
    params = {
        "trade_code": trade_code,
        "fileUrl": fileUrl,
        "fileName": fileName
    }
    with sql_engine.begin() as connection:
        connection.execute(text(sql), params)


headers_login = {
    '.Aspnetcore.Culture': 'zh-Hans',
    'authority': 'auth.ratingdog.cn',
    'ethod': 'POST',
    'path': '/api/TokenAuth/Authenticate',
    'cheme': 'https',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Content-Length': '100',
    'Content-Type': 'application/json;charset=UTF-8',
    'Devicechannel': 'gclife_bmp_pc',
    'Origin': 'https://www.ratingdog.cn',
    'Priority': 'u=1, i',
    'Ratingdog.Tenantid': '114',
    'Referer': 'https://www.ratingdog.cn/',
    'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
}

# 定义 data
data_login = {
    "UserNameOrEmailAddressOrPhone": "13918339361",
    "internationalPhoneCode": "86",
    "password": "welcome@1"
}
url_login = 'https://auth.ratingdog.cn/api/TokenAuth/Authenticate'
r = requests.post(url_login, headers=headers_login, json=data_login)
accessToken = r.json()['result']['accessToken']

headers_yy = {
    ".Aspnetcore.Culture": "zh-Hans",
    "Accept": "application/json, text/plain, /",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Authorization": f"Bearer {accessToken}",
    "Content-Length": "1121",
    "Content-Type": "application/json; charset=UTF-8",
    "Devicechannel": "gclife_bmp_pc",
    "Origin": "https://www.ratingdog.cn",
    "Priority": "u=1, i",
    "Ratingdog.Tenantid": "114",
    "Referer": "https://www.ratingdog.cn/",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
}


def pro_id(id, headers=headers_yy):
    url = f"https://host.ratingdog.cn/api/services/app/ResearchInfo/GetCiPublicOpinionForView?id={id}"
    data = {
        "id": id
    }
    r = requests.get(url, headers=headers, json=data)
    r = str(r.content, encoding="utf-8")
    r = json.loads(r)
    # 提取关键公司
    if r['result'] is None:
        return None
    keywords = r['result']['miniIssuers']
    list_keywords = ''
    for i in range(len(keywords)):
        list_keywords += keywords[i]['issuerName']+','

    # 发生日期
    happenDate = r['result']['happenDate']
    # 信息类型
    TypeInfo_part1 = r['result'].get('parentPublicOpinionTypeName')
    TypeInfo_part2 = r['result'].get('publicOpinionTypeName')

    TypeInfo = ''
    if TypeInfo_part1 is not None:
        TypeInfo += TypeInfo_part1
    if TypeInfo_part2 is not None:
        TypeInfo += TypeInfo_part2

    # 信息内容
    content, image_texts = get_html_text_and_images(
        html_path=0, html_content=r['result']['publicOpinionContent'])
    commentary = r['result']['commentary']
    if r['result']['commentary'] == None:
        commentary = ''
    if content == None:
        content = ''
    if image_texts == None:
        image_texts = ''
    ContentInfo = commentary+content+str(image_texts)
    content0 = '涉及公司：'+list_keywords+'\n'+'负面信息类型：'+TypeInfo + \
        '\n'+'事件发生日期：'+happenDate+'\n'+'具体负面信息内容：'+ContentInfo
    content0 = filter_sensitive_words(content0, automaton)
    ai_sum = summarize_content(content=content0, type='舆情', client=client_hz)

    return list_keywords, TypeInfo, happenDate, ContentInfo, ai_sum


def pro_yyinfo(dt_start, dt_end, headers=headers_yy):
    dt_start = datetime.strptime(dt_start, "%Y-%m-%d")
    dt_end = datetime.strptime(dt_end, "%Y-%m-%d")
    SkipCount = 0
    dt = dt_start
    while dt <= dt_end:
        dt_str = dt.strftime("%Y-%m-%d")
        dt += timedelta(days=1)
        print(dt_str)
        is_end = 0
        while is_end == 0:
            data = {
                "IsRisk": True,
                "MoodLevels": [],
                "StartDate": dt_str,
                "EndDate": dt_str,
                "Type": "",
                "administrativeDivisionIds": [],
                "industryIds": [
                    "39ff4c48-a257-0b76-71f7-13fee3262f49",
                    "39ff4c48-a260-4c75-895a-5f35fca09011",
                    "39ff4c48-a265-b80e-5c68-87eaf63dc085",
                    "39ff4c48-a268-1697-6aa8-fb097d58c81e",
                    "39ff4c48-a26b-d5c4-49fd-6640cb7ff50e",
                    "39ff4c48-a26e-855a-32ab-1625a06ea28b",
                    "39ff4c48-a271-2834-7830-bdce9b67538e",
                    "39ff4c48-a275-5b66-5db3-1f01ad36c93e",
                    "3a0d0503-23f7-c800-1479-d9612aaf8495",
                    "39ff4c48-a2ad-a3f0-bce5-39bd7b10d006",
                    "39ff4c48-a2b1-6c7b-34bf-68e4304424a0",
                    "39ff4c48-a348-0cf0-aaee-864c8ea41414",
                    "39ff4c48-a34b-2b1d-030e-8af60e1da6e3",
                    "39ff4c48-a34e-40a2-0452-06be2d97dc49",
                    "39ff4c48-a351-5810-1e2e-8197ca5744c6",
                    "39ff4c48-a353-1f9d-7fe2-e3974c9c9e0e",
                    "39ff4c48-a356-9ce2-2f02-53f4e57fc514",
                    "39ff4c48-a359-217b-bfd0-5128f2467f99",
                    "39ff4c48-a35c-c6d1-0715-8c6966db9483",
                    "39ff4c48-a35f-e100-e27e-101edd28245f",
                    "39ffb434-fcd6-5edf-b456-0c656e7e5cf7",
                    "3a12922c-fa86-fef5-5ad5-da6c7fa5f74a",
                    "3a12924d-a88d-e831-e748-dfc3388e958a",
                    "3a129257-9559-a547-37e1-fb1fadd09bb4"],
                "Source": False,
                "MaxResultCount": 30,
                "SkipCount": SkipCount
            }

            url = "https://host.ratingdog.cn/api/services/app/ResearchInfo/GetQueryPublicOpinionsForTenant"
            requests.DEFAULT_RETRIES = 5
            s = requests.session()
            r = requests.post(url, headers=headers, json=data)
            r = str(r.content, encoding="utf-8")
            r = json.loads(r)
            print(r)
            totalCount = r['result']['totalCount']
            if totalCount > 0:
                for item in r['result']['items']:
                    results = pro_id(item['id'])
                    if results is None:
                        continue
                    results = [r or '' for r in results]
                    list_keywords, TypeInfo, happenDate, ContentInfo, ai_sum = results
                    print(ai_sum)
                    update_database(list_keywords, TypeInfo,
                                    happenDate, ContentInfo, ai_sum)
            else:
                is_end = 1
            if SkipCount+30 > totalCount:
                is_end = 1
            else:
                SkipCount += 30


dt_today = datetime.now()
dt_today = dt_today.strftime("%Y-%m-%d")
pro_yyinfo(dt_today, dt_today)

# 加载所有关键词数据到内存中
sql = """
SELECT list_keywords, happenDate 
FROM yq.金融债舆情监控;
"""
with sql_engine.begin() as connection:
    df_keywords = pd.read_sql_query(sql, connection)
df_keywords['happenDate'] = pd.to_datetime(df_keywords['happenDate'])

sql = """
SELECT list_keywords, happenDate 
FROM yq.金融债舆情监控 where list_keywords not like '%%建信人寿%%' and list_keywords not like '%%平安%%' and list_keywords not like '%%新华%%' and (ai_sum like '%%高风险%%' or ai_sum like '%%风险高%%' or ai_sum like '%%中高%%' or ai_sum like '%%紧迫性高%%' or ai_sum like '%%高紧迫性%%' or ai_sum like '%%等级升%%' or ai_sum like '%%等级提%%' or ai_sum like '%%等级上%%');
"""
with sql_engine.begin() as connection:
    df_keywords1 = pd.read_sql_query(sql, connection)
df_keywords1['happenDate'] = pd.to_datetime(df_keywords1['happenDate'])

# 准备发行人列表
sql = "SELECT DISTINCT 发行人 FROM yq.temp_金融债成交"
with sql_engine.begin() as connection:
    df_issuers = pd.read_sql_query(sql, connection)
issuers = df_issuers['发行人'].tolist()


min_date = df_keywords['happenDate'].min()
max_date = df_keywords['happenDate'].max()
# Generate a date range (inclusive of start and end dates)
date_list = pd.date_range(start=min_date, end=max_date, freq='D')

# 步骤1: 预处理关键词列表，创建发行人到关键词的映射
issuer_to_keywords = {}
for issuer in tqdm(issuers, desc="Preprocessing keywords"):
    matched_keywords = set()
    for keywords in df_keywords['list_keywords']:
        for kw in keywords.split(','):
            if fuzz.ratio(issuer, kw.strip()) >= 95:  # 假设匹配度阈值为70%
                matched_keywords.add(kw.strip())
    issuer_to_keywords[issuer] = matched_keywords

# 步骤2: 使用关键词集合进行快速匹配


def process_issuer(issuer, df_keywords, issuer_to_keywords):
    matched_keywords = issuer_to_keywords[issuer]
    issuer_matches = df_keywords[df_keywords['list_keywords'].apply(
        lambda keywords: any(kw in keywords for kw in matched_keywords)
    )]

    # 对每个日期计算出现次数
    issuer_counts = issuer_matches.groupby(pd.Grouper(
        key='happenDate', freq='D')).size().reindex(date_list, fill_value=0)
    issuer_counts = issuer_counts.fillna(0)
    issuer_counts = issuer_counts.rolling(window=180, min_periods=1).sum()
    return issuer_counts


issuer_counts = []
for issuer in tqdm(issuers, desc="Processing issuers", dynamic_ncols=True):
    issuer_counts.append(process_issuer(
        issuer, df_keywords, issuer_to_keywords))
# with Pool() as p:
#     issuer_counts = list(tqdm(p.imap_unordered(process_issuer, issuers), total=len(issuers), desc="Processing issuers",dynamic_ncols=True))


# 将结果合并成DataFrame
df_results = pd.concat([pd.Series(counts, name=issuer)
                       for issuer, counts in zip(issuers, issuer_counts)], axis=1)
df_results.index.name = '日期'
df_results.columns.name = '发行人'
df_results.reset_index(inplace=True)
df_results = df_results.melt(
    id_vars='日期', var_name='发行人', value_name='近180天负面次数')

# 排序
df_results.sort_values(by=['日期', '发行人'], inplace=True)
df_results['dt'] = pd.to_datetime(df_results['日期'])
with sql_engine.begin() as connection:
    df_results.to_sql('金融债负面监测结果', con=connection,
                      if_exists='replace', index=False)

# 单独统计中高风险次数
# 步骤1: 预处理关键词列表，创建发行人到关键词的映射
issuer_to_keywords = {}
for issuer in tqdm(issuers, desc="Preprocessing keywords"):
    matched_keywords = set()
    for keywords in df_keywords1['list_keywords']:
        for kw in keywords.split(','):
            if fuzz.ratio(issuer, kw.strip()) >= 95:  # 假设匹配度阈值为70%
                matched_keywords.add(kw.strip())
    issuer_to_keywords[issuer] = matched_keywords

issuer_counts = []
for issuer in tqdm(issuers, desc="Processing issuers", dynamic_ncols=True):
    issuer_counts.append(process_issuer(
        issuer, df_keywords1, issuer_to_keywords))
# with Pool() as p:
#     issuer_counts = list(tqdm(p.imap_unordered(process_issuer, issuers), total=len(issuers), desc="Processing issuers",dynamic_ncols=True))


# 将结果合并成DataFrame
df_results = pd.concat([pd.Series(counts, name=issuer)
                       for issuer, counts in zip(issuers, issuer_counts)], axis=1)
df_results.index.name = '日期'
df_results.columns.name = '发行人'
df_results.reset_index(inplace=True)
df_results = df_results.melt(
    id_vars='日期', var_name='发行人', value_name='近180天中高风险负面次数')

# 排序
df_results.sort_values(by=['日期', '发行人'], inplace=True)
df_results['dt'] = pd.to_datetime(df_results['日期'])
with sql_engine.begin() as connection:
    df_results.to_sql('金融债中高负面监测结果', con=connection,
                      if_exists='replace', index=False)

sql_commands = [
    """ALTER TABLE yq.金融债中高负面监测结果
    MODIFY COLUMN 日期 DATE,
    MODIFY COLUMN dt DATE,
    MODIFY COLUMN 发行人 VARCHAR(100);
    """,
    """ALTER TABLE yq.金融债中高负面监测结果
    ADD PRIMARY KEY (日期, 发行人);
    """,
    """ALTER TABLE yq.金融债负面监测结果
    MODIFY COLUMN 日期 DATE,
    MODIFY COLUMN dt DATE,
    MODIFY COLUMN 发行人 VARCHAR(100);
    """,
    """ALTER TABLE yq.金融债负面监测结果
    ADD PRIMARY KEY (日期, 发行人);
    """
]

with sql_engine.begin() as connection:
    for command in sql_commands:
        connection.execute(text(command))
