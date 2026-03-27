#使用通义千问总结
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
import os
import openai
from pathlib import Path
from sqlalchemy import text
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import shutil
import tempfile
from pathlib import Path
import os
from tika import parser
import ahocorasick
import re

def read_sensitive_words(filename):
    """读取敏感词"""
    # sql_engine1 = sqlalchemy.create_engine(
    # 'mysql+pymysql://%s:%s@%s:%s/%s' % (
    #     'root',
    #     's5bx55dh',
    #     'bja.sealos.run',
    #     '44525',
    #     'timinfo',
    # ), poolclass=sqlalchemy.pool.NullPool
    # )
    # sql_template = """
    #     select keyword from SensitiveWords
    #     """
    # with sql_engine1.begin() as connection:
    #     df=pd.read_sql(sql_template,connection)
    #     sensitive_words = df['keyword'].tolist()
    with open(filename, 'r', encoding='utf-8') as file:
        # 读取每一行，去掉换行符
        sensitive_words = [line.strip() for line in file]
    return sensitive_words

def build_automaton(sensitive_words):
    """构建Aho-Corasick自动机"""
    A = ahocorasick.Automaton()
    for idx, word in enumerate(sensitive_words):
        A.add_word(word, (idx, word))
    A.make_automaton()
    return A

def filter_sensitive_words(text, automaton):
    
    """根据Aho-Corasick自动机过滤文本中的敏感词"""
    matches = []
    for end_index, (insert_order, original_value) in automaton.iter(text):
        start_index = end_index - len(original_value) + 1
        matches.append((start_index, end_index + 1))

    filtered_text_parts = []
    last_end = 0
    for start, end in matches:
        filtered_text_parts.append(text[last_end:start])
        last_end = end
    filtered_text_parts.append(text[last_end:])

    return ''.join(filtered_text_parts)


# 敏感词库文件路径
sensi_filename = r"C:\daily\sensitive_word_dict.txt"
# 读取敏感词库
sensitive_words_list = read_sensitive_words(sensi_filename)
automaton = build_automaton(sensitive_words_list)

# 邮件配置
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
EMAIL_USER = '917952467@qq.com'
EMAIL_PASSWORD = 'ineaylzljuqdbgai'
RECIPIENT_EMAIL = 'tim.ye@foxmail.com'

def pro_db(type='df',sql='',table='',params1={},params2={}):
    sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
    )
    with sql_engine.begin() as connection:
        if type=='df':
            df=pd.read_sql(sql,connection)
            return df
        elif type=='exe':
            connection.execute(text(sql))
        elif type=='insert':
            sql="""
            INSERT ignore INTO """
            +table
            +"("+', '.join(params1.keys())+")"
            +" VALUES (:"+', :'.join(params1.keys())+")"
            connection.execute(text(sql), params1)
        elif type=='update':
            set_clause = ', '.join([f"{key} = :{key}" for key,value in params1.items()])
            # 使用参数化查询构建 WHERE 子句
            where_clause = ' AND '.join([f"{key} = :{key}" for key,value in params2.items()])
            sql = f"""
                UPDATE {table}
                SET {set_clause}
                WHERE {where_clause}
                """
            params=params1 | params2
            connection.execute(text(sql), params)


