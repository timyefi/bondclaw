#用益信托网
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
import requests
from bs4 import BeautifulSoup
import re

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

num=1
url =f"https://www.usetrust.com/Action/AjaxAction.ashx"
post_dict = {
"pageIndex": f'{num}',
"mode": 'ListArticle',
"pageSize": "10",
"parentId": "1050240046"
}

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-Length': '60',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Cookie': 'SeseeionUid=41f737d9-3582-4b0e-b4f6-8c14c39f11b3',
    'Host': 'www.usetrust.com',
    'Origin': 'https://www.usetrust.com',
    'Referer': 'https://www.usetrust.com/studio/',
    'Sec-Ch-Ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
    'X-Requested-With': 'XMLHttpRequest'
}

response = requests.post(url, headers=headers, data=post_dict,timeout=20)
df= response.text
corrected_text =df.replace(f"pageIndex:{num}", f'"pageIndex":"{num}"')
df = json.loads(corrected_text)
df=pd.DataFrame(df['result'])

def keep_chinese(text):
        pattern = re.compile(r'责任编辑(.*?)打印文章', re.S)
        match = pattern.search(text)
        if match:
            content_between = match.group(1)
            # 使用正则表达式匹配中文字符、数字和句号
            chinese_pattern = re.compile(r"[\u4e00-\u9fa50-9.，。%-、]+")
            # 使用正则表达式的findall方法找到所有匹配的中文字符、数字和句号
            filtered_chars = chinese_pattern.findall(content_between)
            # 将匹配到的中文字符、数字和句号列表拼接成一个新的字符串
            result = ''.join(filtered_chars)
            return result
        else:
            return "未找到符合条件的内容"
        
for index, row in df.iterrows():
    # 构建插入 SQL 语句
    sql = """
    INSERT ignore INTO 用益信托 (ROWID,C_ID, CAT_ID, C_TITLE, C_SUBTITLE,C_SUMMARY,C_SOURCE,C_IMAGEURL,C_ADDTIME) 
    VALUES (:ROWID, :C_ID, :CAT_ID, :C_TITLE, :C_SUBTITLE, :C_SUMMARY,:C_SOURCE,:C_IMAGEURL,:C_ADDTIME)
    """
    # 构建参数字典
    params = {
        "ROWID": row['ROWID'],
        "C_ID": row['C_ID'],
        "CAT_ID": row['CAT_ID'],
        "C_TITLE": row['C_TITLE'],
        "C_SUBTITLE": row['C_SUBTITLE'],
        "C_SUMMARY": row['C_SUMMARY'],
        "C_SOURCE": row['C_SOURCE'],
        "C_IMAGEURL": row['C_IMAGEURL'],
        "C_ADDTIME": row['C_ADDTIME']
    }
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql),params)

    url = f"https://www.usetrust.com/Studio/Details.aspx?i={row['C_ID']}"
    # 发送HTTP GET请求
    response = requests.get(url)
      
    # 确查状态码检查，确保请求成功
    if response.status_code == 200:
        # 使用BeautifulSoup解析网页内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取所有文字内容
        all_text = soup.get_text()
        chinese_only = keep_chinese(all_text)
        your_C_ID=row['C_ID']
        sql = """UPDATE 用益信托 SET content = :content WHERE C_ID = :cid"""  
        params = {"content": chinese_only, "cid": your_C_ID} 
        with sql_engine.begin() as _cursor:
            	_cursor.execute(text(sql),params)
        print(index)
    else:
        print(f"请求失败，状态码：{response.status_code}")
        
create_procedure_sql1 = """
DROP PROCEDURE IF EXISTS FindMatchingRecords"""

create_procedure_sql2 = """
CREATE PROCEDURE FindMatchingRecords()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE content_text TEXT;
    DECLARE addtime DATETIME;
    DECLARE cursor_content CURSOR FOR SELECT C_ADDTIME, content FROM 用益信托;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    DROP TEMPORARY TABLE IF EXISTS temp_用益信托;
    CREATE TEMPORARY TABLE temp_用益信托 (
        C_ADDTIME DATETIME,
        成立规模 DECIMAL(10,2),
        紧邻前50字符 VARCHAR(50)
    );

    OPEN cursor_content;

    read_loop: LOOP
        FETCH cursor_content INTO addtime, content_text;
        IF done THEN
            LEAVE read_loop;
        END IF;

        SET @pos = 1;
        WHILE @pos > 0 DO
            SET @pos = LOCATE('成立规模', content_text, @pos);
            IF @pos > 0 THEN
                SET @start_pos = GREATEST(1, @pos - 50);
                SET @sub_content = SUBSTRING(content_text, @start_pos, 50);
                IF @sub_content LIKE '%标品信托%' THEN
                    -- 提取成立规模后的数值
                    SET @scale_text = SUBSTRING(content_text, @pos + CHAR_LENGTH('成立规模'), 10);
                    SET @scale_value = CAST(SUBSTRING_INDEX(@scale_text, '亿', 1) AS DECIMAL(10,2));
                    -- 插入到临时表中
                    INSERT INTO temp_用益信托 (C_ADDTIME, 成立规模, 紧邻前50字符)
                    VALUES (addtime, @scale_value, @sub_content);
                END IF;
                SET @pos = @pos + 1;
            END IF;
        END WHILE;
    END LOOP;

    CLOSE cursor_content;
END;
"""

call_procedure_sql3 = """
CALL FindMatchingRecords()"""

call_procedure_sql4 = """
UPDATE 用益信托 A
JOIN (
    SELECT C_ADDTIME as dt, MAX(成立规模) as 成立规模 FROM temp_用益信托 WHERE 成立规模 > 0
    GROUP BY C_ADDTIME
) B
ON A.C_ADDTIME = B.dt
SET A.标品信托成立规模 = B.成立规模;
"""
with sql_engine.begin() as _cursor:
    _cursor.execute(text(create_procedure_sql1))
    _cursor.execute(text(create_procedure_sql2))
    _cursor.execute(text(call_procedure_sql3))
    _cursor.execute(text(call_procedure_sql4))