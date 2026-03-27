#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
详情页爬虫 - 企业预警通地方化债数据爬虫
用于爬取新闻详情内容
"""

import os
import re
import time
import json
import random
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

import config
from utils import safe_request, setup_logger


class DetailCrawler:
    """详情页爬虫类"""

    def __init__(self, csv_file: Path = None):
        """
        初始化详情页爬虫

        Args:
            csv_file: CSV文件路径，包含待爬取的详情页URL
        """
        self.logger = logging.getLogger("债务预警爬虫")

        if csv_file is None:
            csv_file = config.OUTPUT_FILE
        self.csv_file = csv_file

        # 详情页保存路径
        self.detail_dir = config.DATA_DIR / "详情页"
        self.detail_dir.mkdir(parents=True, exist_ok=True)

    def load_urls(self) -> pd.DataFrame:
        """
        从CSV文件加载URL列表

        Returns:
            pd.DataFrame: 包含URL的DataFrame
        """
        if not self.csv_file.exists():
            self.logger.error(f"CSV文件不存在: {self.csv_file}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(self.csv_file, encoding="utf-8-sig")
            if "详情链接" not in df.columns or "新闻ID" not in df.columns:
                self.logger.error(f"CSV文件缺少必要的列: 详情链接 或 新闻ID")
                return pd.DataFrame()

            return df
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            return pd.DataFrame()

    def crawl_detail(self, url: str, news_id: str) -> Dict[str, Any]:
        """
        爬取详情页内容

        Args:
            url: 详情页URL
            news_id: 新闻ID

        Returns:
            Dict[str, Any]: 详情页内容
        """
        self.logger.info(f"爬取详情页: {url}")

        # 检查是否已经爬取过
        detail_file = self.detail_dir / f"{news_id}.html"
        if detail_file.exists():
            self.logger.info(f"详情页已存在: {detail_file}")
            with open(detail_file, "r", encoding="utf-8") as f:
                content = f.read()
            return {"news_id": news_id, "content": content, "url": url}

        # 从URL中提取id和type参数
        url_parts = url.split("?")
        if len(url_parts) < 2:
            self.logger.error(f"无效的URL格式: {url}")
            return {"news_id": news_id, "content": "", "url": url}

        # 解析参数
        query_params = {}
        for param in url_parts[1].split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                query_params[key] = value

        # 提取id和type
        content_id = query_params.get("id", "")
        content_type = query_params.get("type", "news")

        if not content_id:
            self.logger.error(f"URL中未找到id参数: {url}")
            return {"news_id": news_id, "content": "", "url": url}

        # 构建API URL
        api_url = f"{config.DETAIL_API_URL}?id={content_id}&type={content_type}&_t=1448"

        # 准备请求头
        headers = config.get_detail_api_headers(content_id)

        # 防止请求过于频繁
        time.sleep(random.uniform(*config.REQUEST_DELAY))

        # 发送请求
        response = safe_request(
            url=api_url,
            method="GET",
            headers=headers
        )

        if not response:
            self.logger.error(f"获取详情页失败: {api_url}")
            return {"news_id": news_id, "content": "", "url": url}

        # 处理API响应
        content = ""
        if isinstance(response, dict):
            content = json.dumps(response, ensure_ascii=False, indent=2)

            # 提取正文内容
            article_content = response.get("data", {}).get("content", "")
            if article_content:
                content_file = self.detail_dir / f"{news_id}_content.html"
                with open(content_file, "w", encoding="utf-8") as f:
                    f.write(article_content)
                self.logger.info(f"已保存正文内容: {content_file}")
        else:
            content = str(response)

        # 保存详情页响应
        with open(detail_file, "w", encoding="utf-8") as f:
            f.write(content)

        return {"news_id": news_id, "content": content, "url": url}

    def extract_content(self, html: str) -> Dict[str, Any]:
        """
        从HTML中提取正文内容

        Args:
            html: HTML内容或JSON字符串

        Returns:
            Dict[str, Any]: 提取的内容
        """
        try:
            # 尝试解析为JSON
            try:
                json_data = json.loads(html)
                if "data" in json_data and "content" in json_data.get("data", {}):
                    data = json_data.get("data", {})
                    return {
                        "title": data.get("title", ""),
                        "content": data.get("content", ""),
                        "date": data.get("publishDate", ""),
                        "source": data.get("source", ""),
                        "attachments": data.get("attachments", [])
                    }
            except json.JSONDecodeError:
                pass

            # 尝试作为HTML解析
            soup = BeautifulSoup(html, "html.parser")

            # 提取标题
            title_elem = soup.select_one(".article-title")
            title = title_elem.text.strip() if title_elem else ""

            # 提取正文
            content_elem = soup.select_one(".article-content")
            content = content_elem.text.strip() if content_elem else ""

            # 提取发布时间
            date_elem = soup.select_one(".article-date")
            date = date_elem.text.strip() if date_elem else ""

            # 提取来源
            source_elem = soup.select_one(".article-source")
            source = source_elem.text.strip() if source_elem else ""

            # 提取附件
            attachments = []
            for a in soup.select(".attachment a"):
                attachments.append({
                    "name": a.text.strip(),
                    "url": a.get("href", "")
                })

            return {
                "title": title,
                "content": content,
                "date": date,
                "source": source,
                "attachments": attachments
            }
        except Exception as e:
            self.logger.error(f"解析内容失败: {e}")
            return {}

    def save_details_to_csv(self, details: List[Dict[str, Any]]) -> None:
        """
        将详情内容保存到CSV文件

        Args:
            details: 详情内容列表
        """
        if not details:
            self.logger.warning("没有详情内容需要保存")
            return

        # 提取需要保存的字段
        csv_data = []
        for detail in details:
            news_id = detail.get("news_id", "")
            content = detail.get("content", "")
            url = detail.get("url", "")

            # 提取内容
            extracted = {}
            try:
                try:
                    json_data = json.loads(content)
                    if "data" in json_data:
                        data = json_data.get("data", {})
                        extracted = {
                            "标题": data.get("title", ""),
                            "正文": data.get("content", ""),
                            "发布日期": data.get("publishDate", ""),
                            "来源": data.get("source", ""),
                        }
                except:
                    extracted_content = self.extract_content(content)
                    extracted = {
                        "标题": extracted_content.get("title", ""),
                        "正文": extracted_content.get("content", ""),
                        "发布日期": extracted_content.get("date", ""),
                        "来源": extracted_content.get("source", ""),
                    }
            except Exception as e:
                self.logger.error(f"提取内容失败: {e}")

            csv_row = {
                "新闻ID": news_id,
                "详情链接": url,
                "标题": extracted.get("标题", ""),
                "正文": extracted.get("正文", ""),
                "发布日期": extracted.get("发布日期", ""),
                "来源": extracted.get("来源", ""),
            }
            csv_data.append(csv_row)

        # 保存到CSV
        df = pd.DataFrame(csv_data)
        output_file = config.DATA_DIR / "详情数据.csv"

        mode = "a" if output_file.exists() else "w"
        header = not output_file.exists()

        df.to_csv(output_file, mode=mode, index=False, header=header, encoding="utf-8-sig")
        self.logger.info(f"已保存 {len(csv_data)} 条详情到CSV: {output_file}")

    def run(self) -> None:
        """运行详情页爬虫"""
        self.logger.info("开始爬取详情页")

        # 加载URL列表
        df = self.load_urls()
        if df.empty:
            self.logger.error("没有找到有效的URL列表")
            return

        total_urls = len(df)
        self.logger.info(f"共有 {total_urls} 个URL需要爬取")

        # 成功率计算
        success_threshold = 0.5
        success_count = 0
        total_attempts = 0

        # 动态延迟
        min_delay = config.CRAWL_DELAY
        max_delay = config.CRAWL_DELAY * 3
        current_delay = min_delay

        # 爬取详情页
        details = []
        batch_size = 10
        batch_count = 0

        failed_urls = []
        consecutive_failures = 0
        max_consecutive_failures = 5

        for i, (_, row) in enumerate(tqdm(df.iterrows(), total=len(df), desc="爬取详情页")):
            url = row["详情链接"]
            news_id = row["新闻ID"]

            actual_delay = random.uniform(current_delay, current_delay * 1.5)
            self.logger.debug(f"请求延迟: {actual_delay:.2f}秒")
            time.sleep(actual_delay)

            try:
                self.logger.info(f"爬取详情页 ({i+1}/{total_urls}): {url}")
                detail = self.crawl_detail(url, news_id)
                details.append(detail)

                total_attempts += 1
                if detail.get("content"):
                    success_count += 1
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    failed_urls.append((news_id, url))
                    self.logger.warning(f"获取详情页失败: {url}")

                # 计算成功率并调整延迟
                if total_attempts >= 5:
                    success_rate = success_count / total_attempts
                    self.logger.debug(f"当前成功率: {success_rate:.2f}")

                    if success_rate < success_threshold:
                        current_delay = min(current_delay * 1.5, max_delay)
                        self.logger.warning(f"成功率低于阈值，增加延迟至 {current_delay:.2f}秒")
                    elif success_rate > 0.8 and current_delay > min_delay:
                        current_delay = max(current_delay * 0.9, min_delay)

                # 检查连续失败
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error(f"连续 {consecutive_failures} 次爬取失败，等待30秒后继续")
                    time.sleep(30)
                    consecutive_failures = 0

                # 每批次保存一次
                if len(details) >= batch_size:
                    batch_count += 1
                    self.logger.info(f"保存第 {batch_count} 批详情数据，{len(details)} 条")
                    self.save_details_to_csv(details)
                    details = []
                    time.sleep(random.uniform(3, 8))

            except Exception as e:
                self.logger.error(f"爬取详情页失败: {url}, 错误: {e}")
                failed_urls.append((news_id, url))
                consecutive_failures += 1
                current_delay = min(current_delay * 1.5, max_delay)

                if consecutive_failures >= max_consecutive_failures:
                    wait_time = 60 + random.uniform(0, 30)
                    self.logger.error(f"连续 {consecutive_failures} 次爬取失败，等待 {wait_time:.2f}秒后继续")
                    time.sleep(wait_time)
                    consecutive_failures = 0

        # 保存剩余的详情
        if details:
            batch_count += 1
            self.logger.info(f"保存第 {batch_count} 批详情数据，{len(details)} 条")
            self.save_details_to_csv(details)

        # 记录失败的URL
        if failed_urls:
            self.logger.warning(f"有 {len(failed_urls)} 个URL爬取失败")
            failed_file = config.DATA_DIR / "爬取失败URLs.csv"
            pd.DataFrame(failed_urls, columns=["新闻ID", "详情链接"]).to_csv(
                failed_file, index=False, encoding="utf-8-sig"
            )
            self.logger.info(f"失败的URL已保存到: {failed_file}")

        # 统计爬取结果
        success_rate = success_count / total_attempts if total_attempts > 0 else 0
        self.logger.info(f"详情页爬取完成，成功率: {success_rate:.2f}")
        self.logger.info(f"共处理 {total_urls} 个URL，成功: {success_count}，失败: {total_urls - success_count}")


if __name__ == "__main__":
    # 设置日志
    logger = setup_logger()

    # 运行详情页爬虫
    crawler = DetailCrawler()
    crawler.run()
