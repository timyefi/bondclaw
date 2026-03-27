import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import sqlalchemy
import pandas as pd

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

# 指定网页 URL
url = "https://news.stockstar.com/author_list/张菁.shtml"

# 发送 HTTP GET 请求获取网页内容
response = requests.get(url)

# 检查请求是否成功
if response.status_code == 200:
    response.encoding = response.apparent_encoding
    html_content = response.text

    # 解析 HTML 内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找标题为 "张菁的文章" 的 div
    zhangjing_div = soup.find('div', class_='name', title='张菁的文章')

    # 查找 "张菁的文章" 下面的第一个 <a> 标签
    if zhangjing_div:
        first_a_tag = zhangjing_div.find_next('a')
        if first_a_tag and 'href' in first_a_tag.attrs:
            link = first_a_tag['href']
            response=requests.get(link)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                print(soup.prettify())
        else:
            print("未找到链接")
    else:
        print("未找到'张菁的文章'的 div")
else:
    print("无法获取网页内容，状态码:", response.status_code)

response=requests.get(link)
if response.status_code == 200:
    response.encoding = response.apparent_encoding
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')


def extract_keywords_and_number(text):
    # 查找包含所有关键词且从“截止”开头的子串
    pattern = re.compile(r'(截止.*?理财.*?规模.*?万亿)')
    match = pattern.search(text)
    
    if match:
        # 获取匹配的子串
        matched_text = match.group(1)
        
        # 确保子串长度不超过100个字符，从“截止”开始
        start_pos = match.start()
        end_pos = start_pos + 50
        extracted_text = text[start_pos:end_pos]
        
        print("提取的文本:", extracted_text)
        
        # 提取第一个“规模”和“万亿”之间的数字
        number_pattern = re.compile(r'规模(.*?)万亿')
        number_match = number_pattern.search(extracted_text)
        
        if number_match:
            # 提取第一个数字
            potential_numbers = re.findall(r'[\d,\.]+', number_match.group(1))
            if potential_numbers:
                number = potential_numbers[0]
                print("提取的数字:", number)
            else:
                print("未找到 '规模' 和 '万亿' 之间的数字")
                number = None
        else:
            print("未找到 '规模' 和 '万亿' 之间的内容")
            number = None
        
        # 提取日期并格式化
        date_pattern = re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日)')
        date_match = date_pattern.search(extracted_text)
        
        if date_match:
            date_str = date_match.group(1)
            try:
                # 将日期字符串转换为datetime对象
                date_obj = datetime.strptime(date_str, "%Y年%m月%d日")
                # 格式化为“YYYY-MM-DD”
                formatted_date = date_obj.strftime("%Y-%m-%d")
                print("提取的日期:", formatted_date)
            except ValueError:
                print("日期格式错误")
                formatted_date = None
        else:
            print("未找到日期")
            formatted_date = None
        return number, formatted_date
    else:
        print("未找到包含所有关键词且从'截止'开头的子串")
        return None, None


# 示例字符串
text =soup.prettify()

# 调用函数进行提取
num0,date0=extract_keywords_and_number(text)

if num0 and date0:
    data = {'dt': [date0], '理财规模': [num0]}
    df = pd.DataFrame(data)
    try:
        df.to_sql('理财规模', con=_cursor, if_exists='append', index=False)
    except  Exception as e:
        print(e)