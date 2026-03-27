import json
import os
from time import sleep
from urllib import parse
import requests
import urllib.request
import string
import re
import pandas as pd
from datetime import date, datetime,timedelta
import urllib.parse
from sqlalchemy import text
import sqlalchemy
import random
import shutil
import sys
import os

# 获取模块的绝对路径
module_path = r"C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\代码库"

# 检查模块路径是否已经在 sys.path 中，避免重复添加
if module_path not in sys.path:
    # 将模块路径添加到 sys.path 开头，确保优先加载这个路径的模块
    sys.path.insert(0, module_path)

import timai
from timai import get_html_text_and_images,client_hz,summarize_content,automaton,filter_sensitive_words

folder_path=r'D:\2024年\企业预警通\新建未找到文件夹\新建未找到文件夹\新建未找到文件夹'
sql_engine = sqlalchemy.create_engine(
  'mysql+pymysql://%s:%s@%s:%s/%s' % (
    'hz_work',
    'Hzinsights2015',
    'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    '3306',
    'yq',
  ), poolclass=sqlalchemy.pool.NullPool
  )

sql="""
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
def ocr_database(originfilename,beizhu):
  sql = """
  UPDATE 23年财报文件
  set ocr= :beizhu
  where fileName = :originfilename
  """
  # 构建参数字典
  params = {
    "originfilename":originfilename,
    "beizhu":beizhu
  }
  with sql_engine.begin() as connection:
    connection.execute(text(sql), params)

def download_PDF(fileUrl,fileName):  #下载pdf
  file_path = os.path.join(folder_path,fileName+".pdf")
  # 检查文件是否已存在，如果存在则不下载
  if os.path.exists(file_path):
    print(f"{fileName}File already exists!")
  else:
    r = requests.get(fileUrl)
    with open(file_path, "wb") as f:
      f.write(r.content)
    print(f"Downloaded: {fileName}.pdf\n")

def update_database(list_keywords,TypeInfo,happenDate,ContentInfo,ai_sum):
  sql = """
  INSERT ignore INTO 金融债舆情监控 (list_keywords,TypeInfo,happenDate,ContentInfo,ai_sum)
  VALUES (:list_keywords, :TypeInfo, :happenDate, :ContentInfo, :ai_sum)
  """
  # 构建参数字典
  params = {
    "list_keywords": list_keywords,
    "TypeInfo": TypeInfo,
    "happenDate":happenDate,
    "ContentInfo": ContentInfo,
    "ai_sum": ai_sum
  }
  with sql_engine.begin() as connection:
    connection.execute(text(sql), params)
def update_database1(trade_code,fileUrl,fileName):
  sql = """
  UPDATE 23年财报文件
  set fileUrl= :fileUrl, fileName= :fileName, ocr='已重下'
  where trade_code = :trade_code
  """
  # 构建参数字典
  params = {
    "trade_code": trade_code,
    "fileUrl": fileUrl,
    "fileName":fileName
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
    'Sec-Fetch-Site':'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
}

# 定义 data
data_login = {
    "UserNameOrEmailAddressOrPhone": "13918339361",
    "internationalPhoneCode": "86",
    "password": "welcome@1"
}
url_login='https://auth.ratingdog.cn/api/TokenAuth/Authenticate'
r = requests.post(url_login, headers=headers_login, json=data_login)
accessToken=r.json()['result']['accessToken']

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


def pro_id(id,headers=headers_yy):
  url=f"https://host.ratingdog.cn/api/services/app/ResearchInfo/GetCiPublicOpinionForView?id={id}"
  data={
    "id":id 
  }
  r = requests.get(url, headers=headers, json=data)
  r = str(r.content, encoding="utf-8")
  r = json.loads(r)
  #提取关键公司
  if r['result'] is None:
     return None
  keywords=r['result']['miniIssuers']
  list_keywords=''
  for i in range(len(keywords)):
      list_keywords+=keywords[i]['issuerName']+','

  #发生日期
  happenDate=r['result']['happenDate']
  #信息类型
  TypeInfo_part1 = r['result'].get('parentPublicOpinionTypeName')
  TypeInfo_part2 = r['result'].get('publicOpinionTypeName')

  TypeInfo = ''
  if TypeInfo_part1 is not None:
      TypeInfo += TypeInfo_part1
  if TypeInfo_part2 is not None:
      TypeInfo += TypeInfo_part2


  #信息内容
  content, image_texts=get_html_text_and_images(html_path=0, html_content=r['result']['publicOpinionContent'])
  commentary=r['result']['commentary']
  if r['result']['commentary']==None:
      commentary=''
  if content==None:
    content=''
  if image_texts==None:
      image_texts=''
  ContentInfo=commentary+content+str(image_texts)
  content0='涉及公司：'+list_keywords+'\n'+'负面信息类型：'+TypeInfo+'\n'+'事件发生日期：'+happenDate+'\n'+'具体负面信息内容：'+ContentInfo
  content0=filter_sensitive_words(content0, automaton)
  ai_sum=summarize_content(content=content0,type='舆情',client=client_hz)

  return list_keywords,TypeInfo,happenDate,ContentInfo,ai_sum


def pro_yyqy(headers=headers_yy):
  SkipCount=0
  is_end=0
  while is_end==0:
    data={
    "AdministrativeDivisionIds": [],
    "ReportDates": [],
    "AdministrativeDivisionLevels": [],
    "DataCategoryTypes": [1001, 1002, 1003],
    "categoryCodes": [
        "GDP",
        "GDPGrowthRate",
        "GDPPerCaptita",
        "InvestmentInFixedAssets",
        "InvestmentInFixedAssetsGrowthRate",
        "PermanentResidents",
        "GDPPerCaptita_model",
        "FiscalSelfsufficiencyRate",
        "TaxPercentage",
        "GeneralBudgetRevenue",
        "GeneralBudgetRevenueGrowthRate",
        "TaxIncome",
        "TaxIncomeGrowthRate",
        "TransferIncome",
        "SubsidyIncomeFromSuperiors",
        "TotalGeneralPublicBudgetRevenue",
        "GeneralBudgetExpenditure",
        "GeneralBudgetExpenditureGrowthRate",
        "GeneralBudgetRevenueGrowthRate_NaturalCaliber",
        "TaxIncome_NaturalCaliber",
        "GovernmentFundIncome",
        "GovernmentFundIncomeGrowthRate",
        "LandSaleRevenue",
        "GovernmentFundExpenditure",
        "RMBBalanceOfDeposits",
        "ForeignCurrencyBalanceOfDeposits",
        "RMBBalanceOfLoad",
        "ForeignCurrencyBalanceOfLoad",
        "TotalFinancialAssets",
        "NonperformingLoanRatio",
        "GeneralDebtLimit",
        "SpecialDebtLimit",
        "GeneralDebtBalance",
        "SpecialDebtBalance",
        "ImplicitDebtResolution",
        "YYRatio",
        "InterestDebt",
        "SurvivalAmount",
        "ThreeYearsCompositeGrowthRate",
        "FiveYearsCompositeGrowthRate",
        "InterestDebtYY",
        "InterestDebtYYBankLoan",
        "InterestDebtYYBonds",
        "InterestDebtYYNonStandard",
        "InterestDebtYYOther",
        "MHPI_YoY",
        "MHPI_MoM",
        "ResidentialHouseTradeArea",
        "ResidentialHouseTradeAmount",
        "ResidentialHouseTradeAvgPrice",
        "SecondhandResidentialHouseTradeArea",
        "UrbanArea",
        "UrbanPopulation",
        "MetropolitanArea",
        "MetropolitanPopulation",
        "BuiltUpArea",
        "InvestInFAIOfCMPF",
        "NewFixedAssetOfCMPF",
        "LengthOfRoad",
        "RoadLengthInBuiltUpArea",
        "RoadSurface",
        "RoadAreaInBuiltUpArea",
        "NumberOfBridge",
        "MajorBridgesAndSuperMajorBridges",
        "ComprehensiveProductionCapacityOfTapWater",
        "LengthOfWaterSupplyPipeline",
        "WaterPopulation",
        "LengthOfDrainagePipe",
        "TotalSewageDischarge",
        "TotalSewageTreatment"
    ],
    "MaxResultCount": 150,
    "SkipCount": SkipCount
    }   

    url = "https://host.ratingdog.cn/api/services/app/AdministrativeDivisionData/GetAdministrativeDivisionDatas"
    requests.DEFAULT_RETRIES = 5
    s = requests.session()    
    r = requests.post(url, headers=headers, json=data)
    r = str(r.content, encoding="utf-8")
    r = json.loads(r)
    table_header=r['result']['tableHeader']
    table_content=r['result']['tableData']['items']
    totalCount=r['result']['tableData']['totalCount']
    column_names = [col for col in table_header.keys()]
    rename_columns ={col:table_header[col]['name'] for col in table_header}

    df = pd.DataFrame(table_content, columns=column_names)
    df.rename(rename_columns,inplace=True,axis='columns')
    column_names=df.columns.tolist()
    with sql_engine.begin() as connection:
      try:
        df0=pd.read_sql("""select * from yq.yyqy limit 1""",connection)
        existing_columns=df0.columns.tolist()
        new_columns = [col for col in column_names if col not in existing_columns]
        print(new_columns)
        # 如果存在新列，则先添加这些列
        if new_columns:
            print(f"Adding new columns: {new_columns}")
            # 构造ALTER TABLE SQL语句来添加新列
            # 注意：下面的SQL语句是针对SQLite的，对于其他数据库，语法可能不同
            alter_table_sql = f"ALTER TABLE yq.yyqy ADD COLUMN {', '.join(f'{col} TEXT' for col in new_columns)}"
            try:
                with sql_engine.begin() as connection:
                    connection.execute(alter_table_sql)
            except Exception as e:
                print(f"Failed to add columns: {e}")
      except:
        print(1)
    
    with sql_engine.begin() as connection:
      df.to_sql(name='yyqy',con=connection,if_exists='append')
    if SkipCount+150>totalCount:
      is_end=1
    else:
      SkipCount+=150
      print(SkipCount)
    
pro_yyqy()