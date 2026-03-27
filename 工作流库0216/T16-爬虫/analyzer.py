#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据分析模块 - 企业预警通地方化债数据爬虫
用于统计和分析爬取的地方化债数据
"""

import os
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import jieba.analyse

import config
from utils import setup_logger


class DebtDataAnalyzer:
    """地方化债数据分析类"""

    def __init__(self, data_file: Path = None):
        """
        初始化数据分析器

        Args:
            data_file: 数据文件路径
        """
        self.logger = logging.getLogger("债务预警爬虫")

        if data_file is None:
            data_file = config.OUTPUT_FILE
        self.data_file = data_file

        # 输出目录
        self.output_dir = config.DATA_DIR / "分析结果"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载数据
        self.data = self.load_data()

        # 设置matplotlib支持中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

    def load_data(self) -> pd.DataFrame:
        """
        加载数据

        Returns:
            pd.DataFrame: 加载的数据
        """
        if not self.data_file.exists():
            self.logger.error(f"数据文件不存在: {self.data_file}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(self.data_file, encoding="utf-8-sig")
            if df.empty:
                self.logger.error("数据文件为空")
            else:
                self.logger.info(f"成功加载 {len(df)} 条数据")
            return df
        except Exception as e:
            self.logger.error(f"加载数据文件失败: {e}")
            return pd.DataFrame()

    def basic_stats(self) -> Dict[str, Any]:
        """
        基本统计信息

        Returns:
            Dict[str, Any]: 基本统计信息
        """
        if self.data.empty:
            return {}

        stats = {
            "总数": len(self.data),
            "日期范围": (self.data["发布日期"].min(), self.data["发布日期"].max()),
            "来源分布": self.data["来源"].value_counts().to_dict() if "来源" in self.data.columns else {},
            "标签分布": self.data["标签"].value_counts().to_dict() if "标签" in self.data.columns else {},
            "阅读量统计": {
                "最大": self.data["阅读量"].max() if "阅读量" in self.data.columns else 0,
                "最小": self.data["阅读量"].min() if "阅读量" in self.data.columns else 0,
                "平均": self.data["阅读量"].mean() if "阅读量" in self.data.columns else 0,
                "中位数": self.data["阅读量"].median() if "阅读量" in self.data.columns else 0
            }
        }

        return stats

    def analyze_by_region(self) -> pd.DataFrame:
        """
        按地区分析

        Returns:
            pd.DataFrame: 按地区分组的统计结果
        """
        if self.data.empty or "地区分类" not in self.data.columns:
            return pd.DataFrame()

        # 提取省份信息
        def extract_province(area_str):
            if not isinstance(area_str, str):
                return "未知"
            parts = area_str.split("-")
            return parts[0] if parts else "未知"

        self.data["省份"] = self.data["地区分类"].apply(extract_province)

        # 按省份分组统计
        region_stats = self.data.groupby("省份").agg({
            "新闻ID": "count",
            "阅读量": ["mean", "sum"]
        }).reset_index()

        region_stats.columns = ["省份", "新闻数量", "平均阅读量", "总阅读量"]
        region_stats = region_stats.sort_values("新闻数量", ascending=False)

        return region_stats

    def analyze_by_time(self) -> pd.DataFrame:
        """
        按时间分析

        Returns:
            pd.DataFrame: 按时间分组的统计结果
        """
        if self.data.empty or "发布日期" not in self.data.columns:
            return pd.DataFrame()

        # 提取日期部分
        self.data["日期"] = self.data["发布日期"].str.split(" ").str[0]

        # 按日期分组统计
        time_stats = self.data.groupby("日期").agg({
            "新闻ID": "count",
            "阅读量": ["mean", "sum"]
        }).reset_index()

        time_stats.columns = ["日期", "新闻数量", "平均阅读量", "总阅读量"]
        time_stats = time_stats.sort_values("日期")

        return time_stats

    def keyword_extraction(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        关键词提取

        Args:
            top_n: 提取的关键词数量

        Returns:
            List[Tuple[str, float]]: 关键词及其权重
        """
        if self.data.empty:
            return []

        # 合并标题和摘要文本
        texts = self.data["标题"].fillna("") + " " + self.data["摘要"].fillna("")
        text = " ".join(texts)

        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)

        return keywords

    def plot_region_stats(self, top_n: int = 10) -> str:
        """
        绘制地区统计图

        Args:
            top_n: 显示的地区数量

        Returns:
            str: 保存的文件路径
        """
        region_stats = self.analyze_by_region()
        if region_stats.empty:
            return ""

        # 取前N个地区
        top_regions = region_stats.head(top_n)

        # 创建图形
        plt.figure(figsize=(12, 8))
        plt.bar(top_regions["省份"], top_regions["新闻数量"], color="steelblue")
        plt.title("各省份地方化债相关新闻数量")
        plt.xlabel("省份")
        plt.ylabel("新闻数量")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # 保存图形
        output_file = self.output_dir / "地区分布.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def plot_time_trend(self) -> str:
        """
        绘制时间趋势图

        Returns:
            str: 保存的文件路径
        """
        time_stats = self.analyze_by_time()
        if time_stats.empty:
            return ""

        # 创建图形
        plt.figure(figsize=(14, 8))
        plt.plot(time_stats["日期"], time_stats["新闻数量"], marker="o", linestyle="-", color="teal")
        plt.title("地方化债相关新闻发布时间趋势")
        plt.xlabel("日期")
        plt.ylabel("新闻数量")
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()

        # 保存图形
        output_file = self.output_dir / "时间趋势.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def plot_keywords(self, top_n: int = 20) -> str:
        """
        绘制关键词图

        Args:
            top_n: 显示的关键词数量

        Returns:
            str: 保存的文件路径
        """
        keywords = self.keyword_extraction(top_n)
        if not keywords:
            return ""

        # 创建图形
        plt.figure(figsize=(12, 8))
        plt.bar([k for k, v in keywords], [v for k, v in keywords], color="coral")
        plt.title("地方化债相关新闻关键词")
        plt.xlabel("关键词")
        plt.ylabel("权重")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # 保存图形
        output_file = self.output_dir / "关键词.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def generate_report(self) -> str:
        """
        生成分析报告

        Returns:
            str: 报告文件路径
        """
        if self.data.empty:
            self.logger.error("没有数据，无法生成报告")
            return ""

        # 基本统计
        stats = self.basic_stats()

        # 生成报告
        report = [
            "# 地方化债数据分析报告\n",
            f"## 1. 基本统计\n",
            f"- 总数据量: {stats.get('总数', 0)}条\n",
            f"- 日期范围: {stats.get('日期范围', ('', ''))[0]} 至 {stats.get('日期范围', ('', ''))[1]}\n",
            f"- 最大阅读量: {stats.get('阅读量统计', {}).get('最大', 0)}\n",
            f"- 平均阅读量: {stats.get('阅读量统计', {}).get('平均', 0):.2f}\n",
            f"- 中位数阅读量: {stats.get('阅读量统计', {}).get('中位数', 0)}\n\n",
            f"## 2. 来源分布\n",
        ]

        # 来源分布
        source_dist = stats.get('来源分布', {})
        if source_dist:
            report.extend([f"- {source}: {count}条\n" for source, count in list(source_dist.items())[:10]])
        report.append("\n")

        # 地区分析
        report.append(f"## 3. 地区分析\n")
        region_stats = self.analyze_by_region()
        if not region_stats.empty:
            report.append("| 省份 | 新闻数量 | 平均阅读量 | 总阅读量 |\n")
            report.append("| ---- | -------- | ---------- | -------- |\n")
            for _, row in region_stats.head(15).iterrows():
                report.append(f"| {row['省份']} | {row['新闻数量']} | {row['平均阅读量']:.2f} | {row['总阅读量']} |\n")
            report.append("\n")

        # 关键词分析
        keywords = self.keyword_extraction(30)
        if keywords:
            report.append(f"## 4. 关键词分析\n")
            report.append("| 关键词 | 权重 |\n")
            report.append("| ------ | ---- |\n")
            for word, weight in keywords:
                report.append(f"| {word} | {weight:.4f} |\n")
            report.append("\n")

        # 保存报告
        report_file = self.output_dir / "分析报告.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.writelines(report)

        self.logger.info(f"分析报告已生成: {report_file}")
        return str(report_file)

    def run(self) -> None:
        """运行分析器"""
        self.logger.info("开始分析地方化债数据")

        if self.data.empty:
            self.logger.error("没有数据可供分析")
            return

        # 生成图表
        self.logger.info("生成地区分布图...")
        self.plot_region_stats()

        self.logger.info("生成时间趋势图...")
        self.plot_time_trend()

        self.logger.info("生成关键词图...")
        self.plot_keywords()

        # 生成报告
        self.logger.info("生成分析报告...")
        self.generate_report()

        self.logger.info("数据分析完成")


if __name__ == "__main__":
    # 设置日志
    logger = setup_logger()

    # 运行分析器
    analyzer = DebtDataAnalyzer()
    analyzer.run()
