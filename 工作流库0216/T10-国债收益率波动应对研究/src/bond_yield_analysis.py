import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks
import os

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

# --- 配置参数 ---
FILE_PATH = r"/mnt/windows_share/项目/reports/国债收益率波动应对研究/国债收益率数据.xlsx"
TEN_YEAR_BOND_CODE = 'L001619604'  # 10年国债
ONE_YEAR_BOND_CODE = 'L001619275'   # 1年国债
OUTPUT_DIR = "analysis_results"

# 创建输出目录
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 1. 数据加载和预处理 ---
def load_and_preprocess_data(file_path, trade_code):
    """加载指定债券代码的数据并进行预处理"""
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"错误：文件未找到 {file_path}")
        return None
    
    df_bond = df[df['trade_code'] == trade_code].copy()
    
    if df_bond.empty:
        print(f"错误：交易代码 {trade_code} 在文件中未找到或数据为空。")
        return None
        
    df_bond['dt'] = pd.to_datetime(df_bond['dt'])
    df_bond = df_bond.sort_values(by='dt').set_index('dt')
    df_bond['CLOSE'] = pd.to_numeric(df_bond['CLOSE'], errors='coerce')
    df_bond = df_bond.dropna(subset=['CLOSE'])
    
    # 计算每日收益率变化 (BP)
    # 假设 'CLOSE' 列是百分比数值，例如2.5代表2.5%。
    # 那么 (CLOSE_today - CLOSE_yesterday) 是百分点的变化。
    # 0.01个百分点 = 1 BP. 所以，diff() 结果乘以100得到BP。
    df_bond['change_bp'] = df_bond['CLOSE'].diff() * 100

    df_bond = df_bond.dropna(subset=['change_bp']) # Drop first row with NaN change
    return df_bond

