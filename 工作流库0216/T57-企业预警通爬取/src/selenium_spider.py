# -*- coding: utf-8 -*-
"""
企业预警通Selenium爬虫模块
"""
import time
import random
import logging
import pandas as pd
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QYYJT_BASE_URL, QYYJT_USERNAME, QYYJT_PASSWORD, SPIDER_CONFIG


class QYYJTSeleniumSpider:
    """企业预警通Selenium爬虫类"""

    def __init__(self, username: str = None, password: str = None):
        self.base_url = QYYJT_BASE_URL
        self.username = username or QYYJT_USERNAME
        self.password = password or QYYJT_PASSWORD
        self.driver = None
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

    def _init_driver(self) -> None:
        """初始化浏览器驱动"""
        options = webdriver.EdgeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')

        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        options.add_argument(f'user-agent={user_agent}')

        self.driver = webdriver.Edge(options=options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

    def _random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """随机延时"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _wait_for_element(self, by: By, value: str, timeout: int = 10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"等待元素超时: {value}")
            return None

    def _simulate_human_input(self, element, text: str) -> None:
        """模拟人类输入"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

    def login(self) -> bool:
        """登录"""
        try:
            if not self.driver:
                self._init_driver()

            self.driver.get(f"{self.base_url}/login")
            self._random_sleep()

            # 输入用户名
            username_input = self._wait_for_element(By.CSS_SELECTOR, "input[placeholder='请输入手机号']")
            if not username_input:
                return False
            self._simulate_human_input(username_input, self.username)
            self._random_sleep()

            # 输入密码
            password_input = self._wait_for_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']")
            if not password_input:
                return False
            self._simulate_human_input(password_input, self.password)
            self._random_sleep()

            # 点击登录按钮
            login_button = self._wait_for_element(By.CSS_SELECTOR, "button.login-btn")
            if not login_button:
                return False
            login_button.click()

            self._random_sleep(3, 5)

            # 检查是否登录成功
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".user-info")
                self.logger.info("登录成功")
                return True
            except NoSuchElementException:
                self.logger.error("登录失败")
                return False

        except Exception as e:
            self.logger.error(f"登录异常: {str(e)}")
            return False

    def get_market_table(self) -> Optional[pd.DataFrame]:
        """获取市场化经营主体表格数据"""
        try:
            self.driver.get(f"{self.base_url}/bond/newExitTopic/mark")
            self._random_sleep(3, 5)

            table = self._wait_for_element(By.CSS_SELECTOR, ".el-table")
            if not table:
                return None

            # 获取表头
            headers = []
            header_cells = table.find_elements(By.CSS_SELECTOR, "th .cell")
            for cell in header_cells:
                headers.append(cell.text.strip())

            # 获取表格数据
            rows = []
            data_rows = table.find_elements(By.CSS_SELECTOR, ".el-table__row")
            for row in data_rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td .cell")
                row_data = [cell.text.strip() for cell in cells]
                rows.append(row_data)

            df = pd.DataFrame(rows, columns=headers)
            return df

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

    def close(self) -> None:
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