def send_email(subject, html_content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = RECIPIENT_EMAIL
    
    part = MIMEText(html_content, 'html')
    msg.attach(part)
    
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.connect(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

# 阿里云 Qwen-Long API 配置
api_key = api_key="sk-f4f4de7b9a3f4dbcbab21012757d4fca"
base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
client = openai.OpenAI(api_key=api_key, base_url=base_url)

api_key_hz ="sk-3236ebaa10bc477987e3264e8a8b7d0f"

client_hz = openai.OpenAI(api_key=api_key_hz, base_url=base_url)


def upload_file_to_qwen(file_path,client=client):
    try:
        file_object = client.files.create(file=Path(file_path), purpose="file-extract")
    except Exception as e:
        print(e)
    return file_object.id

def prompt_db(type):
    if type==1:
        prompt_text='''### 内容总结要求

                    在全面阅读文章的基础上，提供一个高度凝练且结构严谨的内容总结。总结时需确保以下几点：

                    1. **核心内容提炼**：精准概括文章的中心思想，突出论述重点与发现。
                    2. **逻辑清晰**：维持内容的条理性和连贯性，使读者能顺畅理解文章脉络。
                    3. **信息准确无误**：确保所有纳入总结的信息严格忠实于原文，无任何误差。
                    4. **无关内容排除**：剔除所有免责声明、广告信息、团队或个人介绍、联系方式，以及文章末尾的法律合规性声明和可能的利益冲突提示。

                    请以中文进行回答，专注于文章主体内容，确保总结既精炼又全面，直接关联文章主旨，为读者提供一个去除了所有冗余信息的精华版内容概览。

                    ### 总结结构

                    1. **文章标题**：提取文章的标题或主题。
                    2. **引言/背景**：描述文章的背景和目的，阐明文章的重要性和相关背景信息。
                    3. **主要内容**：
                    - **方法/过程（如适用）**：描述研究方法、数据来源或事件过程。
                    - **结果/发现**：列出主要的研究结果、关键发现或报道的核心内容。
                    4. **章节概述（如适用）**：
                    - **章节标题**：
                    - **章节内容提要**：包括背景、主要内容、讨论/分析和小结。
                    5. **讨论/分析**：分析文章的主要发现或内容，讨论其对相关领域或行业的影响。
                    6. **结论**：总结文章的主要发现及其影响，提出进一步研究或行动的建议（如有）。
                    7. **推荐/下一步（如适用）**：提出具体的建议或下一步行动。
                    '''
    elif type==2:
        prompt_text='''
                ###作为专业的金融领域分析师，你的任务是分析并总结每个群聊的主要讨论内容。请确保总结遵循以下结构和准则，以保证内容的清晰性、准确性和逻辑连贯性：

                **任务指南：**

                对于每个独立话题，请分别总结并遵循以下结构：

                1. **主题提取：**
                - **标题：** 提取该话题的主要标题或主题。

                2. **引言/背景：**
                - 描述该话题的背景和目的，阐明其重要性和相关背景信息。

                3. **主要内容：**
                - **方法/过程（如适用）：** 描述讨论的方法、数据来源或事件过程。
                - **结果/发现：** 列出主要的讨论结果、关键发现或报道的核心内容。

                4. **章节概述（如适用）：**
                - **章节标题：** 提取每个子话题或章节的标题。
                - **章节内容提要：** 提炼每个章节的关键信息，包括背景、主要内容、讨论/分析和小结。

                5. **讨论/分析：**
                - 分析讨论的主要发现或内容，讨论其对相关领域或行业的影响。

                6. **结论：**
                - 总结该话题的主要发现和其影响，提出进一步研究或行动的建议（如有）。

                7. **推荐/下一步（如适用）：**
                - 提出具体的建议或下一步行动。

                **通用准则：**

                1. **内容准确：**
                - 确保所有信息真实反映群聊内的讨论，避免添加个人臆测或偏离实际讨论内容。

                2. **逻辑通顺：**
                - 保持论述的连贯性，使读者能顺畅理解各部分内容之间的联系和群聊讨论的演变。

                3. **去除无关信息：**
                - 排除免责声明、广告、团队介绍、联系信息等无关内容。
                - 不包括在文章末尾的Analyst Certification、Research excerpts、Important Disclosures、Other Disclosures、免责声明、法律、合规相关内容。

                4. **审查与调整：**
                - 最后，审查总结报告，确认信息的准确性、逻辑性和完整性。
                - 调整表述以达到最佳的可读性。

                请依此指南，总结每个独立话题的群聊内容。
                '''
    elif type=='舆情':
        prompt_text='''作为债券信用风险分析专家，针对特定企业负面舆情进行深入分析： 
            ### 分析任务： - 针对目标企业的负面舆情进行全面剖析，特别聚焦于其对债券偿付能力的潜在影响程度及具体方面;不要出现涉及任何有关YY、瑞霆狗的词语。
            ### 格式要求：务必严格遵守以下格式，不要输出除了结论、逻辑、关注三个部分之外的任何其他信息，不要输出markdown格式，三个部分的子标题用1、2、3、等等来编号。
            结论： 限50字内，概括评估舆情对该企业信用及偿付能力的直接影响，明确指出风险等级与紧迫性。 
            逻辑： 限200字内，阐述分析路径，明确指出结论得出的逻辑链条与支撑信息。 
            关注： 限50字内，基于当前分析，指出应密切监视的几个核心指标或事件，并标识出信息缺口，指导进一步数据收集或调研方向，以期全面把控风险态势。'''
    
    return prompt_text

def summarize_content(file_id=0,type=1,content=0,client=client):
    prompt_text=prompt_db(type)

    if file_id !=0:
        content=f'fileid://{file_id}'
    try:
        completion = client.chat.completions.create(
            model="qwen-long",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'system', 'content': content},
                {'role': 'user', 'content':prompt_text}
            ],
            stream=False
        )
        content = completion.choices[0].message.dict()['content']
    except Exception as e:
        print(e)
    return content