# --- 研究（1）：行情突然性分析 ---
def analyze_suddenness(df_bond, bond_name):
    """分析并可视化行情的突然性"""
    print(f"\n--- 研究（1）：{bond_name} 行情突然性分析 ---")
    if df_bond.empty or len(df_bond) < 30: # Need enough data for peak finding
        print("数据不足，无法进行有效的行情阶段分析。")
        return

    # 1. 绘制整体收益率曲线
    plt.figure(figsize=(14, 7))
    plt.plot(df_bond.index, df_bond['CLOSE'], label=f'{bond_name} 收益率')
    plt.title(f'{bond_name} 国债收益率走势')
    plt.xlabel('日期')
    plt.ylabel('收益率 (%)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, f'{bond_name}_yield_curve.png'))
    plt.close()
    print(f"已保存 {bond_name} 收益率走势图。")

    # 2. 使用 find_peaks 识别行情阶段
    yield_series = df_bond['CLOSE']
    
    # 根据债券名称设置不同的prominence (突显度)，单位是收益率的单位(%)
    # 5BP = 0.05%, 2BP = 0.02%
    # prominence_value = 0.05 if "10年" in bond_name else 0.02 
    # 设置最小距离，避免过于密集的峰谷，例如至少间隔一个月（约21个交易日）
    # min_distance_days = 21 

    # 新的参数，旨在将阶段数量减少到约15个 (可能需要根据数据微调)
    if "10年" in bond_name:
        prominence_value = 0.25 # 25 BP 收益率变动
        min_distance_days = 80 # 约4个月的交易日
    else: # 1年期债券
        prominence_value = 0.15 # 15 BP 收益率变动
        min_distance_days = 60 # 约3个月的交易日

    print(f"使用 prominence={prominence_value*100:.0f}BP, min_distance={min_distance_days}交易日 进行阶段划分。")

    peak_indices, _ = find_peaks(yield_series, prominence=prominence_value, distance=min_distance_days)
    trough_indices, _ = find_peaks(-yield_series, prominence=prominence_value, distance=min_distance_days)

    critical_indices_loc = sorted(list(set(list(peak_indices) + list(trough_indices))))

    # 确保包含数据系列的起始点和结束点
    if not critical_indices_loc or critical_indices_loc[0] != 0:
        critical_indices_loc.insert(0, 0)
    if critical_indices_loc[-1] != len(yield_series) - 1:
        critical_indices_loc.append(len(yield_series) - 1)
    
    # 去重并排序
    critical_indices_loc = sorted(list(set(critical_indices_loc)))
    
    stages = []
    if len(critical_indices_loc) < 2:
        print("未能识别出足够的关键转折点来定义行情阶段。")
        return

    for i in range(len(critical_indices_loc) - 1):
        start_loc = critical_indices_loc[i]
        end_loc = critical_indices_loc[i+1]

        if start_loc == end_loc: # Should not happen if distinct sorted points
            continue

        stage_df_slice = df_bond.iloc[start_loc : end_loc + 1]
        
        start_date = stage_df_slice.index[0]
        end_date = stage_df_slice.index[-1]
        start_price = stage_df_slice['CLOSE'].iloc[0]
        end_price = stage_df_slice['CLOSE'].iloc[-1]

        # 从 start_loc 的第二天到 end_loc 获取 change_bp
        # change_bp 的索引是相对于 df_bond 来的
        # df_bond.iloc[k] 对应 df_bond['change_bp'].iloc[k] (因为 change_bp dropna(1) 了)
        # 但 change_bp.iloc[k] 实际上是 df_bond.index[k+1] 的变化
        # 所以如果阶段是 df_bond.iloc[start_loc:end_loc+1]
        # 对应的 change_bp 是 df_bond['change_bp'].iloc[start_loc : end_loc] (len = end_loc - start_loc)
        # these are the changes *within* the stage, starting from the day after start_loc's price
        
        current_stage_changes_bp = list(df_bond['change_bp'].iloc[start_loc : end_loc])


        if not current_stage_changes_bp and start_loc != end_loc : # Single day stage, no diff recorded if it's the first day overall
             # For a stage of one point to another, total change IS (end_price - start_price)*100
             # If stage is just one data point (start_loc == end_loc), this loop structure skips.
             # If stage is two data points (e.g. loc 0 to loc 1), changes_bp is df_bond['change_bp'].iloc[0:1] which is one value.
             pass


        total_stage_bp_change = (end_price - start_price) * 100
        stage_type_val = np.sign(total_stage_bp_change)
        
        if stage_type_val == 0 and start_loc != end_loc: # Flat stage, but has duration
            stage_type_val = 1 # Arbitrarily assign, or could be skipped if desired

        if stage_type_val == 0 and start_loc == end_loc: # Single point "stage", skip
            continue


        stages.append({
            'start_date': start_date,
            'end_date': end_date,
            'start_price': start_price,
            'end_price': end_price,
            'type': stage_type_val, # 1 for up, -1 for down
            'duration_calendar_days': (end_date - start_date).days +1, # Calendar days might be large if gaps
            'active_change_days': len([c for c in current_stage_changes_bp if c != 0]),
            'changes_bp': current_stage_changes_bp, # List of daily BPs *within* the stage
            'total_change_bp': total_stage_bp_change, # Overall BP change for the stage
            'prices_in_stage': list(stage_df_slice['CLOSE'])
        })
        
    if not stages:
        print("未能识别出明确的行情阶段。")
        return

    stages_df = pd.DataFrame(stages)
    stages_df = stages_df[stages_df['active_change_days'] > 0] # Ensure stage has at least one active day

    if stages_df.empty:
        print("过滤后无有效行情阶段。")
        return
        
    print(f"识别出 {len(stages_df)} 个行情阶段。")

    stage_concentration_info = []
    for idx, stage in stages_df.iterrows():
        if stage['active_change_days'] == 0 or not stage['changes_bp']:
            continue

        total_abs_change_bp_in_stage = abs(stage['total_change_bp'])
        if total_abs_change_bp_in_stage == 0:
            continue
            
        # Use only non-zero changes for concentration analysis if any zeros were stored
        active_changes_bp = [c for c in stage['changes_bp'] if c != 0]
        if not active_changes_bp: continue

        current_abs_cumulative_bp = 0
        days_for_10_pct = -1
        days_for_50_pct = -1
        days_for_90_pct = -1
        
        for day_num, daily_change_bp in enumerate(active_changes_bp):
            current_abs_cumulative_bp += abs(daily_change_bp)
            if days_for_10_pct == -1 and current_abs_cumulative_bp >= 0.1 * total_abs_change_bp_in_stage:
                days_for_10_pct = day_num + 1
            if days_for_50_pct == -1 and current_abs_cumulative_bp >= 0.5 * total_abs_change_bp_in_stage:
                days_for_50_pct = day_num + 1
            if days_for_90_pct == -1 and current_abs_cumulative_bp >= 0.9 * total_abs_change_bp_in_stage:
                days_for_90_pct = day_num + 1
                break 
        
        num_active_days_in_stage = len(active_changes_bp)
        stage_concentration_info.append({
            'start_date': stage['start_date'],
            'end_date': stage['end_date'],
            'type': '上涨' if stage['type'] == 1 else '下跌',
            'duration_calendar_days': stage['duration_calendar_days'],
            'active_change_days': num_active_days_in_stage,
            'total_abs_change_bp': total_abs_change_bp_in_stage,
            'days_for_10_pct_change': days_for_10_pct,
            'days_for_50_pct_change': days_for_50_pct,
            'days_for_90_pct_change': days_for_90_pct,
            'pct_time_for_90_pct_change': (days_for_90_pct / num_active_days_in_stage * 100) if num_active_days_in_stage > 0 and days_for_90_pct != -1 else None
        })

    concentration_df = pd.DataFrame(stage_concentration_info)
    if not concentration_df.empty:
        print("\n行情阶段集中度分析:")
        print(concentration_df)
        concentration_df.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_stage_concentration.csv'), index=False, encoding='utf-8-sig')
        print(f"已保存 {bond_name} 行情阶段集中度分析到CSV文件。")

        if 'pct_time_for_90_pct_change' in concentration_df.columns:
            plt.figure(figsize=(10, 6))
            valid_pct_times = concentration_df['pct_time_for_90_pct_change'].dropna()
            if not valid_pct_times.empty:
                plt.hist(valid_pct_times, bins=np.arange(0, 101, 5), edgecolor='black') # Bins from 0 to 100, step 5
                plt.title(f'{bond_name}: 完成90%行情所需时间的百分比分布')
                plt.xlabel('完成90%行情所用时间的百分比 (% of active days in stage)')
                plt.ylabel('阶段数量')
                plt.xticks(np.arange(0, 101, 10))
                plt.grid(True)
                plt.savefig(os.path.join(OUTPUT_DIR, f'{bond_name}_90pct_change_time_distribution.png'))
                plt.close()
                print(f"已保存 {bond_name} 90%行情时间分布图。")

                avg_pct_time = valid_pct_times.mean()
                median_pct_time = valid_pct_times.median()
                mode_pct_time = valid_pct_times.mode()
                mode_pct_time_str = ", ".join([f"{m:.2f}" for m in mode_pct_time]) if not mode_pct_time.empty else "N/A"
                
                print(f"平均而言，90%的行情在阶段内 {avg_pct_time:.2f}% 的有效交易日内完成。")
                print(f"中位数显示，90%的行情在阶段内 {median_pct_time:.2f}% 的有效交易日内完成。")
                print(f"众数显示，90%的行情在阶段内 {mode_pct_time_str}% 的有效交易日内完成。")

                # Conclusion based on these stats
                if median_pct_time < 30 and avg_pct_time < 40 : # Example thresholds
                     print("结论：数据支持行情具有突然性，大部分变动集中在阶段内较短的时间完成。")
                elif median_pct_time < 50:
                     print("结论：数据部分支持行情具有突然性，存在集中完成的情况。")
                else:
                     print("结论：从90%行情完成时间看，行情的突然性不显著。")
            else:
                print("没有足够的有效数据来绘制90%行情时间分布图或得出结论。")
    else:
        print("未能生成行情阶段集中度分析数据。")


    if not stages_df.empty:
        stages_df_sorted = stages_df.copy()
        stages_df_sorted['abs_total_change_bp'] = stages_df_sorted['total_change_bp'].abs()
        # Sort by absolute change, then by active days to pick more sustained moves if changes are similar
        stages_df_sorted = stages_df_sorted.sort_values(by=['abs_total_change_bp', 'active_change_days'], ascending=[False, False])

        plot_stages_indices = []
        # Get one significant up stage
        up_stages = stages_df_sorted[stages_df_sorted['type']==1]
        if not up_stages.empty: plot_stages_indices.append(up_stages.index[0])
        # Get one significant down stage
        down_stages = stages_df_sorted[stages_df_sorted['type']==-1]
        if not down_stages.empty: plot_stages_indices.append(down_stages.index[0])
        
        for stage_idx in plot_stages_indices:
            stage_to_plot = stages_df.loc[stage_idx]
            active_changes_bp = [c for c in stage_to_plot['changes_bp'] if c != 0]
            if not active_changes_bp: continue
            
            stage_type_str = "上涨" if stage_to_plot['type'] == 1 else "下跌"
            title = f"{bond_name} {stage_type_str}阶段 ({stage_to_plot['start_date'].strftime('%Y-%m-%d')} to {stage_to_plot['end_date'].strftime('%Y-%m-%d')})\n累计收益率变动 (BP)"
            
            plot_cumulative_bp = [0] + list(np.cumsum(active_changes_bp))
            days_in_stage_xaxis = range(len(plot_cumulative_bp))

            plt.figure(figsize=(12, 6))
            plt.plot(days_in_stage_xaxis, plot_cumulative_bp, marker='o', linestyle='-')
            
            total_stage_abs_change = abs(stage_to_plot['total_change_bp'])
            if total_stage_abs_change > 0:
                target_90_pct_abs_change = 0.9 * total_stage_abs_change
                day_for_90_pct_plot = -1
                for d_idx in range(1, len(plot_cumulative_bp)): 
                    if abs(plot_cumulative_bp[d_idx]) >= target_90_pct_abs_change:
                        day_for_90_pct_plot = d_idx 
                        plt.axvline(x=day_for_90_pct_plot, color='r', linestyle='--', 
                                    label=f'90% 行情 ({day_for_90_pct_plot} 天内 / {len(active_changes_bp)} 总有效天数)')
                        break
            
            plt.title(title)
            plt.xlabel(f'阶段内有效交易日天数 (共 {len(active_changes_bp)} 天, 0 = 阶段开始前)')
            plt.ylabel('累计收益率变动 (BP)')
            plt.legend()
            plt.grid(True)
            plt.savefig(os.path.join(OUTPUT_DIR, f"{bond_name}_stage_{stage_to_plot['start_date'].strftime('%Y%m%d')}_cumulative_change.png"))
            plt.close()
            print(f"已保存阶段 {stage_to_plot['start_date'].strftime('%Y%m%d')} 的累计变动图。")


# --- Helper Function for Strategy Simulation ---
def simulate_trading_strategy(df_period_data, tenor, strategy_type, params=None):
    """Simulates a trading strategy (rule-based or buy-and-hold) over a given period.

    Args:
        df_period_data (pd.DataFrame): DataFrame with 'CLOSE' and 'change_bp' for the period.
        tenor (int): Bond tenor in years.
        strategy_type (str): 'rule_based' or 'buy_and_hold'.
        params (dict, optional): Parameters for 'rule_based' strategy. 
                                 Required if strategy_type is 'rule_based'.
                                 Keys: 'up_thresh_bp', 'down_thresh_bp', 
                                       'buy_abs_increment', 'sell_abs_increment'.

    Returns:
        tuple: (sim_df_details, cumulative_pnl_pct, annualized_pnl_pct)
               sim_df_details (pd.DataFrame): DataFrame with simulation details (P&L, position, etc.)
               cumulative_pnl_pct (float): Total cumulative P&L as a percentage.
               annualized_pnl_pct (float): Annualized P&L as a percentage.
    """
    if df_period_data.empty or len(df_period_data) < 1:
        # print(f"Warning: Simulation data for period is empty or too short. Returning zero P&L.")
        return pd.DataFrame(), 0.0, 0.0

    sim_df = df_period_data.copy()

    sim_df['position_at_eod'] = 0.0
    sim_df['weighted_yield_sum_eod'] = 0.0
    sim_df['position_at_sod'] = 0.0
    sim_df['avg_entry_yield_at_sod'] = 0.0
    sim_df['pnl_daily_pct'] = 0.0

    current_long_pos_eod = 0.0
    current_weighted_yield_sum_eod = 0.0

    if strategy_type == 'buy_and_hold':
        # For buy and hold, buy 100% on the first day and hold.
        # The first day's SOD position is 0, it becomes 100% at EOD of day 0 (or effectively SOD of day 1)
        # To correctly calculate P&L for day 0, we assume the buy happens *before* market close of day 0.
        # So, for day 0, SOD position is 1.0, avg_entry_yield is CLOSE of day 0.
        pass # SOD state will be set in the loop for day 0 correctly for B&H

    for i in range(len(sim_df)):
        today_change_bp = sim_df['change_bp'].iloc[i]
        today_close_yield = sim_df['CLOSE'].iloc[i]

        if i == 0 and strategy_type == 'buy_and_hold':
            pos_sod = 1.0 # Buy 100% at the start of the first day
            avg_entry_yield_sod = today_close_yield # Entry yield is the first day's close yield
            # EOD state for B&H will also be 1.0 pos and corresponding weighted_yield_sum
            current_long_pos_eod = 1.0 
            current_weighted_yield_sum_eod = 1.0 * today_close_yield
        else:
            pos_sod = current_long_pos_eod
            weighted_sum_sod = current_weighted_yield_sum_eod
            avg_entry_yield_sod = weighted_sum_sod / pos_sod if pos_sod > 1e-6 else 0.0
        
        sim_df.iloc[i, sim_df.columns.get_loc('position_at_sod')] = pos_sod
        sim_df.iloc[i, sim_df.columns.get_loc('avg_entry_yield_at_sod')] = avg_entry_yield_sod

        price_pnl_pct = pos_sod * tenor * (-today_change_bp / 100.0)
        coupon_pnl_pct = 0.0
        if pos_sod > 1e-6 and avg_entry_yield_sod > 0:
            coupon_pnl_pct = pos_sod * (avg_entry_yield_sod / 100.0) / 365.25
        
        daily_pnl_pct = price_pnl_pct + coupon_pnl_pct
        sim_df.iloc[i, sim_df.columns.get_loc('pnl_daily_pct')] = daily_pnl_pct

        # --- Position Update Logic (for EOD values) ---
        temp_current_long_pos = pos_sod
        temp_weighted_yield_sum = avg_entry_yield_sod * pos_sod if pos_sod > 1e-6 else 0.0 # Reconstruct from avg
        
        if strategy_type == 'rule_based':
            if params is None:
                raise ValueError("Parameters 'params' must be provided for 'rule_based' strategy.")
            yield_for_new_trades = today_close_yield
            if today_change_bp > params['up_thresh_bp']: # Yields UP, BUY
                buy_amount = params['buy_abs_increment']
                actual_buy = min(buy_amount, 1.0 - temp_current_long_pos)
                if actual_buy > 1e-6:
                    temp_weighted_yield_sum += actual_buy * yield_for_new_trades
                    temp_current_long_pos += actual_buy
            elif today_change_bp < -params['down_thresh_bp']: # Yields DOWN, SELL
                sell_amount = params['sell_abs_increment']
                actual_sell = min(sell_amount, temp_current_long_pos)
                if actual_sell > 1e-6:
                    if temp_current_long_pos > 1e-6: 
                        temp_weighted_yield_sum -= (actual_sell / temp_current_long_pos) * temp_weighted_yield_sum
                    temp_current_long_pos -= actual_sell
                    if temp_current_long_pos < 1e-6:
                        temp_current_long_pos = 0.0
                        temp_weighted_yield_sum = 0.0
        elif strategy_type == 'buy_and_hold':
            # Position remains 100% unless it's the very first setup
            if i == 0: # Already handled by the specific if block for B&H day 0 SOD and EOD setup
                 pass # EOD is already set to 1.0 and correct sum
            else: # For subsequent days, position and sum just carry over from previous EOD
                 temp_current_long_pos = current_long_pos_eod # Should be 1.0
                 temp_weighted_yield_sum = current_weighted_yield_sum_eod # Should be 1.0 * initial yield
        
        current_long_pos_eod = temp_current_long_pos
        current_weighted_yield_sum_eod = temp_weighted_yield_sum
        sim_df.iloc[i, sim_df.columns.get_loc('position_at_eod')] = current_long_pos_eod
        sim_df.iloc[i, sim_df.columns.get_loc('weighted_yield_sum_eod')] = current_weighted_yield_sum_eod

    sim_df['cumulative_pnl_pct'] = sim_df['pnl_daily_pct'].cumsum()
    cumulative_pnl_pct = sim_df['cumulative_pnl_pct'].iloc[-1] if not sim_df.empty else 0.0

    # Annualization
    annualized_pnl_pct = 0.0
    if not sim_df.empty and len(sim_df.index) > 0:
        total_return_decimal = cumulative_pnl_pct / 100.0
        start_date_sim = sim_df.index.min()
        end_date_sim = sim_df.index.max()
        # Use number of rows for period length if dates are not continuous or for single point data
        num_days_in_period = (end_date_sim - start_date_sim).days + 1 if len(sim_df.index) > 1 else 1
        
        if num_days_in_period > 0:
            num_years = num_days_in_period / 365.25 
            if num_years > 1e-6: # Avoid division by zero for very short periods
                annualized_pnl_decimal = ((1 + total_return_decimal)**(1 / num_years)) - 1 if total_return_decimal > -1 else -1.0
                annualized_pnl_pct = annualized_pnl_decimal * 100
            elif num_days_in_period == 1 and total_return_decimal != 0: # Handle single day with P&L
                annualized_pnl_decimal = ((1 + total_return_decimal)**(365.25)) - 1 # Extrapolate single day
                annualized_pnl_pct = annualized_pnl_decimal * 100
            # else: annualized_pnl_pct remains 0.0 if period is too short for meaningful annualization or no PnL
    
    return sim_df, cumulative_pnl_pct, annualized_pnl_pct


# --- Plotting Helper Function for Annual Distributions ---
def plot_annual_performance_distributions(all_years_distribution_data, bond_name):
    """Plots annual performance distributions and saves them to a file."""
    if not all_years_distribution_data:
        print(f"No distribution data provided for {bond_name} to plot.")
        return

    num_years = len(all_years_distribution_data)
    if num_years == 0: return
    
    cols = 2
    rows = (num_years + cols - 1) // cols # Calculate rows needed
    
    fig_height_per_row = 5
    fig_width_total = 12
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width_total, rows * fig_height_per_row), squeeze=False)
    axes = axes.flatten() # Flatten to 1D array for easy iteration

    for i, year_data in enumerate(all_years_distribution_data):
        year = year_data['year']
        rule_returns = year_data['all_rule_returns_pct']
        bnh_return = year_data['bnh_annual_pnl_pct']

        ax = axes[i]
        if rule_returns:
            ax.hist(rule_returns, bins=20, alpha=0.7, label='规则策略组合', color='skyblue', edgecolor='black')
            min_val, max_val = min(rule_returns), max(rule_returns)
            median_val = np.median(rule_returns)
            ax.axvline(median_val, color='orange', linestyle='--', linewidth=2, label=f'规则中位数: {median_val:.2f}%')
        else:
            min_val, max_val = bnh_return -1, bnh_return + 1 # Default range if no rule returns
            ax.text(0.5, 0.5, '无规则策略数据', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

        if pd.notna(bnh_return):
            ax.axvline(bnh_return, color='red', linestyle='-', linewidth=2, label=f'买入并持有: {bnh_return:.2f}%')
        
        ax.set_title(f'{bond_name} - {year}年 策略年化收益率分布')
        ax.set_xlabel('年化收益率 (%)')
        ax.set_ylabel('策略组合数量')
        ax.legend()
        ax.grid(True)
        
        # Set x-axis limits to be slightly wider than data range for better visibility
        if rule_returns or pd.notna(bnh_return):
            plot_min = min(min_val, bnh_return if pd.notna(bnh_return) else min_val) - 1
            plot_max = max(max_val, bnh_return if pd.notna(bnh_return) else max_val) + 1
            ax.set_xlim(plot_min, plot_max)

    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout(pad=3.0)
    fig_path = os.path.join(OUTPUT_DIR, f'{bond_name}_annual_performance_distributions.png')
    plt.savefig(fig_path)
    plt.close(fig)
    print(f"已保存 {bond_name} 年度策略表现分布组合图到: {fig_path}")

# --- Plotting Helper for Historical Summary ---
def plot_historical_summary_comparison(annual_summary_df, bond_name):
    """Plots historical summary of median, Q1, min rule returns vs B&H."""
    if annual_summary_df.empty:
        print(f"No summary data provided for {bond_name} to plot historical comparison.")
        return

    plt.figure(figsize=(15, 8))
    plt.plot(annual_summary_df['year'], annual_summary_df['rule_annual_pnl_pct'], marker='*', linestyle='-', color='gold', markersize=10, zorder=10, label='最优规则策略收益率')
    plt.plot(annual_summary_df['year'], annual_summary_df['q75_rule_annual_pnl_pct'], marker='x', linestyle='--', color='mediumseagreen', label='规则策略Q3(前1/4)收益率')
    plt.plot(annual_summary_df['year'], annual_summary_df['median_rule_annual_pnl_pct'], marker='o', linestyle='-', label='规则策略中位数收益率')
    plt.plot(annual_summary_df['year'], annual_summary_df['q25_rule_annual_pnl_pct'], marker='s', linestyle='--', label='规则策略Q1收益率')
    plt.plot(annual_summary_df['year'], annual_summary_df['min_rule_annual_pnl_pct'], marker='^', linestyle=':', label='规则策略最低收益率')
    plt.plot(annual_summary_df['year'], annual_summary_df['bnh_annual_pnl_pct'], marker='D', linestyle='-', linewidth=2.5, markersize=8, label='买入并持有收益率 (基准)')
    
    plt.title(f'{bond_name} - 历史年度策略表现汇总对比')
    plt.xlabel('年份')
    plt.ylabel('年化收益率 (%)')
    plt.xticks(annual_summary_df['year'].unique(), rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    fig_path = os.path.join(OUTPUT_DIR, f'{bond_name}_historical_summary_comparison.png')
    plt.savefig(fig_path)
    plt.close()
    print(f"已保存 {bond_name} 历史策略表现汇总对比图到: {fig_path}")

# --- 研究（2）：策略回测与优化 ---
def strategy_backtest_and_optimization(df_bond_orig, bond_name, tenor):
    print(f"\n--- 研究（2）：{bond_name} 策略优化与基准比较 (优化期特定) ---")
    df_bond = df_bond_orig.copy()

    optimization_start_date_config = pd.to_datetime("2025-01-01")
    optimization_end_date_config = pd.to_datetime("2025-06-05")

    actual_data_start = df_bond.index.min()
    actual_data_end = df_bond.index.max()

    optimization_start_date = max(actual_data_start, optimization_start_date_config)
    optimization_end_date = min(actual_data_end, optimization_end_date_config)

    if optimization_start_date > optimization_end_date or actual_data_end < optimization_start_date_config:
        print(f"数据范围 ({actual_data_start.date()} to {actual_data_end.date()})不足以覆盖配置的优化期起始 {optimization_start_date_config.date()}。")
        print("无法进行研究（2）的策略优化部分。")
        return None # Return None or an empty structure if not proceeding

    df_optimization_period = df_bond[(df_bond.index >= optimization_start_date) & (df_bond.index <= optimization_end_date)].copy()

    if df_optimization_period.empty or len(df_optimization_period) < 1:
        print(f"在调整后的优化期间 ({optimization_start_date.date()} to {optimization_end_date.date()}) 没有足够的数据。")
        return None
    
    print(f"策略优化与基准比较将在 {optimization_start_date.date()} 到 {optimization_end_date.date()} 期间进行。")

    param_grid = {
        'up_thresh_bp': [0.5, 1, 1.5, 2, 2.5, 3],
        'down_thresh_bp': [0.5, 1, 1.5, 2, 2.5, 3],
        'buy_abs_increment': [0.10, 0.25, 0.50, 0.75, 1.0],
        'sell_abs_increment': [0.10, 0.25, 0.50, 0.75, 1.0]
    }

    best_params_opt = None
    max_annualized_pnl_pct_opt = -float('inf')
    best_strategy_details_optimization_df = pd.DataFrame()

    all_combinations_results_this_period = [] # For storing all combos performance

    num_combinations = np.prod([len(v) for v in param_grid.values()])
    print(f"开始遍历 {num_combinations} 种参数组合进行规则策略优化...")
    
    count = 0
    for up_t in param_grid['up_thresh_bp']:
        for down_t in param_grid['down_thresh_bp']:
            for buy_incr in param_grid['buy_abs_increment']:
                for sell_incr in param_grid['sell_abs_increment']:
                    params = {
                        'up_thresh_bp': up_t, 'down_thresh_bp': down_t,
                        'buy_abs_increment': buy_incr, 'sell_abs_increment': sell_incr
                    }
                    count += 1
                    if count % 100 == 0 or count == num_combinations:
                        print(f"  已完成 {count}/{num_combinations} 组合...")
                    
                    _sim_df_details, _cumulative_pnl, annualized_pnl = simulate_trading_strategy(
                        df_optimization_period, tenor, 'rule_based', params=params
                    )
                    
                    current_combo_result = params.copy()
                    current_combo_result['annualized_pnl_pct'] = annualized_pnl
                    all_combinations_results_this_period.append(current_combo_result)
                    
                    if annualized_pnl > max_annualized_pnl_pct_opt:
                        max_annualized_pnl_pct_opt = annualized_pnl
                        best_params_opt = params.copy()
                        best_strategy_details_optimization_df = _sim_df_details.copy()
    
    # Save all combinations for this optimization period
    if all_combinations_results_this_period:
        all_combos_df_opt_period = pd.DataFrame(all_combinations_results_this_period)
        opt_period_label = f"{optimization_start_date.year}{(optimization_start_date.month):02d}{optimization_start_date.day:02d}-{optimization_end_date.year}{(optimization_end_date.month):02d}{optimization_end_date.day:02d}"
        all_combos_filename = os.path.join(OUTPUT_DIR, f'{bond_name}_{opt_period_label}_all_combinations_performance.csv')
        all_combos_df_opt_period.to_csv(all_combos_filename, index=False, encoding='utf-8-sig')
        print(f"已将优化期所有组合表现保存到: {all_combos_filename}")

    if not best_params_opt:
        print("在优化期未能找到有效的规则策略参数。")
    else:
        print(f"\n优化期 ({optimization_start_date.date()} to {optimization_end_date.date()}) 最佳规则策略参数:")
        print(best_params_opt)
        print(f"最佳规则策略 年化收益率: {max_annualized_pnl_pct_opt:.2f}% (占总资本)")
        
        # Sort all_combinations_results_this_period for the optimization log
        all_combos_df_opt_period_sorted = all_combos_df_opt_period.sort_values(by='annualized_pnl_pct', ascending=False)
        all_combos_df_opt_period_sorted.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_strategy_optimization_results_pct.csv'), index=False, encoding='utf-8-sig')
        print(f"已保存策略优化迭代结果 (年化百分比收益) 到CSV文件。")

        if not best_strategy_details_optimization_df.empty:
            fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
            axes[0].plot(best_strategy_details_optimization_df.index, best_strategy_details_optimization_df['CLOSE'], label='收益率 (%)', color='blue')
            axes[0].set_ylabel('收益率 (%)')
            axes[0].tick_params(axis='y', labelcolor='blue')
            axes[0].legend(loc='upper left'); axes[0].grid(True)
            ax0_twin = axes[0].twinx()
            ax0_twin.plot(best_strategy_details_optimization_df.index, best_strategy_details_optimization_df['position_at_sod']*100, label='多头头寸 (%)', color='red', linestyle='--')
            ax0_twin.set_ylabel('多头头寸 (% of Capital)', color='red')
            ax0_twin.tick_params(axis='y', labelcolor='red')
            ax0_twin.legend(loc='upper right')
            axes[0].set_title(f'{bond_name} 最佳规则策略表现 (优化期: {optimization_start_date.date()} to {optimization_end_date.date()})')

            axes[1].plot(best_strategy_details_optimization_df.index, best_strategy_details_optimization_df['cumulative_pnl_pct'], label='累计收益率 (%)', color='green')
            axes[1].set_ylabel('累计收益率 (%)'); axes[1].legend(loc='upper left'); axes[1].grid(True)

            axes[2].bar(best_strategy_details_optimization_df.index, best_strategy_details_optimization_df['pnl_daily_pct'], label='每日收益率 (%)', color='purple', width=0.8)
            axes[2].set_ylabel('每日收益率 (%)'); axes[2].legend(loc='upper left'); axes[2].grid(True)
            
            plt.xlabel('日期'); plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f'{bond_name}_best_rule_strategy_optimization_period_pct.png'))
            plt.close()
            print(f"已保存最佳规则策略在优化期的表现图。")

    print(f"\n计算优化期 ({optimization_start_date.date()} to {optimization_end_date.date()}) '买入并持有' 基准策略...")
    bnh_sim_df, bnh_cumulative_pnl, bnh_annualized_pnl = simulate_trading_strategy(
        df_optimization_period, tenor, 'buy_and_hold'
    )
    print(f"优化期 '买入并持有' 基准策略 年化收益率: {bnh_annualized_pnl:.2f}% (占总资本)")
    if not bnh_sim_df.empty:
         bnh_sim_df.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_buy_and_hold_optimization_period_details.csv'), index=True, encoding='utf-8-sig')
         print(f"已保存优化期 '买入并持有' 基准策略详情到CSV。")

    # Prepare data for the distribution plot for this specific optimization period
    optimization_period_distribution_data = None
    if all_combinations_results_this_period:
        optimization_period_distribution_data = {
            'year': f"{opt_period_label}", # Use period label as year for this plot
            'all_rule_returns_pct': [res['annualized_pnl_pct'] for res in all_combinations_results_this_period],
            'bnh_annual_pnl_pct': bnh_annualized_pnl
        }

    print(f"\n--- {bond_name} 优化期 ({optimization_start_date.date()} to {optimization_end_date.date()}) 总结 ---")
    if best_params_opt:
        print(f"最佳规则策略年化收益率: {max_annualized_pnl_pct_opt:.2f}%")
    else:
        print("最佳规则策略：未能找到有效参数。")
    print(f"'买入并持有'基准策略年化收益率: {bnh_annualized_pnl:.2f}%")
    if best_params_opt and max_annualized_pnl_pct_opt > bnh_annualized_pnl:
        print("结论：在此优化期间，最佳规则策略表现优于'买入并持有'基准。")
    elif best_params_opt:
        print("结论：在此优化期间，'买入并持有'基准策略表现优于或等于最佳规则策略。")
    else:
        print("结论：因未能找到有效规则，无法与'买入并持有'基准进行比较。")
    
    return optimization_period_distribution_data # Return data for combined plotting


