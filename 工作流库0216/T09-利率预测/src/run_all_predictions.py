#!/usr/bin/env python3
"""
利率预测模型统一运行脚本
每周一到周五晚上12点自动运行所有子模型
"""

import subprocess
import sys
import os
from datetime import datetime

def run_script(script_path, description):
    """运行单个脚本并记录结果"""
    print(f"[{datetime.now()}] 开始执行: {description}")
    print(f"脚本路径: {script_path}")
    
    try:
        # 检查脚本文件是否存在
        if not os.path.exists(script_path):
            print(f"错误: 脚本文件不存在: {script_path}")
            return False
        
        # 运行脚本
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            print(f"成功: {description}")
            if result.stdout:
                print("输出:", result.stdout)
        else:
            print(f"失败: {description}")
            print("错误信息:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"超时: {description} - 执行时间超过30分钟")
        return False
    except Exception as e:
        print(f"异常: {description} - {str(e)}")
        return False
    
    print("-" * 50)
    return True

def main():
    """主函数：按顺序运行所有预测模型"""
    print("=" * 60)
    print(f"[{datetime.now()}] 开始执行利率预测模型任务")
    print("=" * 60)
    
    # 定义所有要运行的脚本
    scripts = [
        {
            "path": "/data/项目/快速处理/2025/利率预测/子模型4-基于银行负债成本-中期/run_prediction.py",
            "description": "子模型4-基于银行负债成本-中期"
        },
        {
            "path": "/data/项目/快速处理/2025/利率预测/子模型3-基于资金供需 - 中长期/predict_yield_with_demand_supply.py",
            "description": "子模型3-基于资金供需-中长期"
        },
        {
            "path": "/data/项目/快速处理/2025/利率预测/子模型2-基于交易拥挤度-超短期/predict_yield_with_congestion.py",
            "description": "子模型2-基于交易拥挤度-超短期"
        },
        {
            "path": "/data/项目/快速处理/2025/利率预测/子模型1-基于行情集中度-短期/predict_yield_with_concentration.py",
            "description": "子模型1-基于行情集中度-短期"
        }
    ]
    
    success_count = 0
    total_count = len(scripts)
    
    # 按顺序运行所有脚本
    for script in scripts:
        if run_script(script["path"], script["description"]):
            success_count += 1
    
    # 输出总结
    print("=" * 60)
    print(f"[{datetime.now()}] 任务执行完成")
    print(f"成功: {success_count}/{total_count}")
    print("=" * 60)
    
    # 如果有失败的脚本，返回非零状态码
    if success_count < total_count:
        sys.exit(1)

if __name__ == "__main__":
    main()