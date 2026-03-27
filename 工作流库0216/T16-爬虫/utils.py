#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块 - 企业预警通地方化债数据爬虫
提供日志、请求处理和数据处理等功能
"""

import os
import time
import json
import random
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import requests
import pandas as pd

import config


def setup_logger(name: str = "债务预警爬虫") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 获取logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()

    # 创建文件处理器
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def generate_request_id() -> str:
    """
    生成随机的请求ID

    Returns:
        str: 随机请求ID（20位字符）
    """
    return str(uuid.uuid4()).replace('-', '')[:20]


def safe_request(
    url: str,
    method: str = "POST",
    params: Optional[Dict] = None,
    data: Optional[Union[Dict, str]] = None,
    headers: Optional[Dict] = None,
    timeout: int = None,
    retries: int = None
) -> Optional[Dict]:
    """
    安全的发送HTTP请求并处理可能的错误

    Args:
        url: 请求URL
        method: 请求方法，默认为POST
        params: URL参数
        data: 请求体数据
        headers: 请求头
        timeout: 超时时间
        retries: 重试次数

    Returns:
        Optional[Dict]: 返回解析后的JSON数据，失败则返回None
    """
    logger = logging.getLogger("债务预警爬虫")

    # 使用配置中的默认值
    if timeout is None:
        timeout = config.TIMEOUT
    if retries is None:
        retries = config.MAX_RETRIES

    # 准备请求头
    if headers is None:
        if method.upper() == "GET":
            headers = config.get_list_api_headers()
        else:
            headers = config.get_list_api_headers()

    # 日志记录请求信息
    logger.debug(f"请求URL: {url}")
    logger.debug(f"请求方法: {method}")
    logger.debug(f"请求头: {json.dumps(headers, ensure_ascii=False)[:200]}")
    if data:
        logger.debug(f"请求体: {str(data)[:200]}")

    # 随机延迟
    delay_time = random.uniform(*config.REQUEST_DELAY)
    logger.debug(f"请求延迟: {delay_time:.2f}秒")
    time.sleep(delay_time)

    # 创建请求会话
    session = requests.Session()

    # 设置用户代理
    if "User-Agent" in headers or "user-agent" in headers:
        user_agent = headers.get("User-Agent") or headers.get("user-agent")
        session.headers.update({"User-Agent": user_agent})

    # 创建请求对象
    req = requests.Request(
        method=method.upper(),
        url=url,
        params=params,
        data=data,
        headers=headers
    )

    # 准备请求
    prepped = session.prepare_request(req)

    # 重试计数
    attempt = 0
    max_retry_delay = 30

    while attempt < retries:
        try:
            logger.debug(f"发送请求 (尝试 {attempt+1}/{retries})")

            # 发送请求
            response = session.send(prepped, timeout=timeout)

            # 记录响应状态
            logger.debug(f"响应状态码: {response.status_code}")

            # 处理不同响应状态
            if response.status_code == 200:
                try:
                    result = response.json()

                    # 检查API返回码
                    if "returncode" in result and result["returncode"] != 0:
                        error_code = result.get("returncode")
                        error_msg = result.get("info", "未知错误")
                        logger.warning(f"API返回错误: {error_code} - {error_msg}")

                        # Token过期
                        if error_code == 104:
                            logger.error("Token已过期，请更新环境变量QYYJT_COOKIE的值")
                            return None

                        # 其他错误重试
                        if attempt < retries - 1:
                            retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 3), max_retry_delay)
                            logger.warning(f"API错误，将在 {retry_delay:.2f} 秒后重试...")
                            time.sleep(retry_delay)
                            attempt += 1
                            continue

                    return result

                except json.JSONDecodeError:
                    logger.error("响应不是有效的JSON格式")
                    logger.debug(f"响应内容: {response.text[:200]}...")

                    if "<html" in response.text.lower():
                        logger.error("收到HTML响应，可能是被重定向到登录页面")

                    if attempt < retries - 1:
                        retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 3), max_retry_delay)
                        time.sleep(retry_delay)
                        attempt += 1
                        continue

                    return None

            elif response.status_code == 418:
                # 反爬虫响应
                logger.warning(f"遇到反爬虫响应(418)，等待后重试...")

                if attempt < retries - 1:
                    retry_delay = min(10 * (2 ** attempt) + random.uniform(5, 15), max_retry_delay * 2)
                    logger.warning(f"将在 {retry_delay:.2f} 秒后重试...")
                    time.sleep(retry_delay)

                    # 更新请求头
                    new_headers = headers.copy()
                    new_headers["x-request-id"] = config.generate_request_id()
                    req = requests.Request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        data=data,
                        headers=new_headers
                    )
                    prepped = session.prepare_request(req)

                    attempt += 1
                    continue
                else:
                    logger.error(f"连续 {retries} 次遇到反爬机制，放弃请求")
                    return None

            elif response.status_code == 429:
                # 请求过多
                logger.warning("请求过多(429)，需要降低请求频率")

                if attempt < retries - 1:
                    retry_delay = min(15 * (2 ** attempt) + random.uniform(10, 20), max_retry_delay * 3)
                    time.sleep(retry_delay)
                    attempt += 1
                    continue
                else:
                    logger.error(f"连续 {retries} 次请求过多，放弃请求")
                    return None

            else:
                logger.error(f"HTTP错误: {response.status_code}")
                logger.debug(f"响应内容: {response.text[:200]}...")

                if attempt < retries - 1:
                    retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 5), max_retry_delay)
                    time.sleep(retry_delay)
                    attempt += 1
                    continue
                else:
                    logger.error(f"连续 {retries} 次HTTP错误，放弃请求")
                    return None

        except requests.exceptions.Timeout:
            logger.warning("请求超时")

            if attempt < retries - 1:
                retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 3), max_retry_delay)
                time.sleep(retry_delay)
                attempt += 1
                continue
            else:
                logger.error(f"连续 {retries} 次请求超时，放弃请求")
                return None

        except requests.exceptions.ConnectionError:
            logger.warning("连接错误")

            if attempt < retries - 1:
                retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 3), max_retry_delay)
                time.sleep(retry_delay)
                attempt += 1
                continue
            else:
                logger.error(f"连续 {retries} 次连接错误，放弃请求")
                return None

        except Exception as e:
            logger.error(f"请求过程中发生异常: {str(e)}")

            if attempt < retries - 1:
                retry_delay = min(5 * (2 ** attempt) + random.uniform(1, 3), max_retry_delay)
                time.sleep(retry_delay)
                attempt += 1
                continue
            else:
                logger.error(f"连续 {retries} 次请求异常，放弃请求")
                return None

        attempt += 1

    logger.error(f"请求失败，已达到最大重试次数 {retries}")
    return None


def process_news_data(news_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理新闻数据，提取关键字段

    Args:
        news_item: 原始新闻数据项

    Returns:
        Dict[str, Any]: 处理后的新闻数据
    """
    return {
        "新闻ID": news_item.get("newsCode", ""),
        "标题": news_item.get("title", ""),
        "摘要": news_item.get("summary", ""),
        "发布日期": news_item.get("dateEPT", ""),
        "来源": news_item.get("source", "") or news_item.get("sourceEPT", ""),
        "标签": news_item.get("labeltag", ""),
        "详情链接": news_item.get("detailUrl", "") or f"{config.BASE_URL}{news_item.get('pcContentLink', '')}",
        "相关机构": ",".join([org.get("name", "") for org in news_item.get("relatedOrgs", [])]),
        "地区分类": news_item.get("areaClassifyMoreEPT", ""),
        "主题": (news_item.get("theme", {}) or {}).get("title", "") if news_item.get("theme") else "",
        "阅读量": news_item.get("readTotal", 0),
        "新闻类型": news_item.get("subTitle", ""),
        "skipParam": news_item.get("skipParam", ""),
    }