# --- 新函数：年度对比回测 ---
def perform_annual_comparative_analysis(df_full_history, bond_name, tenor):
    print(f"\n--- {bond_name}: 年度规则优化 vs 买入并持有历史对比分析 ---")
    if df_full_history.empty or len(df_full_history) < 20: 
        print("历史数据不足，无法进行年度对比分析。")
        return [] # Return empty list for distribution plot data

    df_full_history['year'] = df_full_history.index.year
    unique_years = sorted(df_full_history['year'].unique())

    annual_comparison_results_summary = [] # For the summary table and historical plot
    all_years_distribution_plot_data = [] # For the combined distribution plot

    param_grid_annual = {
        'up_thresh_bp': [1, 2, 3, 5], 
        'down_thresh_bp': [1, 2, 3, 5],
        'buy_abs_increment': [0.25, 0.50, 1.0],
        'sell_abs_increment': [0.25, 0.50, 1.0]
    }
    num_annual_combinations = np.prod([len(v) for v in param_grid_annual.values()])

    for year in unique_years:
        print(f"\n-- 分析年份: {year} for {bond_name} --")
        df_current_year = df_full_history[df_full_history['year'] == year].copy()
        df_current_year = df_current_year.drop(columns=['year'])

        if len(df_current_year) < 20: 
            print(f"  年份 {year} 数据过少 ({len(df_current_year)} 天)，跳过。")
            # Still add a placeholder for consistent plotting if desired, or handle in plot function
            all_years_distribution_plot_data.append({
                'year': year, 'all_rule_returns_pct': [], 'bnh_annual_pnl_pct': np.nan
            })
            annual_comparison_results_summary.append({
                'year': year, 'rule_annual_pnl_pct': np.nan, 'bnh_annual_pnl_pct': np.nan,
                'best_params_this_year': None, 'rule_outperformed': np.nan,
                'median_rule_annual_pnl_pct': np.nan, 'q25_rule_annual_pnl_pct': np.nan, 'min_rule_annual_pnl_pct': np.nan,
                'q75_rule_annual_pnl_pct': np.nan
            })
            continue

        best_annualized_pnl_rule_this_year = -float('inf')
        best_params_this_year = None
        current_year_all_combo_performance_list = [] # Store all {params: annualized_pnl} for this year
        current_year_all_rule_returns_pct = [] # Just the returns for median/q1/min/dist plot
        
        print(f"  为年份 {year} 优化规则策略 (共 {num_annual_combinations} 组合)...", end=" ")
        current_best_sim_df_this_year = pd.DataFrame()

        for up_t_yr in param_grid_annual['up_thresh_bp']:
            for down_t_yr in param_grid_annual['down_thresh_bp']:
                for buy_incr_yr in param_grid_annual['buy_abs_increment']:
                    for sell_incr_yr in param_grid_annual['sell_abs_increment']:
                        params_yr = {
                            'up_thresh_bp': up_t_yr, 'down_thresh_bp': down_t_yr,
                            'buy_abs_increment': buy_incr_yr, 'sell_abs_increment': sell_incr_yr
                        }
                        _sim_df_yr, _cum_pnl_yr, annualized_pnl_yr = simulate_trading_strategy(
                            df_current_year, tenor, 'rule_based', params=params_yr
                        )
                        combo_perf_entry = params_yr.copy()
                        combo_perf_entry['annualized_pnl_pct'] = annualized_pnl_yr
                        current_year_all_combo_performance_list.append(combo_perf_entry)
                        current_year_all_rule_returns_pct.append(annualized_pnl_yr)

                        if annualized_pnl_yr > best_annualized_pnl_rule_this_year:
                            best_annualized_pnl_rule_this_year = annualized_pnl_yr
                            best_params_this_year = params_yr.copy()
                            current_best_sim_df_this_year = _sim_df_yr.copy()
        print("完成。")

        # Save all combinations for this year
        if current_year_all_combo_performance_list:
            all_combos_df_year = pd.DataFrame(current_year_all_combo_performance_list)
            all_combos_filename_year = os.path.join(OUTPUT_DIR, f'{bond_name}_{year}_all_combinations_performance.csv')
            all_combos_df_year.to_csv(all_combos_filename_year, index=False, encoding='utf-8-sig')
            print(f"  已将年份 {year} 所有组合表现保存到: {all_combos_filename_year}")
        
        median_rule_pnl_this_year = np.median(current_year_all_rule_returns_pct) if current_year_all_rule_returns_pct else np.nan
        q25_rule_pnl_this_year = np.percentile(current_year_all_rule_returns_pct, 25) if current_year_all_rule_returns_pct else np.nan
        q75_rule_pnl_this_year = np.percentile(current_year_all_rule_returns_pct, 75) if current_year_all_rule_returns_pct else np.nan
        min_rule_pnl_this_year = min(current_year_all_rule_returns_pct) if current_year_all_rule_returns_pct else np.nan

        if best_params_this_year:
             print(f"  年份 {year} 最佳规则策略: 年化 {best_annualized_pnl_rule_this_year:.2f}%, Params: {best_params_this_year}")
             if not current_best_sim_df_this_year.empty:
                 current_best_sim_df_this_year.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_best_rule_strategy_{year}_details.csv'), index=True, encoding='utf-8-sig')
        else:
            print(f"  年份 {year}: 未能找到有效的规则策略参数。")
            best_annualized_pnl_rule_this_year = np.nan 

        _bnh_sim_df_yr, _bnh_cum_pnl_yr, annualized_pnl_bnh_this_year = simulate_trading_strategy(
            df_current_year, tenor, 'buy_and_hold'
        )
        print(f"  年份 {year} '买入并持有' 基准: 年化 {annualized_pnl_bnh_this_year:.2f}%")
        if not _bnh_sim_df_yr.empty:
            _bnh_sim_df_yr.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_buy_and_hold_{year}_details.csv'), index=True, encoding='utf-8-sig')

        all_years_distribution_plot_data.append({
            'year': year,
            'all_rule_returns_pct': current_year_all_rule_returns_pct,
            'bnh_annual_pnl_pct': annualized_pnl_bnh_this_year
        })

        annual_comparison_results_summary.append({
            'year': year,
            'rule_annual_pnl_pct': best_annualized_pnl_rule_this_year, # This is the *best* rule for the year
            'bnh_annual_pnl_pct': annualized_pnl_bnh_this_year,
            'best_params_this_year': str(best_params_this_year) if best_params_this_year else None,
            'rule_outperformed': best_annualized_pnl_rule_this_year > annualized_pnl_bnh_this_year if pd.notna(best_annualized_pnl_rule_this_year) and pd.notna(annualized_pnl_bnh_this_year) else np.nan,
            'median_rule_annual_pnl_pct': median_rule_pnl_this_year,
            'q25_rule_annual_pnl_pct': q25_rule_pnl_this_year,
            'q75_rule_annual_pnl_pct': q75_rule_pnl_this_year,
            'min_rule_annual_pnl_pct': min_rule_pnl_this_year
        })

    if not annual_comparison_results_summary:
        print(f"未能生成 {bond_name} 的年度对比分析结果。")
        return [] # Return empty list for distribution plot data

    annual_summary_df = pd.DataFrame(annual_comparison_results_summary)
    annual_summary_df.to_csv(os.path.join(OUTPUT_DIR, f'{bond_name}_annual_comparative_analysis_summary.csv'), index=False, encoding='utf-8-sig')
    print(f"\n{bond_name} 年度对比分析详细结果已保存到CSV。")
    display_cols = ['year', 'min_rule_annual_pnl_pct', 'q25_rule_annual_pnl_pct', 'median_rule_annual_pnl_pct', 'q75_rule_annual_pnl_pct', 'rule_annual_pnl_pct', 'bnh_annual_pnl_pct', 'rule_outperformed']
    print(annual_summary_df[display_cols])

    # Generate historical summary comparison plot
    plot_historical_summary_comparison(annual_summary_df, bond_name)

    # Textual summary for median outperformance
    if not annual_summary_df['median_rule_annual_pnl_pct'].dropna().empty and not annual_summary_df['bnh_annual_pnl_pct'].dropna().empty:
        valid_comparisons_df = annual_summary_df.dropna(subset=['median_rule_annual_pnl_pct', 'bnh_annual_pnl_pct'])
        median_outperformed_series = valid_comparisons_df['median_rule_annual_pnl_pct'] > valid_comparisons_df['bnh_annual_pnl_pct']
        num_median_outperformed = median_outperformed_series.sum()
        num_valid_median_comparisons = len(valid_comparisons_df)

        if num_valid_median_comparisons > 0:
            print(f"\n总结 for {bond_name} (基于规则策略组合中位数):")
            print(f"  规则策略组合中位表现在 {num_median_outperformed} 年中优于 '买入并持有' 基准 (共 {num_valid_median_comparisons} 个可比年份)。")
            if num_median_outperformed > 0:
                avg_outperformance_margin = (valid_comparisons_df[median_outperformed_series]['median_rule_annual_pnl_pct'] - valid_comparisons_df[median_outperformed_series]['bnh_annual_pnl_pct']).mean()
                print(f"  在这些中位数跑赢的年份中，平均高出基准 {avg_outperformance_margin:.2f} 个百分点。")
        else:
            print(f"\n总结 for {bond_name}: 没有足够的可比年份数据来评估规则策略组合中位数相对于买入持有的表现。")
    else:
        print(f"\n总结 for {bond_name}: 未能确定规则策略组合中位数相对于买入持有的表现。")
        
    return all_years_distribution_plot_data # Return data for combined plotting

