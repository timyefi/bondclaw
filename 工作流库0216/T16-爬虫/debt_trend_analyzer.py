#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
地方债务化解趋势分析模块 - 企业预警通地方化债数据爬虫
分析地方政府债务化解的方式、趋势和效果
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import jieba.analyse
from collections import Counter

import config
from utils import setup_logger


class DebtTrendAnalyzer:
    """地方债务化解趋势分析类"""

    def __init__(self, data_file: Path = None):
        """
        初始化趋势分析器

        Args:
            data_file: 数据文件路径
        """
        self.logger = setup_logger()

        # 输出目录
        self.output_dir = config.DATA_DIR / "分析结果"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置matplotlib支持中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 加载数据
        if data_file and data_file.exists():
            self.data = pd.read_csv(data_file, encoding="utf-8-sig")
            self.logger.info(f"从文件加载了 {len(self.data)} 条数据: {data_file}")
        else:
            self.data = pd.DataFrame()
            self.logger.warning("没有找到数据文件")

    def preprocess_data(self) -> pd.DataFrame:
        """
        预处理数据，添加时间字段、提取债务相关信息等

        Returns:
            pd.DataFrame: 预处理后的数据
        """
        if self.data.empty:
            self.logger.warning("没有数据可供预处理")
            return pd.DataFrame()

        df = self.data.copy()

        # 处理日期字段
        df["日期"] = pd.to_datetime(df["发布日期"], errors="coerce")
        df["年月"] = df["日期"].dt.strftime("%Y-%m")

        # 提取省份
        def extract_province(area_str):
            if not isinstance(area_str, str) or not area_str:
                return "未知"
            return area_str.split("-")[0]

        if "地区分类" in df.columns:
            df["省份"] = df["地区分类"].apply(extract_province)
        else:
            df["省份"] = "未知"

        # 合并标题和摘要
        df["全文"] = df["标题"].fillna("") + " " + df["摘要"].fillna("")

        # 识别债务化解相关的新闻
        debt_patterns = [
            r"化解.*债务",
            r"债务.*化解",
            r"隐性债务",
            r"专项债.*置换",
            r"债务.*清零",
            r"债务.*风险",
            r"([绿黄橙红]色.*风险)|(风险.*[绿黄橙红]色)",
            r"融资平台",
            r"降息减债"
        ]

        df["债务相关"] = df["全文"].apply(
            lambda x: any(re.search(pattern, str(x)) is not None for pattern in debt_patterns)
        )

        # 识别债务化解方式
        methods = {
            "置换债券": [r"置换债券", r"专项债券.*置换", r"债券.*置换"],
            "盘活资产": [r"盘活.*资产", r"资产.*盘活", r"资产变现"],
            "降低利息": [r"降息", r"降低.*利率", r"利率.*降低", r"利息.*降低"],
            "市场化经营": [r"市场化经营", r"市场化转型", r"经营性收入"],
            "政府财政支持": [r"财政.*支持", r"支持.*财政", r"财政.*投入"],
            "债务重组": [r"债务重组", r"重组.*债务", r"债务.*重组"]
        }

        for method, patterns in methods.items():
            df[method] = df["全文"].apply(
                lambda x: any(re.search(pattern, str(x)) is not None for pattern in patterns)
            )

        # 提取债务规模和化解金额
        def extract_amount(text):
            if not isinstance(text, str):
                return np.nan

            patterns = [
                r"化解.*?(\d+\.?\d*)亿元",
                r"化解.*?(\d+\.?\d*)万元",
                r"债务.*?(\d+\.?\d*)亿元",
                r"债务.*?(\d+\.?\d*)万元"
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    amount = float(match.group(1))
                    if "万元" in match.group(0):
                        amount = amount / 10000
                    return amount

            return np.nan

        df["化解金额(亿)"] = df["全文"].apply(extract_amount)

        # 提取风险等级变化
        def extract_risk_level(text):
            if not isinstance(text, str):
                return "未提及"

            risk_patterns = {
                "由红转黄": [r"由红转[黄黄色]", r"红色.*降.*黄色"],
                "由橙降黄": [r"由橙降[黄黄色]", r"橙色.*降.*黄色"],
                "由黄转绿": [r"由[黄黄色]转[绿绿色]", r"黄色.*[转变].*绿色"],
                "绿色": [r"[保持在]*绿色[^区域]*区域", r"[保持在]*绿色[^等级]*等级"]
            }

            for level, patterns in risk_patterns.items():
                if any(re.search(pattern, text) for pattern in patterns):
                    return level

            return "未提及"

        df["风险等级变化"] = df["全文"].apply(extract_risk_level)

        return df

    def analyze_time_trend(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        分析时间趋势

        Args:
            df: 数据框，默认使用预处理后的数据

        Returns:
            pd.DataFrame: 时间趋势数据
        """
        if df is None:
            df = self.preprocess_data()

        if df.empty:
            return pd.DataFrame()

        # 按年月分组统计
        monthly_stats = df.groupby("年月").agg({
            "新闻ID": "count",
            "债务相关": "sum",
            "化解金额(亿)": ["sum", "mean"],
            "风险等级变化": lambda x: (x != "未提及").sum()
        }).reset_index()

        monthly_stats.columns = ["年月", "新闻数量", "债务相关数量", "月度化解总金额(亿)", "月度化解平均金额(亿)", "风险等级变化提及数"]
        monthly_stats = monthly_stats.sort_values("年月")

        return monthly_stats

    def analyze_methods(self, df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分析债务化解方式

        Args:
            df: 数据框，默认使用预处理后的数据

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: 化解方式统计和省份化解方式统计
        """
        if df is None:
            df = self.preprocess_data()

        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # 债务化解方式列表
        methods = ["置换债券", "盘活资产", "降低利息", "市场化经营", "政府财政支持", "债务重组"]

        # 统计每种方式的使用频次
        method_counts = {method: df[method].sum() for method in methods if method in df.columns}

        # 按省份统计
        province_methods = df.groupby("省份").agg({
            method: "sum" for method in methods if method in df.columns
        }).reset_index()

        # 总体统计
        method_stats = pd.DataFrame({
            "化解方式": list(method_counts.keys()),
            "使用频次": list(method_counts.values())
        }).sort_values("使用频次", ascending=False)

        return method_stats, province_methods

    def analyze_risk_level(self, df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分析风险等级变化

        Args:
            df: 数据框，默认使用预处理后的数据

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: 风险等级变化统计和省份风险变化统计
        """
        if df is None:
            df = self.preprocess_data()

        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # 统计风险等级变化
        risk_counts = df["风险等级变化"].value_counts().reset_index()
        risk_counts.columns = ["风险等级变化", "数量"]

        # 移除"未提及"类别
        risk_counts = risk_counts[risk_counts["风险等级变化"] != "未提及"]

        # 按省份统计
        province_risk = df[df["风险等级变化"] != "未提及"].groupby(["省份", "风险等级变化"]).size().reset_index()
        province_risk.columns = ["省份", "风险等级变化", "数量"]

        return risk_counts, province_risk

    def plot_time_trend(self) -> str:
        """
        绘制时间趋势图

        Returns:
            str: 图表文件路径
        """
        df = self.preprocess_data()
        if df.empty:
            return ""

        monthly_stats = self.analyze_time_trend(df)

        # 创建图形
        fig, ax1 = plt.subplots(figsize=(14, 8))
        ax2 = ax1.twinx()

        # 绘制新闻数量趋势
        ax1.plot(monthly_stats["年月"], monthly_stats["新闻数量"], 'b-', marker='o', label="新闻总数")
        ax1.plot(monthly_stats["年月"], monthly_stats["债务相关数量"], 'g-', marker='s', label="债务相关新闻")
        ax1.set_xlabel("年月")
        ax1.set_ylabel("新闻数量", color='b')
        ax1.tick_params(axis='y', labelcolor='b')

        # 绘制化解金额趋势
        ax2.plot(monthly_stats["年月"], monthly_stats["月度化解总金额(亿)"], 'r-', marker='^', label="月度化解总金额(亿)")
        ax2.set_ylabel("化解金额(亿元)", color='r')
        ax2.tick_params(axis='y', labelcolor='r')

        plt.xticks(rotation=45, ha="right")

        # 添加图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        plt.title("地方债务相关新闻与化解金额月度趋势")
        plt.tight_layout()

        # 保存图表
        output_file = self.output_dir / "债务化解趋势.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def plot_methods(self) -> str:
        """
        绘制债务化解方式图表

        Returns:
            str: 图表文件路径
        """
        df = self.preprocess_data()
        if df.empty:
            return ""

        method_stats, _ = self.analyze_methods(df)

        plt.figure(figsize=(12, 8))

        # 绘制柱状图
        bars = plt.bar(method_stats["化解方式"], method_stats["使用频次"], color="skyblue")

        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{int(height)}", ha="center", va="bottom")

        plt.title("地方债务化解方式统计")
        plt.xlabel("化解方式")
        plt.ylabel("提及频次")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()

        # 保存图表
        output_file = self.output_dir / "债务化解方式.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def plot_risk_level(self) -> str:
        """
        绘制风险等级变化图表

        Returns:
            str: 图表文件路径
        """
        df = self.preprocess_data()
        if df.empty:
            return ""

        risk_counts, _ = self.analyze_risk_level(df)

        if risk_counts.empty:
            self.logger.warning("没有风险等级变化数据可供绘制")
            return ""

        plt.figure(figsize=(10, 8))

        # 设置颜色映射
        colors = {
            "由红转黄": "orange",
            "由橙降黄": "gold",
            "由黄转绿": "lightgreen",
            "绿色": "green"
        }

        bar_colors = [colors.get(level, "gray") for level in risk_counts["风险等级变化"]]

        # 绘制柱状图
        bars = plt.bar(risk_counts["风险等级变化"], risk_counts["数量"], color=bar_colors)

        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{int(height)}", ha="center", va="bottom")

        plt.title("地方债务风险等级变化统计")
        plt.xlabel("风险等级变化")
        plt.ylabel("数量")
        plt.xticks(rotation=0)
        plt.tight_layout()

        # 保存图表
        output_file = self.output_dir / "风险等级变化.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def plot_province_map(self) -> str:
        """
        绘制省份债务化解统计图

        Returns:
            str: 图表文件路径
        """
        df = self.preprocess_data()
        if df.empty:
            return ""

        # 按省份统计
        province_stats = df.groupby("省份").agg({
            "债务相关": "sum",
            "化解金额(亿)": ["sum", "count"]
        }).reset_index()

        province_stats.columns = ["省份", "债务相关数量", "化解总金额(亿)", "提及金额的新闻数"]
        province_stats = province_stats.sort_values("债务相关数量", ascending=False).head(15)

        fig, ax1 = plt.subplots(figsize=(14, 8))
        ax2 = ax1.twinx()

        x = np.arange(len(province_stats))
        width = 0.35

        bars1 = ax1.bar(x - width/2, province_stats["债务相关数量"], width, label="债务相关新闻", color="steelblue")
        ax1.set_xlabel("省份")
        ax1.set_ylabel("新闻数量", color="steelblue")
        ax1.tick_params(axis="y", labelcolor="steelblue")

        bars2 = ax2.bar(x + width/2, province_stats["化解总金额(亿)"], width, label="化解总金额(亿)", color="coral")
        ax2.set_ylabel("化解金额(亿元)", color="coral")
        ax2.tick_params(axis="y", labelcolor="coral")

        ax1.set_xticks(x)
        ax1.set_xticklabels(province_stats["省份"], rotation=45, ha="right")

        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")

        plt.title("各省份债务相关新闻与化解金额统计")
        plt.tight_layout()

        # 保存图表
        output_file = self.output_dir / "省份债务化解情况.png"
        plt.savefig(output_file, dpi=300)
        plt.close()

        return str(output_file)

    def generate_trend_report(self) -> str:
        """
        生成债务化解趋势分析报告

        Returns:
            str: 报告文件路径
        """
        df = self.preprocess_data()
        if df.empty:
            self.logger.warning("没有数据可供生成报告")
            return ""

        # 绘制图表
        self.plot_time_trend()
        self.plot_methods()
        self.plot_risk_level()
        self.plot_province_map()

        # 获取分析数据
        monthly_stats = self.analyze_time_trend(df)
        method_stats, _ = self.analyze_methods(df)
        risk_counts, _ = self.analyze_risk_level(df)

        # 债务清零地区
        debt_zero_news = df[df["全文"].str.contains(r'债务.*清零|隐[性债]债务.*清零', na=False)]
        debt_zero_provinces = debt_zero_news["省份"].unique()

        # 构建报告内容
        report_content = f"""# 地方债务化解趋势分析报告

## 1. 总体情况

- 总新闻数量: {len(df)}
- 债务相关新闻: {df["债务相关"].sum()}条 ({df["债务相关"].sum()/len(df)*100:.1f}%)
- 提及债务清零的地区: {len(debt_zero_provinces)}个
- 提及化解金额的新闻: {df["化解金额(亿)"].notna().sum()}条
- 总化解金额: {df["化解金额(亿)"].sum():.2f}亿元
- 平均化解金额: {df["化解金额(亿)"].mean():.2f}亿元

## 2. 时间趋势分析

### 月度趋势:
"""

        # 添加月度趋势数据
        for _, row in monthly_stats.iterrows():
            report_content += f"- {row['年月']}: 新闻{row['新闻数量']}条，债务相关{row['债务相关数量']}条，化解金额{row['月度化解总金额(亿)']:.2f}亿元\n"

        # 添加债务化解方式分析
        report_content += "\n## 3. 债务化解方式分析\n\n"
        for _, row in method_stats.iterrows():
            report_content += f"- {row['化解方式']}: {row['使用频次']}次提及\n"

        # 添加风险等级变化分析
        report_content += "\n## 4. 风险等级变化分析\n\n"
        for _, row in risk_counts.iterrows():
            report_content += f"- {row['风险等级变化']}: {row['数量']}次提及\n"

        # 添加省份分析
        report_content += "\n## 5. 区域债务化解情况\n\n"

        # 按债务相关新闻数量排序的省份
        top_provinces = df.groupby("省份")["债务相关"].sum().sort_values(ascending=False).head(10)

        report_content += "### 债务相关新闻数量前10省份:\n"
        for province, count in top_provinces.items():
            report_content += f"- {province}: {count}条\n"

        # 保存报告
        report_file = self.output_dir / "地方债务化解趋势分析报告.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        self.logger.info(f"债务化解趋势分析报告已生成: {report_file}")
        return str(report_file)

    def run(self) -> None:
        """运行债务趋势分析"""
        self.logger.info("开始分析地方债务化解趋势")

        # 预处理数据
        df = self.preprocess_data()
        if df.empty:
            self.logger.error("没有有效数据可供分析")
            return

        # 生成趋势报告
        self.generate_trend_report()

        self.logger.info("债务趋势分析完成")


if __name__ == "__main__":
    analyzer = DebtTrendAnalyzer()
    analyzer.run()