def save_data_to_csv(
    data: List[Dict[str, Any]],
    filename: Path = None,
    mode: str = "a"
) -> None:
    """
    将数据保存为CSV文件

    Args:
        data: 要保存的数据列表
        filename: 文件路径
        mode: 写入模式，a为追加，w为覆盖
    """
    logger = logging.getLogger("债务预警爬虫")

    if filename is None:
        filename = config.OUTPUT_FILE

    df = pd.DataFrame(data)

    # 检查文件是否存在
    file_exists = filename.exists()

    if mode == "a" and file_exists:
        df.to_csv(filename, mode="a", index=False, header=False, encoding="utf-8-sig")
        logger.info(f"已追加 {len(data)} 条数据到 {filename}")
    else:
        df.to_csv(filename, mode="w", index=False, encoding="utf-8-sig")
        logger.info(f"已保存 {len(data)} 条数据到 {filename}")


def read_last_crawl() -> Optional[str]:
    """
    读取上次爬取的时间或ID

    Returns:
        Optional[str]: 上次爬取的时间或ID，如果不存在则返回None
    """
    if not config.LAST_CRAWL_FILE.exists():
        return None

    with open(config.LAST_CRAWL_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_last_crawl(value: str) -> None:
    """
    保存本次爬取的时间或ID

    Args:
        value: 要保存的时间或ID
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.LAST_CRAWL_FILE, "w", encoding="utf-8") as f:
        f.write(value)


def read_last_skip_param() -> str:
    """
    读取上次爬取的skipParam

    Returns:
        str: 上次爬取的skipParam，如果不存在则返回初始值
    """
    if not config.LAST_SKIP_PARAM_FILE.exists():
        return config.INITIAL_SKIP_PARAM

    with open(config.LAST_SKIP_PARAM_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_last_skip_param(value: str) -> None:
    """
    保存本次爬取的skipParam

    Args:
        value: 要保存的skipParam
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.LAST_SKIP_PARAM_FILE, "w", encoding="utf-8") as f:
        f.write(value)


def format_timestamp_to_date(timestamp: int) -> str:
    """
    将时间戳转换为日期字符串

    Args:
        timestamp: 毫秒级时间戳

    Returns:
        str: 格式化的日期字符串 (YYYY-MM-DD HH:MM:SS)
    """
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_timestamp() -> int:
    """
    获取当前时间的毫秒级时间戳

    Returns:
        int: 当前时间的毫秒级时间戳
    """
    return int(time.time() * 1000)


def export_request_debug(
    url: str,
    method: str,
    headers: Dict,
    data: Optional[str] = None
) -> None:
    """
    导出请求信息用于调试

    Args:
        url: 请求URL
        method: 请求方法
        headers: 请求头
        data: 请求体数据
    """
    logger = logging.getLogger("债务预警爬虫")
    logger.debug("====== 请求调试信息 ======")
    logger.debug(f"请求方法: {method}")
    logger.debug(f"请求URL: {url}")
    logger.debug(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    if data:
        logger.debug(f"请求体: {data}")
    logger.debug("==========================")


def load_cookie_from_file() -> Optional[str]:
    """
    从cookie.txt文件加载Cookie

    Returns:
        Optional[str]: Cookie字符串，失败返回None
    """
    logger = logging.getLogger("债务预警爬虫")
    cookie_file = config.PROJECT_ROOT / "cookie.txt"

    if cookie_file.exists():
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookie = f.read().strip()
                if cookie:
                    logger.info(f"已从文件加载Cookie: {cookie[:30]}...")
                    return cookie
        except Exception as e:
            logger.error(f"从文件加载Cookie失败: {e}")

    return None