# def pro_ai(filename_ocr,type,client):
#     # 上传文件到阿里云
#     list=client.files.list()
#     list1=list.data
#     file_exist=0
#     for item in list1:
#         if item.filename == filename_ocr:
#             file_exist = 1
#             file_id = item.id
#     if file_exist==1:
#         if filename_ocr in list_filename:
#             continue
#         else:
#             summary = summarize_content(file_id,type,client)
#     else:
#         file_id = upload_file_to_qwen(temp_file_path,client)
#         if filename_ocr in list_filename:
#             continue
#         else:
#             summary = summarize_content(file_id,type,client)
#     return summary

def upload_metadata_to_mysql(file_id, summary,filename):
    sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
    )
    # _cursor = sql_engine.connect()
    sql_engine1 = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'root',
        's5bx55dh',
        'bja.sealos.run',
        '44525',
        'timinfo',
    ), poolclass=sqlalchemy.pool.NullPool
    )
    # _cursor1 = sql_engine1.connect()

    date = datetime.now()
    # _cursor.execute(
    #     "INSERT INTO documents (dt, fileid, summary) VALUES (%s, %s, %s)",
    #     (date,file_id, summary)
    # )

    sql = """
    INSERT ignore INTO 信息库 (dt, fileid, summary,filename)
    VALUES (:dt, :fileid, :summary,:filename)
    """
    # 构建参数字典
    params = {
        "dt": date,
        "fileid": file_id,
        "summary":summary,
        "filename":filename
    }
    with sql_engine1.begin() as connection:
        connection.execute(text(sql), params)
    summary = summary.replace('\n', '<br>')
    summary=f'fileid://{file_id}\n\n'+summary
    send_email(filename,summary)

def pase_file(file_path):
    # 解析PDF文件
    # parsed = parser.from_file(file_path)
    text = main_ocr(file_path)

    # 提取文本
    # text = parsed['content']
    return text

