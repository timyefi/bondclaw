import cv2
import numpy as np
from datetime import datetime, timedelta
import requests
from dateutil.relativedelta import relativedelta
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy
import json
import os

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine.connect()  # 写入数据库

def select_data_region(img):
    """交互式选择数据区域"""
    window_name = '选择数据区域 - 按Enter确认，按c重选'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # 允许调整窗口大小
    # 调整窗口大小以适应屏幕
    screen_height = 800  # 设置合适的高度
    screen_width = int(img.shape[1] * screen_height / img.shape[0])  # 保持宽高比
    cv2.resizeWindow(window_name, min(screen_width, 1200), screen_height)  # 限制最大宽度
    
    while True:
        img_copy = img.copy()
        roi = cv2.selectROI(window_name, img_copy, False, False)
        
        x, y, w, h = roi
        cv2.rectangle(img_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imshow(window_name, img_copy)
        
        key = cv2.waitKey(0) & 0xFF
        if key == 13:  # Enter键
            cv2.destroyWindow(window_name)
            return roi
        elif key == ord('c'):  # c键重选
            continue
        else:
            cv2.destroyWindow(window_name)
            return roi

def get_axis_range():
    """获取坐标轴范围"""
    print("\n请输入Y轴范围（数值）：")
    y_min = float(input("Y轴最小值: "))
    y_max = float(input("Y轴最大值: "))
    
    print("\n请输入X轴范围（日期，支持格式：YYYY/MM 或 YYYY-MM-DD）：")
    x_min = input("X轴起始日期: ")
    x_max = input("X轴结束日期: ")
    
    # 转换日期字符串为datetime对象，支持多种格式
    def parse_date(date_str):
        # 尝试不同的日期格式
        formats = ['%Y/%m', '%Y-%m-%d', '%Y/%m/%d', '%Y-%m']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # 如果所有格式都失败，抛出异常
        raise ValueError(f"无法解析日期格式: {date_str}")
    
    start_date = parse_date(x_min)
    end_date = parse_date(x_max)
    
    return (y_min, y_max), (start_date, end_date)

def select_sample_point(img, cache_file="sample_points_cache.json"):
    """交互式选择曲线的样本点，支持多点选择，按Enter结束选择"""
    window_name = '选择曲线样本点 - 左键选择点，ESC清除所有点，Enter确认完成'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # 允许调整窗口大小
    # 调整窗口大小以适应屏幕
    screen_height = 800  # 设置合适的高度
    screen_width = int(img.shape[1] * screen_height / img.shape[0])  # 保持宽高比
    cv2.resizeWindow(window_name, min(screen_width, 1200), screen_height)  # 限制最大宽度
    
    # 检查是否存在缓存文件
    if os.path.exists(cache_file):
        response = input("检测到已保存的样本点缓存，是否使用？(y/n): ")
        if response.lower() == 'y':
            try:
                with open(cache_file, 'r') as f:
                    cached_points = json.load(f)
                print(f"已加载 {len(cached_points)} 个缓存点")
                return [(p[0], p[1]) for p in cached_points]
            except Exception as e:
                print(f"加载缓存失败: {e}")
    
    img_copy = img.copy()
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal img_copy
        if event == cv2.EVENT_LBUTTONDOWN:
            # 添加新点到列表
            param['points'].append((x, y))
            # 在当前图像上绘制所有点
            temp_img = img.copy()
            for px, py in param['points']:
                cv2.circle(temp_img, (px, py), 3, (0, 255, 0), -1)
            cv2.imshow(window_name, temp_img)
            img_copy = temp_img
    
    points_data = {'points': []}
    cv2.setMouseCallback(window_name, mouse_callback, points_data)
    cv2.imshow(window_name, img_copy)
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and points_data['points']:  # Enter键且至少选择了一个点
            # 保存点到缓存文件
            try:
                with open(cache_file, 'w') as f:
                    json.dump(points_data['points'], f)
                print(f"已保存 {len(points_data['points'])} 个样本点到缓存文件")
            except Exception as e:
                print(f"保存缓存失败: {e}")
            
            cv2.destroyWindow(window_name)
            # 返回所有选择的点的平均颜色位置
            return points_data['points']
        elif key == 27:  # ESC键清除所有点
            img_copy = img.copy()
            cv2.imshow(window_name, img_copy)
            points_data['points'] = []

def extract_data_from_graph(image_url, is_url=True, frequency='week'):
    """
    从图表图像中提取数据点
    
    参数:
    image_url: 图像路径或URL
    is_url: 是否为URL
    frequency: 数据点频率 ('week', 'month', 'year')，默认为'week'
    
    返回:
    value_points: 数据点列表，每个元素为(日期, 值)元组
    result_img: 标注了检测点的结果图像
    """
    # 下载并读取图片
    if is_url:
        response = requests.get(image_url)
        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    else:
        img_array = np.asarray(bytearray(open(image_url, 'rb').read()), dtype=np.uint8)
    

    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    print("请框选数据点区域（包含所有数据点的矩形区域）")
    data_roi = select_data_region(img)
    x, y, w, h = data_roi
    
    # 获取坐标轴范围
    (y_min, y_max), (start_date, end_date) = get_axis_range()
    
    # 提取数据点区域
    points_region = img[y:y+h, x:x+w]
    
    # 交互式选择曲线的样本点
    print("请选择曲线上的多个样本点，按Enter结束选择")
    sample_points = select_sample_point(img)
    
    # 获取所有样本点的颜色，计算颜色范围
    sample_colors = []
    for point in sample_points:
        color = img[point[1], point[0]]
        sample_colors.append(color)
    
    if len(sample_colors) > 0:
        # 计算样本颜色的范围
        sample_colors = np.array(sample_colors)
        avg_sample_color = np.mean(sample_colors, axis=0)
        color_std = np.std(sample_colors, axis=0)
        
        # 根据样本颜色的标准差调整容差
        tolerance = np.maximum(color_std * 2, [10, 10, 10])  # 最小容差为10
        print(f"\n样本点平均颜色: {avg_sample_color}")
        print(f"颜色容差: {tolerance}")
    else:
        avg_sample_color = np.array([0, 0, 0])
        tolerance = np.array([25, 25, 25])
    
    # 创建颜色掩码
    mask = np.zeros(points_region.shape[:2], dtype=np.uint8)
    matched_colors = []  # 用于存储匹配的颜色
    
    for i in range(points_region.shape[0]):
        for j in range(points_region.shape[1]):
            pixel_color = points_region[i, j]
            color_diff = np.abs(pixel_color.astype(np.float32) - avg_sample_color)
            if np.all(color_diff <= tolerance):  # 使用动态容差
                mask[i, j] = 255
                matched_colors.append(pixel_color)
    
    print(f"\n找到的匹配颜色数量: {len(matched_colors)}")
    if matched_colors:
        print(f"匹配颜色示例: {matched_colors[0]}")
    
    # 显示掩码图像
    cv2.imshow('Color Mask', mask)
    cv2.waitKey(1)
    
    # 使用形态学操作清理噪点和连接断开的线段
    # 先进行开运算去除小的噪点
    kernel_open = np.ones((2,2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    
    # 再进行闭运算连接断开的线段
    kernel_close = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    
    # 使用特定形状的结构元素来更好地连接线段
    kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))  # 水平线结构元素
    mask = cv2.dilate(mask, kernel_line, iterations=1)
    
    # 再次进行腐蚀以恢复线条的原始粗细
    mask = cv2.erode(mask, kernel_close, iterations=1)
    
    # 显示处理后的掩码图像
    cv2.imshow('Processed Mask', mask)
    cv2.waitKey(1)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    print(f"\n找到的轮廓数量: {len(contours)}")
    
    # 收集所有点
    points = []
    for contour in contours:
        # 对于每个轮廓点，我们不再进行多边形逼近，而是保留更多细节
        for point in contour:
            px = point[0][0] + x  # 加上ROI的偏移
            py = point[0][1] + y
            points.append((px, py))
    
    print(f"\n提取的点数量（去重前）: {len(points)}")
    
    # 对点进行排序并去重
    points = list(set(points))  # 去重
    points.sort(key=lambda p: p[0])  # 按x坐标排序
    
    # 确保第一个和最后一个点都在
    if len(points) > 0:
        first_point = points[0]
        last_point = points[-1]
        
        # 根据频率参数重新采样，但保留首尾点
        if frequency == 'year':
            # 按年频率计算目标点数
            years_range = end_date.year - start_date.year
            if start_date.month > end_date.month or (start_date.month == end_date.month and start_date.day > end_date.day):
                years_range -= 1
            target_points = max(5, min(years_range + 2, len(points)))  # 至少5个点，最多每年一个点+首尾点
        elif frequency == 'month':
            # 按月频率计算目标点数
            months_range = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
            if start_date.day > end_date.day:
                months_range -= 1
            target_points = max(10, min(months_range + 2, len(points)))  # 至少10个点，最多每月一个点+首尾点
        else:  # 默认按周频率
            # 计算需要的点数（基于日期范围）
            months_range = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
            weeks_range = int(months_range * 4.33)  # 大约每周一个点
            
            # 保证至少有30个点，但不超过原始点数
            target_points = max(30, min(weeks_range, len(points)))
        
        if len(points) > target_points and target_points > 2:
            # 重新采样，但确保首尾点保留
            sampled_points = [first_point]  # 添加第一个点
            
            # 在中间区域均匀采样
            step = (len(points) - 2) / (target_points - 2)
            for i in range(1, target_points - 1):
                idx = int(i * step) + 1
                if idx < len(points) - 1:  # 确保不超出范围
                    sampled_points.append(points[idx])
            
            sampled_points.append(last_point)  # 添加最后一个点
            points = sampled_points
            print(f"按{frequency}频率采样后点数量: {len(points)}")
        elif len(points) > 2:
            # 点数不够目标点数，使用简化算法保留更多点
            # 每隔几个点取一个点，但确保首尾点保留
            if len(points) > 50:  # 如果点数较多，适当减少
                step = len(points) // target_points if target_points > 0 else len(points) // 30
                if step > 1:
                    reduced_points = [points[i] for i in range(0, len(points), step)]
                    # 确保最后一个点包含在内
                    if points[-1] not in reduced_points:
                        reduced_points.append(points[-1])
                    points = reduced_points
            print(f"简化后点数量: {len(points)}")
        else:
            # 点数太少，直接使用所有点，但确保首尾点存在
            if len(points) > 0:
                points = [first_point, last_point] if len(points) == 1 else [first_point] + points[1:-1] + [last_point]
    
    # 转换坐标为实际值
    def pixel_to_value(point):
        px, py = point
        
        # Y值映射
        y_value = y_max - (py - y) * (y_max - y_min) / h
        
        # X值（日期）映射 - 改进日期计算，提供更精确的日期
        # 修复日期重复问题：使用浮点数计算并添加微小偏移
        days_range = (end_date - start_date).days
        days_from_start = (px - x) * days_range / w
        
        # 为了避免日期重复，我们添加一个基于像素位置的微小偏移
        # 这样可以确保即使相邻像素也会映射到不同的日期时间
        microsecond_offset = int(((px - x) / w) * 86400 * 1000000) % 1000000  # 微秒偏移
        
        # 使用浮点数天数计算，而不是整数
        date = start_date + timedelta(days=days_from_start)
        
        # 添加微秒偏移以确保日期唯一性
        date = date + timedelta(microseconds=microsecond_offset)
        
        return (date.strftime('%Y/%m/%d'), y_value)
    
    value_points = [pixel_to_value(p) for p in points]
    
    # 修复日期重复问题：对转换后的日期值也进行去重处理
    # 使用字典按日期分组，保留每个日期的第一个值
    unique_value_points = {}
    for date_str, value in value_points:
        if date_str not in unique_value_points:
            unique_value_points[date_str] = value
        # 如果需要保留平均值而不是第一个值，可以使用以下逻辑：
        # else:
        #     unique_value_points[date_str] = (unique_value_points[date_str] + value) / 2
    
    # 转换回列表格式
    value_points = list(unique_value_points.items())
    
    # 按日期排序
    value_points.sort(key=lambda x: x[0])
    
    # 可视化结果
    result_img = img.copy()
    
    # 绘制数据区域
    cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # 绘制检测到的点
    for px, py in points:
        cv2.circle(result_img, (px, py), 2, (0, 0, 255), -1)
    
    # 绘制样本点
    for px, py in sample_points:
        cv2.circle(result_img, (px, py), 4, (0, 255, 0), -1)
    
    # 添加坐标轴范围标注
    font = cv2.FONT_HERSHEY_SIMPLEX
    # 注意：这里需要确保所有变量都在当前作用域内
    try:
        cv2.putText(result_img, f"{y_max:.1f}", (x-50, y+15), font, 0.5, (0, 0, 255), 1)
        cv2.putText(result_img, f"{y_min:.1f}", (x-50, y+h-5), font, 0.5, (0, 0, 255), 1)
        cv2.putText(result_img, start_date.strftime('%Y/%m'), (x, y+h+20), font, 0.5, (0, 0, 255), 1)
        cv2.putText(result_img, end_date.strftime('%Y/%m'), (x+w-60, y+h+20), font, 0.5, (0, 0, 255), 1)
    except Exception as e:
        print(f"添加文本标注时出错: {e}")
    
    return value_points, result_img

# 使用示例
# image_url = "https://verticalmind.oss-accelerate.aliyuncs.com/new/new/schart/img/DelinquencyrateforcreditcardsAllcommercialbanks_1725606525.png"
# value_points, result_img = extract_data_from_graph(image_url,is_url=True)
if __name__ == "__main__":
    image_path = r"Z:\data\项目\快速处理\图表\图表复制工作流\实物资产比金融资产.png"
    # 可以通过frequency参数设置数据点频率: 'week'(默认), 'month', 'year'
    value_points, result_img = extract_data_from_graph(image_path, is_url=False, frequency='week')

    print(f"\n检测到的点数：{len(value_points)}")
    print("\n数据点（日期, 值）：")
    for point in value_points:
        print(f"({point[0]}, {point[1]:.2f})")

    # 显示结果图像
    cv2.namedWindow('Detected Points', cv2.WINDOW_NORMAL)  # 允许调整窗口大小
    # 调整窗口大小以适应屏幕
    def show_result_image(result_img):
        screen_height = 800  # 设置合适的高度
        screen_width = int(result_img.shape[1] * screen_height / result_img.shape[0])  # 保持宽高比
        cv2.resizeWindow('Detected Points', min(screen_width, 1200), screen_height)  # 限制最大宽度
        cv2.imshow('Detected Points', result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    show_result_image(result_img)
    
    # 保存结果图像
    cv2.imwrite('detected_points.png', result_img)
    # 将value_points转换为DataFrame
    df = pd.DataFrame(value_points, columns=['dt', 'close'])
    
    # 转换日期列为datetime类型
    df['dt'] = pd.to_datetime(df['dt'], format='%Y/%m/%d')
    # df['区域'] = '美国'
    
    # df = df.groupby(['dt','区域'])['close'].mean().reset_index()
    
    # 按日期排序
    df.sort_values('dt', inplace=True)
    
    # 按日期排序（可选）
    df.sort_index(inplace=True)
    df.to_sql('全球实物资产比金融资产', _cursor, if_exists='replace', index=False)