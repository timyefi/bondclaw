"""
政府网站链接爬取 - 配置模块

配置参数通过环境变量加载，避免硬编码敏感信息。
"""

import os
from typing import Dict, Any


class Config:
    """项目配置类"""

    # ==================== 数据库配置 ====================
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'site_dis')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_CHARSET = os.environ.get('DB_CHARSET', 'utf8mb4')

    # 数据库连接池配置
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', 30))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600))

    # ==================== 爬虫配置 ====================
    # 并发控制
    MAX_CONCURRENT_PAGES = int(os.environ.get('MAX_CONCURRENT_PAGES', 5))
    MAX_CONCURRENT_SITES = int(os.environ.get('MAX_CONCURRENT_SITES', 3))

    # 超时设置
    PAGE_TIMEOUT = int(os.environ.get('PAGE_TIMEOUT', 30000))  # 毫秒
    SITE_TIMEOUT = int(os.environ.get('SITE_TIMEOUT', 300))  # 秒
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))  # 秒

    # 重试配置
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 5))  # 秒
    RETRY_BACKOFF = float(os.environ.get('RETRY_BACKOFF', 2.0))

    # ==================== 请求限制 ====================
    MAX_REQUESTS_PER_SECOND = int(os.environ.get('MAX_REQUESTS_PER_SECOND', 10))
    MAX_REQUESTS_PER_MINUTE = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', 600))
    MAX_REQUESTS_PER_HOUR = int(os.environ.get('MAX_REQUESTS_PER_HOUR', 30000))

    # 单域名限制
    MAX_REQUESTS_PER_DOMAIN_SECOND = int(os.environ.get('MAX_REQUESTS_PER_DOMAIN_SECOND', 2))
    MAX_REQUESTS_PER_DOMAIN_MINUTE = int(os.environ.get('MAX_REQUESTS_PER_DOMAIN_MINUTE', 100))
    COOLDOWN_PERIOD = int(os.environ.get('COOLDOWN_PERIOD', 60))  # 秒

    # ==================== 缓存配置 ====================
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_EXPIRE = int(os.environ.get('CACHE_EXPIRE', 3600))  # 秒
    CACHE_MAX_SIZE = int(os.environ.get('CACHE_MAX_SIZE', 1000))

    # ==================== 代理配置 ====================
    PROXY_ENABLED = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'
    PROXY_URL = os.environ.get('PROXY_URL', '')
    PROXY_SECRET = os.environ.get('PROXY_SECRET', '')
    PROXY_ORDER_NO = os.environ.get('PROXY_ORDER_NO', '')

    # ==================== 浏览器配置 ====================
    BROWSER_HEADLESS = os.environ.get('BROWSER_HEADLESS', 'true').lower() == 'true'
    BROWSER_USER_AGENT = os.environ.get(
        'BROWSER_USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    BROWSER_VIEWPORT_WIDTH = int(os.environ.get('BROWSER_VIEWPORT_WIDTH', 1920))
    BROWSER_VIEWPORT_HEIGHT = int(os.environ.get('BROWSER_VIEWPORT_HEIGHT', 1080))

    # ==================== NLP配置 ====================
    JIEBA_DICT_PATH = os.environ.get('JIEBA_DICT_PATH', '')
    STOPWORDS_PATH = os.environ.get('STOPWORDS_PATH', '')
    KEYWORDS_TOP_K = int(os.environ.get('KEYWORDS_TOP_K', 10))

    # ==================== 机器学习配置 ====================
    ML_CONFIDENCE_THRESHOLD = float(os.environ.get('ML_CONFIDENCE_THRESHOLD', 0.7))
    ML_MIN_TRAINING_SAMPLES = int(os.environ.get('ML_MIN_TRAINING_SAMPLES', 100))
    ML_FEATURE_EXPIRY_DAYS = int(os.environ.get('ML_FEATURE_EXPIRY_DAYS', 30))

    # ==================== 日志配置 ====================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    LOG_FILE = os.environ.get('LOG_FILE', '')

    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """获取数据库配置字典"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'charset': cls.DB_CHARSET,
            'pool_size': cls.DB_POOL_SIZE,
            'max_overflow': cls.DB_MAX_OVERFLOW,
            'pool_timeout': cls.DB_POOL_TIMEOUT,
            'pool_recycle': cls.DB_POOL_RECYCLE,
        }

    @classmethod
    def get_crawler_config(cls) -> Dict[str, Any]:
        """获取爬虫配置字典"""
        return {
            'concurrency': {
                'max_concurrent_pages': cls.MAX_CONCURRENT_PAGES,
                'max_concurrent_sites': cls.MAX_CONCURRENT_SITES,
            },
            'timeout': {
                'page_timeout': cls.PAGE_TIMEOUT,
                'site_timeout': cls.SITE_TIMEOUT,
                'request_timeout': cls.REQUEST_TIMEOUT,
            },
            'retry': {
                'max_retries': cls.MAX_RETRIES,
                'retry_delay': cls.RETRY_DELAY,
                'retry_backoff': cls.RETRY_BACKOFF,
            },
            'rate_limit': {
                'max_per_second': cls.MAX_REQUESTS_PER_SECOND,
                'max_per_minute': cls.MAX_REQUESTS_PER_MINUTE,
                'max_per_hour': cls.MAX_REQUESTS_PER_HOUR,
            },
        }

    @classmethod
    def get_browser_config(cls) -> Dict[str, Any]:
        """获取浏览器配置字典"""
        return {
            'headless': cls.BROWSER_HEADLESS,
            'user_agent': cls.BROWSER_USER_AGENT,
            'viewport': {
                'width': cls.BROWSER_VIEWPORT_WIDTH,
                'height': cls.BROWSER_VIEWPORT_HEIGHT,
            },
        }

    @classmethod
    def get_proxy_config(cls) -> Dict[str, Any]:
        """获取代理配置字典"""
        return {
            'enabled': cls.PROXY_ENABLED,
            'url': cls.PROXY_URL,
            'secret': cls.PROXY_SECRET,
            'order_no': cls.PROXY_ORDER_NO,
        }


# 省份门户网站配置
PROVINCE_SITES = {
    '北京': 'http://www.beijing.gov.cn',
    '上海': 'http://www.sh.gov.cn',
    '天津': 'http://www.tj.gov.cn',
    '重庆': 'http://www.cq.gov.cn',
    '广东': 'http://www.gd.gov.cn',
    '江苏': 'http://www.js.gov.cn',
    '浙江': 'http://www.zj.gov.cn',
    '山东': 'http://www.sd.gov.cn',
    '四川': 'http://www.sc.gov.cn',
    '湖北': 'http://www.hubei.gov.cn',
    '河南': 'http://www.henan.gov.cn',
    '福建': 'http://www.fujian.gov.cn',
    '湖南': 'http://www.hunan.gov.cn',
    '安徽': 'http://www.ah.gov.cn',
    '河北': 'http://www.hebei.gov.cn',
    '陕西': 'http://www.shaanxi.gov.cn',
    '辽宁': 'http://www.ln.gov.cn',
    '江西': 'http://www.jiangxi.gov.cn',
    '云南': 'http://www.yn.gov.cn',
    '广西': 'http://www.gxzf.gov.cn',
}

# 中央部委配置
CENTRAL_GOVERNMENT = [
    {'name': '国务院', 'domain': 'gov.cn'},
    {'name': '国家发改委', 'domain': 'ndrc.gov.cn'},
    {'name': '工信部', 'domain': 'miit.gov.cn'},
    {'name': '商务部', 'domain': 'mofcom.gov.cn'},
    {'name': '财政部', 'domain': 'mof.gov.cn'},
    {'name': '人民银行', 'domain': 'pbc.gov.cn'},
    {'name': '海关总署', 'domain': 'customs.gov.cn'},
    {'name': '税务总局', 'domain': 'chinatax.gov.cn'},
    {'name': '市场监管总局', 'domain': 'samr.gov.cn'},
    {'name': '统计局', 'domain': 'stats.gov.cn'},
]

# 页面类型特征配置
PAGE_TYPE_FEATURES = {
    'gov_info': {
        'title_keywords': ['关于', '通知', '意见', '办法', '规定', '条例', '实施'],
        'content_keywords': ['各省', '各部门', '文号', '特此', '执行'],
        'url_patterns': ['/zwgk/', '/xxgk/', '/govinfo/', '/zfxxgk/'],
    },
    'notice': {
        'title_keywords': ['公告', '通告', '通知', '公示', '声明'],
        'content_keywords': ['现将', '特此公告', '公示期', '联系电话'],
        'url_patterns': ['/notice/', '/gonggao/', '/tzgg/'],
    },
    'news': {
        'title_keywords': ['新闻', '动态', '资讯', '快讯', '要闻'],
        'content_keywords': ['记者', '报道', '采访', '表示'],
        'url_patterns': ['/news/', '/xinwen/', '/dongtai/'],
    },
    'guide': {
        'title_keywords': ['指南', '指引', '流程', '手册', '须知'],
        'content_keywords': ['步骤', '材料', '办理', '申请'],
        'url_patterns': ['/guide/', '/service/', '/bszn/'],
    },
}


if __name__ == '__main__':
    # 打印配置信息
    print("=== 政府网站链接爬取配置 ===")
    print(f"数据库: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
    print(f"爬虫并发: {Config.MAX_CONCURRENT_PAGES} 页, {Config.MAX_CONCURRENT_SITES} 站")
    print(f"请求限制: {Config.MAX_REQUESTS_PER_SECOND}/秒, {Config.MAX_REQUESTS_PER_MINUTE}/分钟")
    print(f"代理启用: {Config.PROXY_ENABLED}")
    print(f"缓存启用: {Config.CACHE_ENABLED}")
    print(f"已配置省份: {len(PROVINCE_SITES)} 个")
    print(f"已配置部委: {len(CENTRAL_GOVERNMENT)} 个")
