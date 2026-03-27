# -*- coding: utf-8 -*-
"""
小波分析模块
"""
import numpy as np
import pywt
import scipy.stats as stats
from typing import Tuple


class WaveletAnalyzer:
    """小波分析类"""

    def __init__(self, wavelet: str = 'db2'):
        self.wavelet = wavelet

    def decompose(self, data: np.ndarray, level: int = None) -> list:
        """小波分解"""
        if level is None:
            level = pywt.dwt_max_level(len(data), pywt.Wavelet(self.wavelet).dec_len)
        return pywt.wavedec(data, self.wavelet, level=level)

    def reconstruct(self, coeffs: list, keep_levels: int) -> np.ndarray:
        """部分重构"""
        new_coeffs = coeffs[:keep_levels + 1] + [np.zeros_like(c) for c in coeffs[keep_levels + 1:]]
        return pywt.waverec(new_coeffs, self.wavelet)

    def get_cycle_value(self, data: np.ndarray, period_cycle: int, period_trend: int,
                        level: int) -> Tuple[float, int]:
        """计算周期分位点和趋势"""
        coeffs = self.decompose(data)
        level = int(level)
        period_cycle = int(period_cycle)
        period_trend = int(period_trend)

        recon = self.reconstruct(coeffs, level)

        # 计算最近周期
        if len(recon) < abs(period_cycle):
            recent_cycle = recon
        else:
            recent_cycle = recon[-period_cycle:]

        latest_value = recon[-1]
        percentile = stats.percentileofscore(recent_cycle, latest_value)

        # 计算趋势
        if len(recon) < abs(period_trend):
            trend_value = recon[-len(recon) + 1] if len(recon) > 1 else recon[-1]
        else:
            trend_value = recon[-period_trend]

        trend_diff = latest_value - trend_value
        trend = 1 if trend_diff > 0 else (-1 if trend_diff < 0 else 0)

        return percentile, trend

    def create_animation_data(self, data: np.ndarray) -> list:
        """创建动画数据用于可视化"""
        coeffs = self.decompose(data)
        frames = []

        for i in range(len(coeffs)):
            recon = self.reconstruct(coeffs, i)[:len(data)]
            length = len(recon)
            cycle = length / (2 ** i)
            trend = cycle / 4

            frames.append({
                'level': i,
                'reconstruction': recon,
                'cycle_days': cycle,
                'trend_days': trend
            })

        return frames
