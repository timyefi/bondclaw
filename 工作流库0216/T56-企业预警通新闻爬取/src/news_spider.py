# -*- coding: utf-8 -*-
"""
新闻爬虫模块
"""
import requests
import json
import time
import random
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QYYJT_BASE_URL, QYYJT_PC_USS, SPIDER_CONFIG


class NewsSpider:
    """企业预警通新闻爬虫类"""

    def __init__(self, pcuss: str = None):
        self.base_url = QYYJT_BASE_URL
        self.pcuss = pcuss or QYYJT_PC_USS
        self.session = requests.Session()
        self._setup_logging()
        self._setup_session()

    def _setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _setup_session(self):
        """配置会话"""
        self.session.headers.update(self._get_default_headers())

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'authority': 'www.qyyjt.cn',
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'client': 'pc-web;pro',
            'content-type': 'application/json;charset=UTF-8',
            'origin': self.base_url,
            'pcuss': self.pcuss,
            'referer': f'{self.base_url}/publicOpinons/bondMarket',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'system': 'new',
            'terminal': 'pc-web;pro',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'ver': '20240903'
        }

    def _random_sleep(self):
        """随机延时"""
        delay = random.uniform(
            SPIDER_CONFIG['request_delay_min'],
            SPIDER_CONFIG['request_delay_max']
        )
        time.sleep(delay)

    def fetch_news(self, bdate: str, edate: str, topic_code: str = 'areaNews',
                   sub_type: str = 'policyDynamic', pagesize: int = 15,
                   skip: int = 0) -> Optional[List[Dict]]:
        """获取新闻数据"""
        url = f'{self.base_url}/getData.action'

        data = {
            'bdate': bdate,
            'edate': edate,
            'pagesize': pagesize,
            'skipParam': skip,
            'subType': sub_type,
            'topicCode': topic_code
        }

        try:
            response = self.session.post(
                url,
                json=data,
                timeout=SPIDER_CONFIG['timeout']
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    news_list = result.get('data', {}).get('news', [])
                    self.logger.info(f"成功获取 {len(news_list)} 条新闻")
                    return news_list
                else:
                    self.logger.error(f"API返回错误: {result.get('msg')}")
            else:
                self.logger.error(f"HTTP错误: {response.status_code}")

        except Exception as e:
            self.logger.error(f"请求异常: {str(e)}")

        self._random_sleep()
        return None

    def fetch_news_by_date_range(self, start_date: datetime, end_date: datetime,
                                  topic_code: str = 'areaNews',
                                  sub_type: str = 'policyDynamic') -> pd.DataFrame:
        """按日期范围获取新闻"""
        all_news = []
        current_date = start_date

        while current_date <= end_date:
            bdate = current_date.strftime('%Y%m%d000000')
            edate = (current_date + timedelta(hours=23, minutes=59, seconds=59)).strftime('%Y%m%d235959')

            news_list = self.fetch_news(bdate, edate, topic_code, sub_type)
            if news_list:
                all_news.extend(news_list)

            self.logger.info(f"已处理: {current_date.strftime('%Y-%m-%d')}")
            current_date += timedelta(days=1)

        if all_news:
            df = pd.DataFrame(all_news)
            return df
        return pd.DataFrame()

    def fetch_news_hourly(self, target_date: datetime, topic_code: str = 'areaNews',
                          sub_type: str = 'policyDynamic') -> pd.DataFrame:
        """按小时获取新闻（一天24小时）"""
        all_news = []

        for hour in range(24):
            bdate = target_date.replace(hour=hour, minute=0, second=0).strftime('%Y%m%d%H%M%S')
            edate = target_date.replace(hour=hour, minute=59, second=59).strftime('%Y%m%d%H%M%S')

            news_list = self.fetch_news(bdate, edate, topic_code, sub_type)
            if news_list:
                all_news.extend(news_list)

            self.logger.info(f"已处理: {target_date.strftime('%Y-%m-%d')} {hour}:00")

        if all_news:
            df = pd.DataFrame(all_news)
            return df
        return pd.DataFrame()
