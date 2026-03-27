# -*- coding: utf-8 -*-
"""
Excel读取模块
"""
import pandas as pd
import os
from typing import Optional, List


class ExcelReader:
    """Excel文件读取类"""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir

    def list_excel_files(self) -> List[str]:
        """列出data目录下的所有Excel文件"""
        files = []
        for f in os.listdir(self.data_dir):
            if f.endswith(('.xlsx', '.xls')):
                files.append(os.path.join(self.data_dir, f))
        return files

    def read_excel(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """读取Excel文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)

        return df

    def read_all_sheets(self, file_path: str) -> dict:
        """读取Excel文件的所有sheet"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        return pd.read_excel(file_path, sheet_name=None)

    def get_column_info(self, df: pd.DataFrame) -> dict:
        """获取DataFrame列信息"""
        info = {
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'shape': df.shape,
            'null_counts': df.isnull().sum().to_dict()
        }
        return info

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """清理列名（去除空格、特殊字符等）"""
        df = df.copy()
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(' ', '_')
        return df