def process_files(folder_path,folder_path2,list_filename):
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if  '微信消息' in filename:
            type=2
        else:
            type=1
        try:
            text=pase_file(file_path)
            # 过滤文本中的敏感词
            # text = filter_sensitive_words(text, sensitive_words_list)
            text = filter_sensitive_words(text, automaton)
            print(text)
            base_name, extension = os.path.splitext(filename)
            filename_ocr=base_name+".txt"
            temp_file_path = os.path.join('/tmp', filename_ocr)
            # temp_file_path = tempfile.mkstemp(suffix=".txt", prefix=base_name + "_")[1]
            with open(temp_file_path, "w+", encoding='utf-8') as temp_file:
                temp_file.write(text)
            # 上传文件到阿里云
            list=client.files.list()
            list1=list.data
            file_exist=0
            for item in list1:
                if item.filename == filename_ocr:
                    file_exist = 1
                    file_id = item.id
            if file_exist==1:
                if filename_ocr in list_filename:
                    continue
                else:
                    summary = summarize_content(file_id,type)
            else:
                file_id = upload_file_to_qwen(temp_file_path)
                if filename_ocr in list_filename:
                    continue
                else:
                    summary = summarize_content(file_id,type)
            
            # 将文件ID和总结内容上传到MySQL
            upload_metadata_to_mysql(file_id, summary,filename_ocr)
            
            # 删除本地文件
            file_path2 = os.path.join(folder_path2, filename)
            if not os.path.exists(file_path2):
                shutil.copy(file_path, file_path2)
            folder_path3 = r"C:\Users\Administrator\iCloudDrive\lib"
            file_path3 = os.path.join(folder_path3, filename)
            if not os.path.exists(file_path3):
                shutil.copy(file_path, file_path3)
            os.remove(file_path)
            os.remove(temp_file_path)

        except Exception as e:
            print(e)
            folder_path4 = r"C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\quick1"
            file_path4 = os.path.join(folder_path4, filename)
            if not os.path.exists(file_path4):
                shutil.copy(file_path, file_path4)
            os.remove(file_path)
            os.remove(temp_file_path)

import os
import io
import concurrent.futures
from tika import parser
from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
from PIL import Image
from docx import Document
from ebooklib import epub
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import base64
from io import BytesIO
import re
from IPython.display import Image as IPImage
from paddleocr import PaddleOCR, draw_ocr
import fitz
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log')


os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# 初始化OCR，开启文字方向检测、使用更广泛的多语言模型
lang_list=['ch', 'en','fr','german','korean', 'japan', 'chinese_cht', 'ta', 'te', 'ka', 'latin', 'arabic', 'cyrillic', 'devanagari']
method='paddle'
try:
    ocr = PaddleOCR(use_angle_clsf=True, lang='ch', show_log=False, use_gpu=True,
                 rec_model_dir='./pretrain_models/ch_ppocr_server_v2.0_rec_pre/best_accuracy',
                 det_model_dir='./pretrain_models/ch_PP-OCRv3_det_infer/', 
                 cls_model_dir='./pretrain_models/ch_ppocr_mobile_v2.0_cls_infer/')
except:
    method='tesseract'
    logging.info(f"paddle调用失败，改用tesseract")

# 绘制识别结果和边界框
    
def recognize_and_draw(img):
    results = ocr.ocr(img, cls=True)
    result=results[0]
    text=''
    for idx in range(len(result)):
        try:
            res = result[idx]
            text+=res[1][0]+'\n'
        except Exception as e:
            text+=''
            logging.info(e)
    # 绘制识别结果，作为展示用，实际应用中可能会有定制化的展现方式
    # draw_img = draw_ocr(img_corrected, result, show_log=False)
    # cv2.imwrite("result.jpg", draw_img)
    return text


def preprocess_and_ocr_image(img, method='paddle'):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        # dist = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
        # dist = cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
        # dist = (dist * 255).astype("uint8")

        _,dist = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
        opening = cv2.morphologyEx(dist, cv2.MORPH_OPEN, kernel)
        if method =='paddle':
            text = recognize_and_draw(opening)
        elif method =='tesseract':
            text = pytesseract.image_to_string(opening,custom_config = r'--oem 3 --psm 6 -l chi_sim+eng')
    except Exception as e:
        text=''
        logging.info(f"paddle调用失败，改用tesseract")
    return text


def fetch_file_content(file_url_or_path):
    if file_url_or_path.startswith('http'):
        html_content=get_dynamic_page_content(file_url_or_path)
        file_path = os.path.join('/tmp', 'temp.html')
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html_content)
        return file_path,1
    else:
        file_path = file_url_or_path
        return file_path,2


def extract_images(pdf_path):
    images_list = []
    doc = fitz.open(pdf_path)
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images_list.append(base_image)
    return images_list