# --- 主程序 ---
def main():
    # --- 10年国债 ---
    print("处理10年期国债...")
    df_10y = load_and_preprocess_data(FILE_PATH, TEN_YEAR_BOND_CODE)
    tenor_10y = 10
    all_distribution_data_10y = []
    if df_10y is not None and not df_10y.empty:
        if 'close' in df_10y.columns and 'CLOSE' not in df_10y.columns:
             df_10y = df_10y.rename(columns={'close': 'CLOSE'})
        analyze_suddenness(df_10y, "10年期国债")
        # Run 2025 optimization and get its distribution data
        opt_period_dist_data_10y = strategy_backtest_and_optimization(df_10y, "10年期国债", tenor_10y)
        if opt_period_dist_data_10y:
            all_distribution_data_10y.append(opt_period_dist_data_10y)
        
        # Run annual analysis and get its distribution data
        annual_dist_data_10y = perform_annual_comparative_analysis(df_10y, "10年期国债", tenor_10y)
        all_distribution_data_10y.extend(annual_dist_data_10y)
        
        # Plot combined annual distributions for 10y
        plot_annual_performance_distributions(all_distribution_data_10y, "10年期国债")
    else:
        print("未能加载或处理10年期国债数据，跳过分析。")

    # --- 1年国债 ---
    print("\n处理1年期国债...")
    df_1y = load_and_preprocess_data(FILE_PATH, ONE_YEAR_BOND_CODE)
    tenor_1y = 1
    all_distribution_data_1y = []
    if df_1y is not None and not df_1y.empty:
        if 'close' in df_1y.columns and 'CLOSE' not in df_1y.columns:
            df_1y = df_1y.rename(columns={'close': 'CLOSE'})
        analyze_suddenness(df_1y, "1年期国债")
        # Run 2025 optimization and get its distribution data
        opt_period_dist_data_1y = strategy_backtest_and_optimization(df_1y, "1年期国债", tenor_1y)
        if opt_period_dist_data_1y:
            all_distribution_data_1y.append(opt_period_dist_data_1y)

        # Run annual analysis and get its distribution data
        annual_dist_data_1y = perform_annual_comparative_analysis(df_1y, "1年期国债", tenor_1y)
        all_distribution_data_1y.extend(annual_dist_data_1y)

        # Plot combined annual distributions for 1y
        plot_annual_performance_distributions(all_distribution_data_1y, "1年期国债")
    else:
        print("未能加载或处理1年期国债数据，跳过分析。")

    print("\n--- 所有分析完成 ---")
    print(f"结果已保存到 '{OUTPUT_DIR}' 目录下。")

if __name__ == '__main__':
    main() 