#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
企业预警通地方化债数据爬虫主程序
"""

import os
import json
import time
import logging
import argparse
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from tqdm import tqdm

import config
from utils import (
    setup_logger,
    safe_request,
    process_news_data,
    save_data_to_csv,
    read_last_crawl,
    save_last_crawl,
    read_last_skip_param,
    save_last_skip_param,
    get_current_timestamp,
    export_request_debug,
    load_cookie_from_file
)


class DebtDataCrawler:
    """地方化债数据爬虫类"""

    def __init__(self):
        """初始化爬虫"""
        self.logger = setup_logger()
        self.logger.info("初始化地方化债数据爬虫")

        # 确保数据目录存在
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 上次爬取的记录
        self.last_crawl_id = read_last_crawl()
        self.last_skip_param = read_last_skip_param()

    def get_total_count(self) -> int:
        """
        获取数据总数

        Returns:
            int: 数据总数
        """
        params = config.DEFAULT_PARAMS.copy()

        # 更新User-Agent
        config.update_user_agent()

        # 添加随机延迟
        time.sleep(random.uniform(1, 3))

        response = safe_request(
            url=f"{config.API_URL}?_t=1447",
            method="POST",
            data=params,
            headers=config.get_list_api_headers()
        )

        if response and isinstance(response, dict):
            if "data" in response and "news" in response["data"]:
                return response.get("data", {}).get("total", 0)
            return response.get("total", 0)

        return 0

    def crawl_data_by_param(
        self,
        skip_param: str = "",
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """
        根据skipParam爬取数据

        Args:
            skip_param: 分页参数skipParam
            limit: 每页数量

        Returns:
            Tuple[List[Dict[str, Any]], str, bool]:
                返回处理后的数据列表、下一页的skipParam和是否需要继续爬取的标志
        """
        self.logger.info(f"使用skipParam: {skip_param if skip_param else '初始页'}")

        # 准备请求数据
        request_data = {
            "topicCode": "areaNews",
            "subType": "localizedBonds"
        }

        if skip_param:
            request_data["skipParam"] = skip_param

        # 防止请求过于频繁
        time.sleep(random.uniform(*config.REQUEST_DELAY))

        # 转换为JSON字符串
        json_data = json.dumps(request_data)
        self.logger.debug(f"请求体: {json_data}")

        try:
            # 获取请求头
            headers = config.get_list_api_headers()

            # 导出调试信息
            export_request_debug(
                url=f"{config.API_URL}?_t=1447",
                method="POST",
                headers=headers,
                data=json_data
            )

            # 发送请求
            response = safe_request(
                url=f"{config.API_URL}?_t=1447",
                method="POST",
                data=json_data,
                headers=headers
            )

            if not response or not isinstance(response, dict):
                self.logger.error(f"获取数据失败，skipParam: {skip_param}")
                return [], "", False

            # 解析新闻列表
            news_list = []
            if "data" in response and "news" in response["data"]:
                news_list = response["data"]["news"]
                self.logger.info(f"从data.news中获取到 {len(news_list)} 条新闻")
            elif "news" in response:
                news_list = response["news"]
                self.logger.info(f"从news中获取到 {len(news_list)} 条新闻")
            else:
                self.logger.warning(f"未在响应中找到news字段: {json.dumps(response)[:200]}...")

            processed_data = []
            continue_crawl = True
            next_skip_param = ""

            # 获取下一页的skipParam
            if news_list and len(news_list) >= 1:
                next_skip_param = news_list[-1].get("skipParam", "")
                self.logger.debug(f"下一页skipParam: {next_skip_param}")

            # 处理新闻列表
            for news_item in news_list:
                # 增量更新检查
                if config.INCREMENTAL and self.last_crawl_id:
                    current_id = news_item.get("newsCode", "")
                    if current_id == self.last_crawl_id:
                        self.logger.info(f"已到达上次爬取的位置: {current_id}")
                        continue_crawl = False
                        break

                processed_news = process_news_data(news_item)
                processed_data.append(processed_news)

            # 判断是否还有下一页
            if not news_list or len(news_list) < limit:
                self.logger.info("未获取到足够数据，可能是最后一页")
                continue_crawl = False

            return processed_data, next_skip_param, continue_crawl

        except Exception as e:
            self.logger.error(f"爬取数据时发生异常: {str(e)}")
            return [], skip_param, True

    def crawl_all_data(
        self,
        max_pages: int = None,
        limit: int = 20,
        start_skip_param: str = ""
    ) -> List[Dict[str, Any]]:
        """
        爬取所有数据

        Args:
            max_pages: 最大页数
            limit: 每页数量
            start_skip_param: 起始skipParam

        Returns:
            List[Dict[str, Any]]: 所有爬取的数据
        """
        if max_pages is None:
            max_pages = config.MAX_PAGES

        self.logger.info(f"开始爬取所有数据, 最大页数: {max_pages}, 每页数量: {limit}")

        # 确定起始skipParam
        if not start_skip_param and config.LAST_SKIP_PARAM_FILE.exists() and not config.RESET_SKIP_PARAM:
            skip_param = read_last_skip_param()
            if skip_param:
                self.logger.info(f"从文件读取上次的skipParam: {skip_param}")
            else:
                skip_param = config.INITIAL_SKIP_PARAM
        else:
            skip_param = start_skip_param if start_skip_param else config.INITIAL_SKIP_PARAM

        all_data = []
        error_count = 0
        page_count = 0
        first_id = ""
        first_skip_param = ""
        empty_count = 0
        max_empty_count = 3

        # 自适应延迟
        min_delay = config.REQUEST_DELAY[0]
        max_delay = config.REQUEST_DELAY[1]
        current_delay = min_delay

        self.logger.info(f"初始请求延迟范围: {min_delay} - {max_delay} 秒")

        while page_count < max_pages:
            self.logger.info(f"正在爬取第 {page_count+1} 页")

            actual_delay = random.uniform(current_delay, current_delay * 1.5)
            self.logger.debug(f"当前页延迟: {actual_delay:.2f} 秒")
            time.sleep(actual_delay)

            try:
                data, next_skip_param, continue_crawl = self.crawl_data_by_param(skip_param, limit)

                if data:
                    # 保存第一条数据信息
                    if page_count == 0 and not first_id and data:
                        first_id = data[0].get("新闻ID", "")
                        first_skip_param = data[0].get("skipParam", "")
                        self.logger.info(f"首条数据ID: {first_id}")
                        self.logger.info(f"首条数据标题: {data[0].get('标题', '无标题')}")

                        if first_id:
                            save_last_crawl(first_id)

                    all_data.extend(data)

                    # 每页保存一次
                    save_data_to_csv(
                        data,
                        mode="a" if page_count > 0 or config.OUTPUT_FILE.exists() else "w"
                    )

                    if next_skip_param:
                        save_last_skip_param(next_skip_param)

                    # 重置计数
                    error_count = 0
                    empty_count = 0
                    current_delay = max(current_delay * 0.9, min_delay)

                    if not continue_crawl:
                        self.logger.info("已到达最后一页数据，停止爬取")
                        break

                    skip_param = next_skip_param
                else:
                    empty_count += 1
                    error_count += 1
                    self.logger.warning(f"第 {page_count+1} 页未获取到数据，空响应计数: {empty_count}/{max_empty_count}")

                    if empty_count >= max_empty_count:
                        self.logger.warning(f"连续 {empty_count} 次未获取到数据，可能已到达最后一页")
                        break

                    current_delay = min(current_delay * 1.5, max_delay * 3)
                    self.logger.warning(f"增加延迟到 {current_delay:.2f} 秒")

                    if error_count >= 3:
                        wait_time = 30 + random.uniform(0, 10)
                        self.logger.error(f"连续 {error_count} 次未获取到数据，等待 {wait_time:.2f} 秒")
                        time.sleep(wait_time)

                    if error_count >= 5:
                        self.logger.error(f"连续 {error_count} 次未获取到数据，中断爬取")
                        break

                page_count += 1

            except Exception as e:
                self.logger.exception(f"爬取过程中发生异常: {e}")
                error_count += 1
                current_delay = min(current_delay * 2, max_delay * 3)

                if error_count >= 3:
                    wait_time = 60 + random.uniform(0, 30)
                    self.logger.error(f"连续 {error_count} 次发生异常，等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)

                if error_count >= 5:
                    self.logger.error(f"连续 {error_count} 次发生异常，中断爬取")
                    break

        self.logger.info(f"爬取完成，共爬取 {len(all_data)} 条数据，{page_count} 页")
        return all_data

    def crawl_by_skip_param_list(
        self,
        skip_param_list: List[str] = None,
        max_pages_per_param: int = 30
    ) -> List[Dict[str, Any]]:
        """
        按照skipParam列表分别爬取数据

        Args:
            skip_param_list: skipParam列表
            max_pages_per_param: 每个skipParam爬取的最大页数

        Returns:
            List[Dict[str, Any]]: 所有爬取的数据
        """
        if skip_param_list is None:
            skip_param_list = config.SKIP_PARAM_LIST

        if not skip_param_list:
            self.logger.warning("skipParam列表为空，使用默认方法爬取")
            return self.crawl_all_data()

        self.logger.info(f"开始按照skipParam列表爬取数据，共 {len(skip_param_list)} 个起始点")

        all_data = []
        success_count = 0

        for i, skip_param in enumerate(skip_param_list):
            self.logger.info(f"开始爬取第 {i+1}/{len(skip_param_list)} 个起始点: {skip_param}")

            try:
                batch_data = self.crawl_batch_data(skip_param, max_pages_per_param)

                if batch_data:
                    all_data.extend(batch_data)
                    success_count += 1
                    self.logger.info(f"成功爬取第 {i+1} 个起始点的数据，获取 {len(batch_data)} 条")
                else:
                    self.logger.warning(f"第 {i+1} 个起始点未获取到数据")

                wait_time = random.uniform(10, 20)
                self.logger.info(f"等待 {wait_time:.2f} 秒后爬取下一个起始点")
                time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"爬取第 {i+1} 个起始点时发生异常: {e}")

        self.logger.info(f"按skipParam列表爬取完成，共爬取 {len(all_data)} 条数据，成功起始点: {success_count}/{len(skip_param_list)}")
        return all_data

    def crawl_batch_data(
        self,
        start_skip_param: str,
        max_pages: int = 30
    ) -> List[Dict[str, Any]]:
        """
        从指定的skipParam开始爬取一批数据

        Args:
            start_skip_param: 起始skipParam
            max_pages: 最大爬取页数

        Returns:
            List[Dict[str, Any]]: 爬取的数据
        """
        self.logger.info(f"开始从 {start_skip_param} 爬取批次数据, 最大页数: {max_pages}")

        all_data = []
        error_count = 0
        page_count = 0
        skip_param = start_skip_param
        empty_count = 0
        max_empty_count = 3

        min_delay = config.REQUEST_DELAY[0]
        max_delay = config.REQUEST_DELAY[1]
        current_delay = min_delay

        while page_count < max_pages:
            self.logger.info(f"正在爬取批次 {page_count+1}/{max_pages} 页")

            actual_delay = random.uniform(current_delay, current_delay * 1.5)
            time.sleep(actual_delay)

            try:
                data, next_skip_param, continue_crawl = self.crawl_data_by_param(skip_param)

                if data:
                    all_data.extend(data)
                    save_data_to_csv(
                        data,
                        mode="a" if config.OUTPUT_FILE.exists() else "w"
                    )
                    error_count = 0
                    empty_count = 0
                    current_delay = max(current_delay * 0.9, min_delay)

                    if not continue_crawl or not next_skip_param:
                        self.logger.info("批次爬取完成，没有更多数据")
                        break

                    skip_param = next_skip_param
                else:
                    empty_count += 1
                    error_count += 1

                    if empty_count >= max_empty_count:
                        self.logger.warning(f"连续 {empty_count} 次未获取到数据，停止批次爬取")
                        break

                    current_delay = min(current_delay * 1.5, max_delay * 3)

                    if error_count >= 3:
                        time.sleep(30 + random.uniform(0, 10))

                    if error_count >= 5:
                        break

                page_count += 1

            except Exception as e:
                self.logger.exception(f"批次爬取过程中发生异常: {e}")
                error_count += 1
                current_delay = min(current_delay * 2, max_delay * 3)

                if error_count >= 3:
                    time.sleep(60 + random.uniform(0, 30))

                if error_count >= 5:
                    break

        self.logger.info(f"批次爬取完成，共爬取 {len(all_data)} 条数据，{page_count} 页")
        return all_data

    def run(self) -> None:
        """运行爬虫"""
        self.logger.info("开始爬取地方化债数据")
        start_time = time.time()

        try:
            # 尝试从文件加载Cookie
            cookie = load_cookie_from_file()
            if cookie:
                config.DEFAULT_COOKIE = cookie

            # 使用skipParam列表爬取
            all_data = self.crawl_by_skip_param_list()

            end_time = time.time()
            duration = end_time - start_time

            self.logger.info(f"爬取完成，共爬取 {len(all_data)} 条数据，耗时 {duration:.2f} 秒")

        except Exception as e:
            self.logger.exception(f"爬取过程中发生错误: {e}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="企业预警通地方化债数据爬虫")
    parser.add_argument("--incremental", action="store_true", help="是否增量爬取")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--limit", type=int, default=20, help="每页数量")
    parser.add_argument("--max-pages", type=int, default=config.MAX_PAGES, help="最大爬取页数")
    parser.add_argument("--delay", type=float, default=config.CRAWL_DELAY, help="请求间隔时间(秒)")
    parser.add_argument("--reset-skip", action="store_true", help="是否重置skip参数")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 更新配置
    if args.incremental is not None:
        config.INCREMENTAL = args.incremental

    if args.output:
        config.OUTPUT_FILE = Path(args.output)

    if args.max_pages:
        config.MAX_PAGES = args.max_pages

    if args.delay:
        config.CRAWL_DELAY = args.delay

    if args.reset_skip:
        config.RESET_SKIP_PARAM = True

    # 运行爬虫
    crawler = DebtDataCrawler()
    crawler.run()