def get_pdf_text_and_images(pdf_path):
    try:
        images = extract_images(pdf_path)
        parsed = parser.from_file(pdf_path)
        text_extracted = parsed.get('content', '')

        image_texts = []

        for idx, image in enumerate(images, start=1):
            try:
                image_data = image["image"]
                # binary_data = base64.b64decode(image_data)
                
                # 使用PIL加载图像，指定图像格式
                img = Image.open(io.BytesIO(image_data))
                
                # 转换为numpy数组
                img_array = np.array(img)

                ocr_result = preprocess_and_ocr_image(img_array)
                image_texts.append((f"---IMAGE {idx}---", ocr_result))
            except Exception as e:
                logging.info(e)
    except Exception as e:
        text_extracted = ''
        image_texts = []
        logging.info(e)
    return text_extracted, image_texts

def process_image_for_docx(document):
    image_counter = 1
    image_texts = []
    try:
        for rel in document.part.rels:
            try:
                if "image" in document.part.rels[rel].target_ref:
                    image_data = document.part.rels[rel].target_part.blob
                    image = Image.open(io.BytesIO(image_data))
                    img_array = np.array(image)
                    ocr_result = preprocess_and_ocr_image(img_array)
                    image_texts.append((f"---IMAGE {image_counter}---", ocr_result))
                    image_counter += 1
            except Exception as e:
                image_counter += 1
                logging.info(e)
    except Exception as e:
        image_texts = []
        logging.info(e)
    return image_texts

def get_docx_text_and_images(docx_path):
    try:
        document = Document(docx_path)
        text_extracted = "\n".join([para.text for para in document.paragraphs])
        image_texts = process_image_for_docx(document)
    except Exception as e:
        text_extracted = ''
        image_texts = []
        logging.info(e)
    return text_extracted, image_texts

