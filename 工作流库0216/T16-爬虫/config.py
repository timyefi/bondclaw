#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件 - 企业预警通地方化债数据爬虫
所有敏感配置使用环境变量，无硬编码密码
"""

import os
import random
import string
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ================================
# 基础路径配置
# ================================
# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ================================
# API配置
# ================================
BASE_URL = os.getenv("QYYJT_BASE_URL", "https://www.qyyjt.cn")
API_URL = os.getenv("QYYJT_API_URL", "https://www.qyyjt.cn/getData.action")
DETAIL_API_URL = os.getenv("QYYJT_DETAIL_API_URL", "https://www.qyyjt.cn/finchinaAPP/newsDetail/getNewsContent.action")

# ================================
# 认证配置（使用环境变量）
# ================================
# Cookie认证 - 从环境变量获取
DEFAULT_COOKIE = os.getenv("QYYJT_COOKIE", "")

# 用户ID - 从环境变量获取
USER_ID = os.getenv("QYYJT_USER_ID", "")

# ================================
# 浏览器模拟配置
# ================================
# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/123.0.0.0 Mobile/15E148 Safari/604.1"
]

# 当前用户代理
USER_AGENT = random.choice(USER_AGENTS)


def generate_request_id(length: int = 16) -> str:
    """生成随机请求ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def update_user_agent() -> str:
    """更新并返回随机User-Agent"""
    global USER_AGENT
    USER_AGENT = random.choice(USER_AGENTS)
    return USER_AGENT


# ================================
# 请求头配置
# ================================
def get_headers() -> dict:
    """获取请求头"""
    return {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "client": "pc-web;pro",
        "content-type": "application/json;charset=UTF-8",
        "dataid": "1447",
        "origin": BASE_URL,
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "system": "new",
        "system1": "Windows NT 10.0; Win64; x64;Edge;135.0.0.0",
        "terminal": "pc-web;pro",
        "user": USER_ID if USER_ID else "D1AF164E61900A87F95701B23461E45A262FDB7EC17EECD4A610F09436B2BB96",
        "ver": "20250401",
        "x-request-id": generate_request_id(),
        "x-request-url": "_global",
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE_URL}/publicOpinons/region",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    }


def get_list_api_headers() -> dict:
    """获取列表API请求头"""
    headers = get_headers()
    if DEFAULT_COOKIE:
        headers["pcuss"] = DEFAULT_COOKIE
        headers["cookie"] = f"HWWAFSESID={generate_request_id(16)}; HWWAFSESTIME={int(__import__('time').time() * 1000)}"
    return headers


def get_detail_api_headers(news_id: str = "") -> dict:
    """获取详情页API请求头"""
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "client": "pc-web;pro",
        "dataid": "1448",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": f"{BASE_URL}/publicOpinonsNewsDetail/{news_id}",
        "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "system": "new",
        "system1": "Linux; Android 6.0; Nexus 5 Build/MRA58N;Edge;135.0.0.0",
        "terminal": "pc-web;pro",
        "user": USER_ID if USER_ID else "D1AF164E61900A87F95701B23461E45A262FDB7EC17EECD4A610F09436B2BB96",
        "ver": "20250401",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36 Edg/135.0.0.0",
        "x-request-id": generate_request_id(),
        "x-request-url": f"%2FpublicOpinonsNewsDetail%2F{news_id}"
    }
    if DEFAULT_COOKIE:
        headers["pcuss"] = DEFAULT_COOKIE
    return headers


# 向后兼容的常量
HEADERS = get_headers()
LIST_API_HEADERS = get_list_api_headers()
DETAIL_API_HEADERS_TEMPLATE = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "cache-control": "no-cache",
    "client": "pc-web;pro",
    "dataid": "1448",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.qyyjt.cn/publicOpinonsNewsDetail/{news_id}",
    "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "system": "new",
    "system1": "Linux; Android 6.0; Nexus 5 Build/MRA58N;Edge;135.0.0.0",
    "terminal": "pc-web;pro",
    "user": "D1AF164E61900A87F95701B23461E45A262FDB7EC17EECD4A610F09436B2BB96",
    "ver": "20250401",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36 Edg/135.0.0.0",
    "x-request-id": "frcd9cAmywwptgcRzeAxV",
    "x-request-url": "%2FpublicOpinonsNewsDetail%2F{news_id}"
}

# ================================
# 爬取参数配置
# ================================
# 默认请求参数
DEFAULT_PARAMS = {
    "topicCode": "areaNews",
    "subType": "localizedBonds",
    "sortColumn": "newsDate",
    "sortOrder": "desc",
    "pageSize": 20,
    "channelId": "1448"
}

# 初始skipParam值
INITIAL_SKIP_PARAM = os.getenv("QYYJT_INITIAL_SKIP_PARAM", "")

# skipParam列表（用于分批爬取）
SKIP_PARAM_LIST = []

# ================================
# 输出文件配置
# ================================
OUTPUT_FILE = DATA_DIR / "地方化债数据.csv"

# ================================
# 爬虫运行配置
# ================================
# 请求延迟范围（秒）
REQUEST_DELAY = (3, 8)

# 基础爬取延迟（秒）
CRAWL_DELAY = int(os.getenv("QYYJT_CRAWL_DELAY", "3"))

# 最大重试次数
MAX_RETRIES = int(os.getenv("QYYJT_MAX_RETRIES", "5"))

# 请求超时时间（秒）
TIMEOUT = int(os.getenv("QYYJT_TIMEOUT", "15"))

# 最大页数
MAX_PAGES = int(os.getenv("QYYJT_MAX_PAGES", "300"))

# 是否增量爬取
INCREMENTAL = os.getenv("QYYJT_INCREMENTAL", "true").lower() == "true"

# 是否重置skipParam
RESET_SKIP_PARAM = False

# ================================
# Playwright配置
# ================================
HEADLESS = os.getenv("QYYJT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_TIMEOUT = 30000  # 毫秒
SCREENSHOT_DIR = DATA_DIR / "screenshots"

# ================================
# 记录文件配置
# ================================
LAST_CRAWL_FILE = DATA_DIR / "last_crawl.txt"
LAST_SKIP_PARAM_FILE = DATA_DIR / "last_skip_param.txt"
LOG_FILE = LOG_DIR / "crawler.log"

# ================================
# 初始化
# ================================
# 初始化时随机选择User-Agent
update_user_agent()
