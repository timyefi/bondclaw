#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
企业预警通地方化债数据爬虫入口脚本
集成数据爬取、详情页爬取和数据分析功能
"""

import os
import sys
import time
import random
import logging
import argparse
from pathlib import Path

from main import DebtDataCrawler
from detail_crawler import DetailCrawler
from analyzer import DebtDataAnalyzer
from debt_trend_analyzer import DebtTrendAnalyzer
from utils import setup_logger, load_cookie_from_file
import config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="企业预警通地方化债数据爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整运行（爬取列表 + 详情 + 分析）
  python run.py

  # 仅爬取列表数据
  python run.py --mode crawl

  # 仅爬取详情页
  python run.py --mode detail

  # 仅分析数据
  python run.py --mode analyze

  # 增量爬取
  python run.py --incremental

  # 使用自定义Cookie
  python run.py --cookie "your_cookie_here"

  # 慢速爬取模式（减少被反爬的可能性）
  python run.py --slow

环境变量配置:
  QYYJT_COOKIE          - Cookie认证信息
  QYYJT_USER_ID         - 用户ID
  QYYJT_CRAWL_DELAY     - 爬取延迟(秒)
  QYYJT_MAX_PAGES       - 最大爬取页数
  QYYJT_INCREMENTAL     - 是否增量爬取
  QYYJT_HEADLESS        - Playwright无头模式
        """
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["all", "crawl", "detail", "analyze", "trend"],
        default="all",
        help="运行模式: all(全部), crawl(仅爬取列表), detail(仅爬取详情), analyze(仅分析), trend(趋势分析)"
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help="是否增量爬取"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="每页数量"
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="最大爬取页数"
    )

    parser.add_argument(
        "--reset-skip",
        action="store_true",
        help="重置skipParam，从头开始爬取"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="请求间隔时间(秒)"
    )

    parser.add_argument(
        "--retry",
        type=int,
        default=None,
        help="最大重试次数"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="请求超时时间(秒)"
    )

    parser.add_argument(
        "--cookie",
        type=str,
        help="自定义Cookie"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    parser.add_argument(
        "--skip-param",
        type=str,
        help="自定义起始skipParam"
    )

    parser.add_argument(
        "--ua",
        type=str,
        help="自定义User-Agent"
    )

    parser.add_argument(
        "--slow",
        action="store_true",
        help="启用更慢的爬取速度"
    )

    return parser.parse_args()


def update_cookie_from_file() -> bool:
    """
    从cookie.txt文件更新Cookie

    Returns:
        bool: 是否成功加载
    """
    logger = logging.getLogger("债务预警爬虫")
    cookie = load_cookie_from_file()

    if cookie:
        config.DEFAULT_COOKIE = cookie
        return True
    return False


def main() -> int:
    """主函数"""
    args = parse_args()

    # 设置日志
    logger = setup_logger()

    # 设置调试模式
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.info("已启用调试模式，日志级别设置为DEBUG")

    logger.info("企业预警通地方化债数据爬虫启动")

    start_time = time.time()

    # 更新配置
    if args.incremental is not None:
        config.INCREMENTAL = args.incremental

    if args.output:
        config.OUTPUT_FILE = Path(args.output)

    if args.max_pages:
        config.MAX_PAGES = args.max_pages

    if args.delay:
        config.CRAWL_DELAY = args.delay
        config.REQUEST_DELAY = (args.delay, args.delay * 2)

    if args.retry:
        config.MAX_RETRIES = args.retry

    if args.timeout:
        config.TIMEOUT = args.timeout

    # Cookie处理
    if args.cookie:
        config.DEFAULT_COOKIE = args.cookie
        logger.info(f"使用自定义Cookie: {args.cookie[:30]}...")
    else:
        update_cookie_from_file()

    # 自定义User-Agent
    if args.ua:
        logger.info(f"使用自定义User-Agent: {args.ua}")
        config.USER_AGENT = args.ua

    # 慢速模式
    if args.slow:
        logger.info("启用慢速爬取模式，增加请求间隔")
        config.CRAWL_DELAY = max(config.CRAWL_DELAY * 2, 10)
        logger.info(f"请求间隔已设置为: {config.CRAWL_DELAY} 秒")

    # 重置skipParam
    if args.reset_skip and config.LAST_SKIP_PARAM_FILE.exists():
        logger.info("重置skipParam，从头开始爬取")
        config.LAST_SKIP_PARAM_FILE.unlink()

    # 自定义skipParam
    start_skip_param = ""
    if args.skip_param:
        logger.info(f"使用自定义skipParam: {args.skip_param}")
        start_skip_param = args.skip_param

    # 随机等待
    time.sleep(random.uniform(1, 3))

    try:
        # 爬取列表数据
        if args.mode in ["all", "crawl"]:
            logger.info("=== 开始爬取列表数据 ===")
            crawler = DebtDataCrawler()
            if start_skip_param:
                crawler.crawl_all_data(start_skip_param=start_skip_param)
            else:
                crawler.run()

        # 爬取详情页
        if args.mode in ["all", "detail"] and config.OUTPUT_FILE.exists():
            logger.info("=== 开始爬取详情页数据 ===")
            logger.info(f"使用详情页API: {config.DETAIL_API_URL}")
            time.sleep(random.uniform(3, 5))
            detail_crawler = DetailCrawler()
            detail_crawler.run()
            logger.info("详情页数据已保存到 data/详情数据.csv")

        # 分析数据
        if args.mode in ["all", "analyze"] and config.OUTPUT_FILE.exists():
            logger.info("=== 开始分析数据 ===")
            analyzer = DebtDataAnalyzer()
            analyzer.run()

        # 趋势分析
        if args.mode in ["all", "trend"] and config.OUTPUT_FILE.exists():
            logger.info("=== 开始债务化解趋势分析 ===")
            trend_analyzer = DebtTrendAnalyzer()
            trend_analyzer.run()

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"任务完成，总耗时 {duration:.2f} 秒")

    except KeyboardInterrupt:
        logger.info("用户中断，程序停止")
        return 0
    except Exception as e:
        logger.exception(f"运行过程中发生错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