def get_dynamic_page_content(url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 为了无界面运行 Chrome
        chrome_options.add_argument("--disable-gpu") # 可选，针对某些系统的性能优化
        chrome_options.add_argument("--no-sandbox")  # 为了容器化运行方便
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        driver.get(url)

        # 让页面充分加载
        import time
        time.sleep(5)

        html_content = driver.page_source
        driver.quit()
    except Exception as e:
        html_content = ''
        logging.info(e) 
    return html_content

def download_image(url):
    try:
        # 获取图像数据，注意使用stream=True来处理大文件
        response = requests.get(url, stream=True)
        
        # 确保请求成功
        response.raise_for_status()  # 这会抛出一个HTTPError如果状态码不是200
        
        # 使用BytesIO处理响应内容
        image_stream = BytesIO(response.content)
        
        # 尝试打开并保存图片
        image = Image.open(image_stream)
        # print("图片保存成功。")
    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
        image=''
        logging.info(e)
    except IOError as e:
        print(f"图片处理错误: {e}")
        image=''
        logging.info(e)
    return image

def handle_base64_image(base64_string):
    try:
        """处理Base64编码的图片并返回Image对象"""
        image_data = re.sub('^data:image/.+;base64,', '', base64_string)
        byte_data = base64.b64decode(image_data)
        image = Image.open(BytesIO(byte_data))
    except Exception as e:
        image=''
        logging.info(e)
    return image

def process_picture_tag(picture_tag):
    try:
        """处理<picture>标签，选择最佳图片源"""
        # 此处简化处理，实际应用中可能需要更复杂的逻辑来选择最佳资源
        img_tag = picture_tag.find('img')
        img_src=img_tag['src']
    except Exception as e:
        img_src=''
        logging.info(e)
    return img_src

def get_html_text_and_images(html_path=0, html_content=0):
    try:
        content = ''
        image_texts = []
        image_counter = 1
        try:
            if html_path != 0:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            content = soup.get_text()
            images = soup.find_all(['img', 'picture'])
        except Exception as e:
            content=''
            images=[]
            logging.info(e)

        for img in images:
            try:
                img_src = None
                if img.name == 'img':
                    # 优先处理src，其次data-src
                    img_src = img.get('data-src') or img.get('src')
                        
                    if (not img_src) and 'base64,' in img.get('src', ''):
                        # 理Base64编码的图片
                        img_src = img['src']
                elif img.name == 'picture':
                    # 处理<picture>标签
                    img_src = process_picture_tag(img)
                
                if not img_src:
                    logging.info("No valid image source found, skipping...")
                    continue
                
                if img_src.startswith('data:'):
                    # Base64 编码的图片处理
                    image = handle_base64_image(img_src)
                elif img_src.startswith(('http://', 'https://')):
                    # 网络图片下载
                    image = download_image(img_src)
                else:
                    # 假设是相对路径或本地文件
                    with open(img_src, 'rb') as img_file:
                        image = Image.open(img_file)
                
                ocr_result = preprocess_and_ocr_image(np.array(image),'paddle')  # 确保此函数已定义
                image_texts.append((f"---IMAGE {image_counter}---", ocr_result))
                image_counter += 1

            except Exception as e:
                image_counter += 1
                logging.info(e)
    except Exception as e:
        content = ''
        image_texts = []
        logging.info(e)
    return content, image_texts

def process_epub_layout(epub_path):
    try:
        book = epub.read_epub(epub_path)
        text_extracted = ''
        image_texts = []
        image_counter = 1

        for item in book.get_items():
            try:
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    text_extracted += BeautifulSoup(item.content, 'html.parser').get_text()
                elif item.get_type() == ebooklib.ITEM_IMAGE:
                    image = Image.open(io.BytesIO(item.content))
                    img_array = np.array(image)
                    ocr_result = preprocess_and_ocr_image(img_array)
                    image_texts.append((f"---IMAGE {image_counter}---", ocr_result))
                    image_counter += 1
            except Exception as e:
                image_counter += 1
                logging.info(e)
    except Exception as e:
        text_extracted = ''
        image_texts = []
        logging.info(e)
    return text_extracted, image_texts

def ocr_and_reconstruct_content(input_path):
    try:
        if input_path.endswith(".pdf"):
            text, images = get_pdf_text_and_images(input_path)
        elif input_path.endswith(".docx") or input_path.endswith(".doc"):
            text, images = get_docx_text_and_images(input_path)
        elif input_path.endswith(".epub"):
            text, images = process_epub_layout(input_path)
        elif input_path.endswith(".html"):
            text, images = get_html_text_and_images(input_path)
        elif input_path.endswith(".txt"):
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            images = []
        elif input_path.endswith(".png") or input_path.endswith(".jpg") or input_path.endswith(".jpeg") or input_path.endswith(".bmp") or input_path.endswith(".tif") or input_path.endswith(".tiff"):
            image = Image.open(input_path)  
            text = preprocess_and_ocr_image(np.array(image),'paddle')
            images = []
        else:
            raise ValueError("Unsupported file format.")
        final_text = text+'\n下面是文档中所有图表内容：\n'
        for idx,ocr_text in enumerate(images):
            ocr_text=str(ocr_text)
            final_text = final_text + f'\n{ocr_text}\n'
    except Exception as e:
        final_text = ''
        logging.info(e)

    return final_text

def main_ocr(file_url_or_path):
    try:
        temp_file_path,is_urlpath = fetch_file_content(file_url_or_path)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(ocr_and_reconstruct_content, temp_file_path)
            result = future.result()  # 会阻塞主进程直至完成

        if is_urlpath==1 and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    except Exception as e:
        result = ''
        logging.info(e)

    return result


def main():
    folder_path = r"C:\Users\Administrator\iCloudDrive\quickinfo"
    folder_path1 = r"C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\quick"
    folder_path2 = r"C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\lib"
    sql_engine1 = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'root',
        's5bx55dh',
        'bja.sealos.run',
        '44525',
        'timinfo',
    ), poolclass=sqlalchemy.pool.NullPool
    )
    # _cursor1 = sql_engine1.connect()
    # sql = """
    # select filename from 信息库
    # """
    # with sql_engine1.begin() as connection:
    #     df=pd.read_sql(sql,connection)
    # # sql_engine1.commit()
    # # sql_engine1.close()
    # list_filename=df['filename'].tolist()
    
    # process_files(folder_path,folder_path2,list_filename)
    # process_files(folder_path1,folder_path2,list_filename)

if __name__ == '__main__':
    main()
