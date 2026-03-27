# -*- coding: utf-8 -*-
"""
T56-企业预警通新闻爬取 核心模块
"""
from .news_spider import NewsSpider
from .data_storage import DataStorage

__all__ = ['NewsSpider', 'DataStorage']
