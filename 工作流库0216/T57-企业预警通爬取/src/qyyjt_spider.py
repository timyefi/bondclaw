# -*- coding: utf-8 -*-
"""
企业预警通API爬虫模块
"""
import requests
import json
import time
import random
import logging
import hashlib
from urllib import parse
from typing import Dict, Optional, Any
from datetime import datetime
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QYYJT_BASE_URL, QYYJT_USERNAME, QYYJT_PASSWORD, SPIDER_CONFIG


class QYYJTSpider:
    """企业预警通API爬虫类"""

    def __init__(self, username: str = None, password: str = None):
        self.base_url = QYYJT_BASE_URL
        self.username = username or QYYJT_USERNAME
        self.password = password or QYYJT_PASSWORD
        self.session = self._init_session()
        self.headers = self._get_default_headers()
        self.token = None
        self.user_id = None
        self._setup_logging()

    def _setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spider.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _init_session(self) -> requests.Session:
        """初始化会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=SPIDER_CONFIG['max_retries'],
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'authority': 'www.qyyjt.cn',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'client': 'pc-web;pro',
            'content-type': 'application/json;charset=UTF-8',
            'origin': self.base_url,
            'pragma': 'no-cache',
            'referer': f'{self.base_url}/login',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'system': 'new',
            'terminal': 'pc-web;pro',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'ver': '20240624'
        }

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        return random_str

    def _random_sleep(self):
        """随机延时"""
        delay = random.uniform(
            SPIDER_CONFIG['request_delay_min'],
            SPIDER_CONFIG['request_delay_max']
        )
        time.sleep(delay)

    def _encrypt_password(self, password: str) -> str:
        """加密密码"""
        return hashlib.md5(password.encode()).hexdigest().upper()

    def login(self) -> bool:
        """登录并获取token"""
        try:
            self.session.get(self.base_url, headers=self.headers)
            self._random_sleep()

            login_url = f"{self.base_url}/getData.action"
            login_data = {
                "root_type": "user",
                "skip": 0,
                "pagesize": 15,
                "text": self.username
            }

            self.logger.info(f"尝试登录: {self.username}")
            response = self.session.post(
                login_url,
                headers=self.headers,
                json=login_data,
                timeout=SPIDER_CONFIG['timeout']
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    user_list = result.get("data", {}).get("list", [])
                    if user_list:
                        user_info = user_list[0]
                        self.user_id = user_info.get("code")
                        self.token = user_info.get("token")
                        if self.token:
                            self.headers["pcuss"] = self.token
                            self.logger.info("登录成功")
                            return True

            self.logger.error(f"登录失败: {response.text}")
            return False

        except Exception as e:
            self.logger.error(f"登录异常: {str(e)}")
            return False

    def _make_request(self, method: str, url: str, params: Optional[Dict] = None,
                      data: Optional[Dict] = None, retry_count: int = 3) -> Optional[Dict]:
        """发送请求并处理响应"""
        for i in range(retry_count):
            try:
                request_id = self._generate_request_id()
                self.headers.update({
                    'x-request-id': request_id,
                    'x-request-url': url.replace(self.base_url, '')
                })

                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data if method.upper() == 'POST' else None,
                    timeout=SPIDER_CONFIG['timeout']
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 104:  # 登录状态异常
                        if self.login() and i < retry_count - 1:
                            continue
                    return result
                elif response.status_code == 401:
                    if self.login() and i < retry_count - 1:
                        continue

            except Exception as e:
                self.logger.error(f"请求异常 {url}: {str(e)}")
                if i == retry_count - 1:
                    return None

            self._random_sleep()

        return None

    def get_market_table(self) -> Optional[pd.DataFrame]:
        """获取市场化经营主体表格数据"""
        try:
            self.session.get(
                f"{self.base_url}/bond/newExitTopic/mark",
                headers=self.headers
            )
            self._random_sleep()

            url = f"{self.base_url}/getData.action"
            data = {
                "root_type": "bond",
                "skip": 0,
                "pagesize": 100,
                "sort": "updateTime,desc"
            }

            response = self._make_request(method="POST", url=url, data=data)

            if response:
                data_list = response.get("data", {}).get("list", [])
                if data_list:
                    df = pd.DataFrame(data_list)
                    self.logger.info(f"获取到 {len(df)} 条数据")
                    return df

            return None

        except Exception as e:
            self.logger.error(f"获取表格数据异常: {str(e)}")
            return None

    def save_to_excel(self, df: pd.DataFrame, filename: str = "market_data.xlsx") -> None:
        """保存数据到Excel"""
        try:
            df.to_excel(filename, index=False)
            self.logger.info(f"数据已保存到 {filename}")
        except Exception as e:
            self.logger.error(f"保存数据异常: {str(e)}")
