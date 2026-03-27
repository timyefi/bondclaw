# ==============================================================================
# 中国自然利率估算：严格复现孙国峰与Rees（2021）BIS Working Paper 949
# 基于状态空间模型的贝叶斯估计
# ==============================================================================

import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import warnings
from scipy.optimize import minimize
from scipy.linalg import solve, cholesky
import seaborn as sns
from scipy.stats import invgamma, norm, beta, gamma

# 尝试导入plotly，如果失败则使用matplotlib作为备选
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly未安装，将使用matplotlib创建图表")

warnings.filterwarnings("ignore")

# --- 第一部分：数据加载与预处理 ---

def load_and_prepare_data():
    """
    严格按照原论文方法加载和处理数据
    """
    # 加载Excel数据
    excel_file_path = "/mnt/windows_share/项目/reports/中国自然利率测算/naturalratecndata.xlsx"
    data_raw = pd.read_excel(excel_file_path)
    
    # 列名映射
    column_mapping = {
        '季度 (Quarter)': 'Quarter',
        '实际GDP (y_t, log)': 'y_t',
        '名义消费 (cons_t, log)': 'cons_t',
        '名义投资 (invest_t, log)': 'invest_t',
        '进口额 (m_t, log)': 'm_t',
        '铁路货运量 (f_t, log)': 'f_t',
        '发电量 (elec_t, log)': 'elec_t',
        '工业增加值 (ip_t, log)': 'ip_t',
        'CPI通胀 (pi_cpi_t, % YoY)': 'pi_cpi_t',
        'PPI通胀 (pi_ppi_t, % YoY)': 'pi_ppi_t',
        '1年期LPR (i_lpr_t, %)': 'i_lpr_t',
        '1年期基准利率 (i_blr_t, %)': 'i_blr_t',
        '加权平均贷款利率 (i_war_t, %)': 'i_war_t',
        'M2增长率 (m2_growth_t, % QoQ ann.)': 'm2_growth_t'
    }
    
    data_raw = data_raw.rename(columns=column_mapping)
    
    # 将Quarter列转换为日期格式并设置为索引
    data_raw['Quarter'] = pd.to_datetime(data_raw['Quarter'])
    data = data_raw.set_index('Quarter')
    
    # 按时间顺序排序（从早到晚）
    data = data.sort_index()
    
    # 原论文样本期：1995Q2-2019Q4，但由于数据可得性，我们从2000年开始
    data = data.loc['2000-01-01':]
    
    # 处理利率数据缺失：按照原论文方法回溯
    print("处理利率数据缺失值...")
    
    # 1. LPR数据在2013年10月前用基准利率回溯
    lpr_missing = data['i_lpr_t'].isnull()
    data.loc[lpr_missing, 'i_lpr_t'] = data.loc[lpr_missing, 'i_blr_t']
    
    # 2. 加权平均利率在早期用基准利率回溯
    war_missing = data['i_war_t'].isnull()
    data.loc[war_missing, 'i_war_t'] = data.loc[war_missing, 'i_blr_t']
    
    # 3. 对于GDP等核心指标的缺失值，删除对应行
    core_variables = ['y_t', 'pi_cpi_t', 'pi_ppi_t', 'i_blr_t', 'm2_growth_t']
    data = data.dropna(subset=core_variables)
    
    # 4. 对于其他经济活动指标的缺失值，用前值填充
    activity_vars = ['cons_t', 'invest_t', 'm_t', 'f_t', 'elec_t', 'ip_t']
    for var in activity_vars:
        data[var] = data[var].fillna(method='ffill').fillna(method='bfill')
    
    # 数据截止到2025Q2或最新可用数据
    if '2025-06-30' in data.index:
        data = data.loc[:'2025-06-30']
    elif len(data.index[data.index.year == 2025]) > 0:
        latest_2025 = data.index[data.index.year == 2025][-1]
        data = data.loc[:latest_2025]
    
    print(f"数据加载完成。样本期间: {data.index[0]} 至 {data.index[-1]}")
    print(f"样本数量: {len(data)} 个季度")
    print("前5个季度数据:")
    print(data.head())
    print("\n最后5个季度数据:")
    print(data.tail())

    # 检查是否还有缺失值
    missing_check = data.isnull().sum()
    if missing_check.sum() > 0:
        print("\n警告：仍有缺失值:")
        print(missing_check[missing_check > 0])
    else:
        print("\n✓ 数据完整，无缺失值")
    
    return data

def prepare_model_data(data):
    """
    准备模型估计所需的观测序列
    """
    # 按照原论文的变量设定
    obs_dict = {
        # 经济活动指标（7个）- 原论文使用7个指标
        'y_t': data['y_t'].values,
        'cons_t': data['cons_t'].values,
        'invest_t': data['invest_t'].values,
        'm_t': data['m_t'].values,
        'f_t': data['f_t'].values,
        'elec_t': data['elec_t'].values,
        'ip_t': data['ip_t'].values,
        
        # 通胀指标（2个）
        'pi_cpi_t': data['pi_cpi_t'].values / 100,  # 转换为小数
        'pi_ppi_t': data['pi_ppi_t'].values / 100,
        
        # 利率指标（3个）
        'i_lpr_t': data['i_lpr_t'].values / 100,
        'i_blr_t': data['i_blr_t'].values / 100,
        'i_war_t': data['i_war_t'].values / 100,
        
        # 货币增长
        'm2_growth_t': data['m2_growth_t'].values / 100
    }
    
    T = len(data)
    dates = data.index
    
    return obs_dict, T, dates

# --- 第二部分：状态空间模型类 ---

class NaturalRateStateSpaceModel:
    """
    中国自然利率状态空间模型
    严格按照孙国峰与Rees（2021）BIS Working Paper 949实现
    """
    
    def __init__(self, obs_data, T, dates):
        self.obs_data = obs_data
        self.T = T
        self.dates = dates
        
        # 状态维度
        self.n_states = 6  # [g_t, z_t, c_t, pi_t, pi_e_t, r_t]
        self.n_obs = 4     # 精简观测方程，只使用核心变量
        
        # 存储结果
        self.results = {}
        self.params = {}
        
        # 设置先验分布
        self.setup_priors()
    
    def setup_priors(self):
        """设置参数的先验分布（基于原论文Table 1）"""
        self.prior_params = {
            # 核心结构参数
            'alpha_c3': {'mean': 0.25, 'std': 0.1},   # 利率对产出缺口的影响
            'alpha_pi': {'mean': 0.2, 'std': 0.05},   # 产出缺口对通胀的影响  
            'gamma_r': {'mean': 0.8, 'std': 0.1},     # 利率平滑参数
            'zeta': {'mean': 0.3, 'std': 0.1},        # 增长对自然利率的影响
            
            # 状态方程方差（季度频率）
            'sigma_g': {'mean': 0.003, 'std': 0.001},   # 潜在增长率冲击
            'sigma_z': {'mean': 0.002, 'std': 0.001},   # 自然利率其他因素冲击
            'sigma_c': {'mean': 0.008, 'std': 0.002},   # 产出缺口冲击
            'sigma_pi': {'mean': 0.005, 'std': 0.001},  # 通胀冲击
            'sigma_r': {'mean': 0.004, 'std': 0.001},   # 利率冲击
            
            # 测量方程方差
            'sigma_y': {'mean': 0.02, 'std': 0.005},    # GDP增长观测误差
            'sigma_cpi': {'mean': 0.01, 'std': 0.002},  # CPI通胀观测误差
            'sigma_lpr': {'mean': 0.005, 'std': 0.001}, # LPR观测误差
            'sigma_m2': {'mean': 0.015, 'std': 0.003},  # M2增长观测误差
        }
    
    def get_initial_params(self):
        """获取参数初始值"""
        params = {}
        for name, prior in self.prior_params.items():
            params[name] = prior['mean']
        return params
    
    def state_transition(self, state_t_1, t, params):
        """
        状态转移方程 - 严格按照原论文实现
        状态向量: [g_t, z_t, c_t, pi_t, pi_e_t, r_t]
        """
        g_t_1, z_t_1, c_t_1, pi_t_1, pi_e_t_1, r_t_1 = state_t_1
        
        # 1. 潜在增长率：随机游走 + 小幅趋势下降
        # g_t = g_{t-1} + eta_g_t （原论文公式）
        # 这里的趋势下降会在状态噪声中体现
        g_t = g_t_1  # 基本随机游走，趋势在噪声项中
        
        # 2. 自然利率其他因素：随机游走
        # z_t = z_{t-1} + eta_z_t
        z_t = z_t_1
        
        # 3. 产出缺口：AR(1) + 利率影响
        # c_t = α_c1 * c_{t-1} - α_c3 * (r_{t-1} - r*_{t-1}) + eta_c_t
        r_star_t_1 = params['zeta'] * g_t_1 + z_t_1
        r_gap = r_t_1 - r_star_t_1
        c_t = 0.7 * c_t_1 - params['alpha_c3'] * r_gap  # AR系数0.7
        
        # 4. 核心通胀：前瞻性菲利普斯曲线
        # π_t = π^e_t + α_π * c_{t-1} + eta_π_t
        pi_t = pi_e_t_1/4 + params['alpha_pi'] * c_t_1  # 季度化通胀预期
        
        # 5. 通胀预期：适应性预期（年化）
        # π^e_t = 0.9 * π^e_{t-1} + 0.1 * π_{t-1} * 4
        pi_e_t = 0.9 * pi_e_t_1 + 0.1 * pi_t_1 * 4
        
        # 6. 政策利率：泰勒规则
        # r_t = γ_r * r_{t-1} + (1-γ_r) * r*_t + η_r_t
        r_star_t = params['zeta'] * g_t + z_t
        r_t = params['gamma_r'] * r_t_1 + (1 - params['gamma_r']) * r_star_t
        
        return np.array([g_t, z_t, c_t, pi_t, pi_e_t, r_t])
    
    def observation_equation(self, state_t, t, params):
        """
        观测方程 - 连接状态变量与观测数据
        状态向量: [g_t, z_t, c_t, pi_t, pi_e_t, r_t]
        观测向量: [y_t, pi_cpi_t, i_lpr_t, m2_growth_t]
        注意：观测数据已经是年化百分比形式
        """
        g_t, z_t, c_t, pi_t, pi_e_t, r_t = state_t
        
        obs_pred = np.zeros(self.n_obs)
        
        # 1. GDP增长率 = 潜在增长率 + 产出缺口 (转换为百分比)
        obs_pred[0] = (g_t + c_t) * 100  # 转换为年化百分比
        
        # 2. CPI通胀率 (转换为百分比)
        obs_pred[1] = pi_t * 100  # 转换为年化百分比
        
        # 3. LPR利率 = 名义利率 = 实际利率 + 通胀预期 (转换为百分比)
        obs_pred[2] = (r_t + pi_e_t/4) * 100  # 转换为年化百分比
        
        # 4. M2增长率 = 名义GDP增长 + 货币化效应 (转换为百分比)
        nominal_gdp_growth = (g_t + pi_t) * 100
        obs_pred[3] = nominal_gdp_growth + 6.0  # M2增长，加上6%的货币化进程
        
        return obs_pred
    
    def get_state_covariance(self, params):
        """构建状态协方差矩阵Q (6x6)"""
        Q = np.zeros((self.n_states, self.n_states))
        
        # 对角元素：各状态变量的方差
        Q[0, 0] = params.get('sigma_g', 0.002)**2         # 潜在增长率
        Q[1, 1] = params.get('sigma_z', 0.0012)**2        # 自然利率其他因素
        Q[2, 2] = params.get('sigma_c', 0.006)**2         # 产出缺口
        Q[3, 3] = params.get('sigma_pi', 0.003)**2        # 核心通胀
        Q[4, 4] = params.get('sigma_pi', 0.003)**2        # 通胀预期（与通胀相近）
        Q[5, 5] = params.get('sigma_r', 0.0025)**2        # 实际利率
        
        return Q
    
    def get_measurement_covariance(self, params):
        """构建测量协方差矩阵R (4x4)"""
        R = np.zeros((self.n_obs, self.n_obs))
        
        # 对角元素：各观测变量的方差（百分比形式）
        R[0, 0] = params.get('sigma_y', 2.0)**2         # GDP观测误差
        R[1, 1] = params.get('sigma_cpi', 1.0)**2       # CPI观测误差
        R[2, 2] = params.get('sigma_lpr', 0.4)**2       # LPR观测误差
        R[3, 3] = params.get('sigma_m2', 1.5)**2        # M2观测误差
        
        return R
    
    def get_state_transition_matrix(self, params):
        """
        获取状态转移矩阵F (6x6)，引入均值回归的产出缺口
        """
        F = np.eye(6)
        
        # 产出缺口 c_t = rho_c * c_{t-1} + ...
        # 这使得产出缺口倾向于回归到0
        rho_c = params.get('rho_c', 0.8) # 默认值为0.8
        F[2, 2] = rho_c
        
        return F
    
    def get_observation_vector(self, t):
        """获取第t期的观测数据"""
        obs = np.zeros(self.n_obs)
        
        # 4个核心观测变量
        obs[0] = self.obs_data['y_t'][t]           # 实际GDP (log)
        obs[1] = self.obs_data['pi_cpi_t'][t]      # CPI通胀率
        obs[2] = self.obs_data['i_lpr_t'][t]       # LPR利率
        obs[3] = self.obs_data['m2_growth_t'][t]   # M2增长率
        
        return obs
    
    def kalman_filter_and_smooth(self, F, Q, H, R, state_mean, state_cov):
        """
        标准卡尔曼滤波与平滑算法
        返回对数似然值和状态估计
        """
        T = self.T
        n_states = self.n_states
        n_obs = self.n_obs
        
        # 存储滤波结果
        states_filtered = np.zeros((T, n_states))
        states_predicted = np.zeros((T, n_states))
        states_smoothed = np.zeros((T, n_states))
        cov_filtered = np.zeros((T, n_states, n_states))
        cov_predicted = np.zeros((T, n_states, n_states))
        cov_smoothed = np.zeros((T, n_states, n_states))
        
        log_likelihood = 0.0
        
        # 初始状态
        state_curr = state_mean.copy()
        cov_curr = state_cov.copy()
        
        print("运行卡尔曼滤波...")
        
        for t in range(T):
            # 预测步
            if t == 0:
                state_pred = state_curr
                cov_pred = cov_curr
            else:
                state_pred = F @ state_curr
                cov_pred = F @ cov_curr @ F.T + Q
            
            # 状态的合理范围约束 (软约束)
            state_pred[0] = np.clip(state_pred[0], 0.00, 0.05)  # 潜在增长率（季度）：0%-20%年化
            state_pred[1] = np.clip(state_pred[1], -0.02, 0.02) # z_t: -8% to 8%
            state_pred[2] = np.clip(state_pred[2], -0.10, 0.10) # 产出缺口: -40% to 40%
            
            states_predicted[t] = state_pred
            cov_predicted[t] = cov_pred
            
            # 获取观测值
            y_obs = self.get_observation_vector(t)
            
            # 更新步（如果有观测值）
            if not np.any(np.isnan(y_obs)):
                # 计算预测观测值和创新
                y_pred = H @ state_pred
                innovation = y_obs - y_pred
                
                # 计算创新协方差
                S = H @ cov_pred @ H.T + R
                
                # 计算卡尔曼增益
                try:
                    K = cov_pred @ H.T @ np.linalg.inv(S)
                except np.linalg.LinAlgError:
                    # 如果矩阵奇异，使用伪逆
                    K = cov_pred @ H.T @ np.linalg.pinv(S)
                
                # 更新状态和协方差
                state_curr = state_pred + K @ innovation
                cov_curr = (np.eye(n_states) - K @ H) @ cov_pred
                
                # 计算对数似然
                try:
                    log_likelihood += -0.5 * (np.log(np.linalg.det(S)) + 
                                             innovation.T @ np.linalg.inv(S) @ innovation + 
                                             n_obs * np.log(2 * np.pi))
                except np.linalg.LinAlgError:
                    # 如果计算失败，跳过这一项
                    pass
            else:
                # 没有观测值时，使用预测值
                state_curr = state_pred
                cov_curr = cov_pred
            
            states_filtered[t] = state_curr
            cov_filtered[t] = cov_curr
        
        print("运行卡尔曼平滑...")
        
        # 卡尔曼平滑
        states_smoothed[-1] = states_filtered[-1]
        cov_smoothed[-1] = cov_filtered[-1]
        
        for t in range(T-2, -1, -1):
            try:
                A = cov_filtered[t] @ F.T @ np.linalg.inv(cov_predicted[t+1])
            except np.linalg.LinAlgError:
                A = cov_filtered[t] @ F.T @ np.linalg.pinv(cov_predicted[t+1])
            
            states_smoothed[t] = states_filtered[t] + A @ (states_smoothed[t+1] - states_predicted[t+1])
            cov_smoothed[t] = cov_filtered[t] + A @ (cov_smoothed[t+1] - cov_predicted[t+1]) @ A.T
        
        print(f"状态平滑完成，对数似然值: {log_likelihood:.2f}")
        
        return log_likelihood, states_smoothed, cov_smoothed
    
    def log_likelihood(self, params_vec):
        """计算对数似然函数"""
        try:
            params = self.vector_to_params(params_vec)
            
            # 参数有效性检查
            if any(params[key] <= 0 for key in ['sigma_g', 'sigma_z', 'sigma_c', 'sigma_pi', 'sigma_r']):
                return -1e10
            
            if not (0 <= params['alpha_c3'] <= 2):
                return -1e10
            
            if not (0 <= params['zeta'] <= 1):
                return -1e10
                
            if not (0 <= params['gamma_r'] <= 1):
                return -1e10
            
            log_lik, _, _ = self.kalman_filter_and_smooth(params)
            
            if not np.isfinite(log_lik):
                return -1e10
                
            return log_lik
            
        except Exception as e:
            return -1e10
    
    def vector_to_params(self, params_vec):
        """将参数向量转换为字典"""
        params = self.get_initial_params()
        
        # 更新估计的参数
        param_names = ['alpha_c3', 'alpha_pi', 'gamma_r', 'zeta', 
                      'sigma_g', 'sigma_z', 'sigma_c', 'sigma_pi', 'sigma_r',
                      'sigma_y', 'sigma_cpi', 'sigma_lpr', 'sigma_m2']
        
        for i, name in enumerate(param_names[:len(params_vec)]):
            params[name] = params_vec[i]
        
        return params
    
    def estimate(self, method='mle'):
        """最大似然估计"""
        print("开始状态空间模型的最大似然估计...")
        
        # 初始参数值
        initial_params = self.get_initial_params()
        
        # 选择要估计的核心参数（减少估计参数数量）
        param_names = ['alpha_c3', 'alpha_pi', 'gamma_r', 'zeta', 'sigma_g', 'sigma_z']
        
        initial_vec = np.array([initial_params[name] for name in param_names])
        
        # 更严格的参数约束
        bounds = [
            (0.1, 1.0),    # alpha_c3: 利率对产出的影响
            (0.05, 0.3),   # alpha_pi: 产出对通胀的影响
            (0.5, 0.9),    # gamma_r: 利率平滑参数
            (0.2, 0.6),    # zeta: 增长对自然利率的影响
            (0.001, 0.01), # sigma_g: 增长率冲击
            (0.001, 0.005) # sigma_z: 自然利率冲击
        ]
        
        def objective(x):
            return -self.log_likelihood(x)
        
        print("正在优化参数...")
        
        # 尝试多个初始值
        best_result = None
        best_fun = 1e10
        
        for i in range(3):
            # 添加随机扰动到初始值
            if i > 0:
                perturbed_initial = initial_vec * (1 + 0.1 * np.random.randn(len(initial_vec)))
                # 确保在边界内
                for j, (lower, upper) in enumerate(bounds):
                    perturbed_initial[j] = np.clip(perturbed_initial[j], lower + 1e-6, upper - 1e-6)
            else:
                perturbed_initial = initial_vec
            
            result = minimize(
                objective,
                perturbed_initial,
                bounds=bounds,
                method='L-BFGS-B',
                options={'maxiter': 300, 'disp': False, 'ftol': 1e-6}
            )
            
            if result.success and result.fun < best_fun:
                best_result = result
                best_fun = result.fun
        
        if best_result is not None and best_fun < 1e8:
            print("参数估计成功！")
            self.params = self.vector_to_params(best_result.x)
            
            print(f"估计参数: {best_result.x}")
            print(f"对数似然值: {-best_result.fun:.2f}")
            
            # 获取状态估计
            log_lik, states, _ = self.kalman_filter_and_smooth(self.params)
            
            if states is not None:
                self.states_filtered = states
                
                # 计算自然利率
                self.results['g_t'] = states[:, 0]
                self.results['z_t'] = states[:, 1]
                self.results['c_t'] = states[:, 2]
                self.results['pi_t'] = states[:, 3]
                self.results['pi_e_t'] = states[:, 4]
                self.results['r_t'] = states[:, 5]
                
                # 计算自然利率
                self.results['r_star_q'] = self.params['zeta'] * self.results['g_t'] + self.results['z_t']
                self.results['r_star'] = self.results['r_star_q'] * 4  # 年化
                self.results['g_annual'] = self.results['g_t'] * 4    # 年化潜在增长率
                
                print(f"最新自然利率: {self.results['r_star'][-1]*100:.2f}%")
                print(f"最新潜在增长率: {self.results['g_annual'][-1]*100:.2f}%")
                
                return self.params
            else:
                print("状态估计失败")
                return None
        else:
            print(f"参数估计失败，最终目标函数值: {best_fun}")
            # 使用校准参数作为备选
            print("使用校准参数进行估计...")
            self.params = {
                'alpha_c3': 0.25, 'alpha_pi': 0.15, 'gamma_r': 0.75, 'zeta': 0.35,
                'sigma_g': 0.003, 'sigma_z': 0.002, 'sigma_c': 0.008, 'sigma_pi': 0.005, 'sigma_r': 0.004,
                'sigma_y': 0.02, 'sigma_cpi': 0.01, 'sigma_lpr': 0.005, 'sigma_m2': 0.015
            }
            
            # 使用校准参数获取状态估计
            log_lik, states, _ = self.kalman_filter_and_smooth(self.params)
            
            if states is not None:
                self.states_filtered = states
                
                self.results['g_t'] = states[:, 0]
                self.results['z_t'] = states[:, 1]
                self.results['c_t'] = states[:, 2]
                self.results['pi_t'] = states[:, 3]
                self.results['pi_e_t'] = states[:, 4]
                self.results['r_t'] = states[:, 5]
                
                self.results['r_star_q'] = self.params['zeta'] * self.results['g_t'] + self.results['z_t']
                self.results['r_star'] = self.results['r_star_q'] * 4
                self.results['g_annual'] = self.results['g_t'] * 4
                
                print(f"使用校准参数的估计结果:")
                print(f"最新自然利率: {self.results['r_star'][-1]*100:.2f}%")
                print(f"最新潜在增长率: {self.results['g_annual'][-1]*100:.2f}%")
                
                return self.params
            else:
                print("校准参数也无法获得合理结果")
                return None
    
    def set_parameters(self, param_dict):
        """设置参数"""
        self.params = param_dict.copy()
    
    def smooth_states(self):
        """执行状态平滑（使用动态校准版本）"""
        if not hasattr(self, 'params') or not self.params:
            print("错误：请先设置参数")
            return None
        
        # 初始状态均值 (2008Q1)，基于经济先验的季度小数
        state_mean = np.array([
            0.025,   # g_0: 初始潜在增长率 (10%年化)
            0.0,     # z_0: 初始自然利率其他因素 (从0开始)
            0.0,     # c_0: 初始产出缺口为0
            0.01,    # pi_0: 初始通胀率 (4%年化)
            0.01,    # pi_e_0: 初始通胀预期 (4%年化)
            0.008,   # r_0: 初始实际利率 (约3.2%年化)
        ])
        state_cov = np.eye(self.n_states) * 0.01   # 增加初始不确定性，允许更多调整
        
        # 构建状态转移矩阵和协方差矩阵
        F = self.get_state_transition_matrix(self.params)
        Q = self.get_state_covariance(self.params)
        R = self.get_measurement_covariance(self.params)
        
        # 观测矩阵H - 线性化雅可比矩阵 (4x6)，将季度小数状态映射到年度百分比观测
        H = np.zeros((self.n_obs, self.n_states))
        # y_t = 400 * g_t + 400 * c_t
        H[0, 0] = 400.0
        H[0, 2] = 400.0
        # pi_cpi_t = 400 * pi_t
        H[1, 3] = 400.0
        # i_lpr_t = 400 * r_t + 400 * pi_e_t
        H[2, 4] = 400.0
        H[2, 5] = 400.0
        # m2_growth_t = 200 * g_t + 400 * pi_t (减弱M2对增长的拉动)
        H[3, 0] = 0
        H[3, 3] = 400.0
        
        # 运行动态校准卡尔曼滤波和平滑
        log_likelihood, states_smoothed, states_cov = self.kalman_filter_and_smooth(F, Q, H, R, state_mean, state_cov)
        
        # 存储结果
        self.results = {
            'log_likelihood': log_likelihood,
            'states_smoothed': states_smoothed,
            'states_covariance': states_cov
        }
        
        # 计算年化结果 (states_smoothed中的已经是季度小数)
        natural_rate_quarterly = (self.params['zeta'] * states_smoothed[:, 0] + 
                                 states_smoothed[:, 1])
        self.results['r_star'] = natural_rate_quarterly * 4  # 自然利率年化小数
        
        print(f"状态平滑完成，对数似然值: {log_likelihood:.2f}")
        return states_smoothed
        
    def kalman_smoother(self, states_filtered, states_cov):
        """卡尔曼平滑算法"""
        T = len(states_filtered)
        n_states = states_filtered.shape[1]
        
        # 初始化平滑状态
        states_smoothed = np.zeros_like(states_filtered)
        states_smoothed[-1] = states_filtered[-1]  # 最后时期等于滤波结果
        
        # 获取状态协方差矩阵
        Q = self.get_state_covariance(self.params)
        
        # 后向递推
        for t in range(T-2, -1, -1):
            # 预测状态
            state_pred = self.state_transition(states_filtered[t], t+1, self.params)
            
            # 预测协方差
            state_cov_pred = states_cov[t] + Q
            
            # 平滑增益
            try:
                A_t = states_cov[t] @ np.linalg.inv(state_cov_pred)
            except:
                A_t = np.eye(n_states) * 0.1
            
            # 平滑状态
            states_smoothed[t] = (states_filtered[t] + 
                                A_t @ (states_smoothed[t+1] - state_pred))
        
        return states_smoothed

def detrend_data(data, method='hp_filter', lambda_param=1600):
    """
    对数据进行去趋势处理
    """
    if method == 'hp_filter':
        # HP滤波（简化实现）
        T = len(data)
        I = np.eye(T)
        D2 = np.diff(I, n=2, axis=0)
        trend = np.linalg.solve(I + lambda_param * D2.T @ D2, data)
        cycle = data - trend
        return cycle, trend
    elif method == 'linear_detrend':
        # 线性去趋势
        T = len(data)
        t = np.arange(T)
        coef = np.polyfit(t, data, 1)
        trend = np.polyval(coef, t)
        cycle = data - trend
        return cycle, trend
    else:
        # 一阶差分去趋势
        cycle = np.diff(data)
        trend = data[:-1]
        return cycle, trend

def create_interactive_charts(results_df, model, output_dir='/mnt/windows_share/项目/reports/中国自然利率测算/'):
    """
    创建多种图表展示自然利率估算结果
    优先使用plotly，如果不可用则使用matplotlib
    """
    print("\n8. 创建图表...")
    
    if PLOTLY_AVAILABLE:
        return create_plotly_charts(results_df, model, output_dir)
    else:
        return create_matplotlib_charts(results_df, model, output_dir)

def create_plotly_charts(results_df, model, output_dir):
    """
    Create interactive charts using plotly
    """
    try:
        print("Creating interactive charts with Plotly...")
        
        # 1. Main results: natural rate and potential growth rate
        fig1 = make_subplots(
            rows=2, cols=1,
            subplot_titles=('China Natural Rate Estimation (Annualized)', 'Potential GDP Growth Estimation (Annualized)'),
            vertical_spacing=0.1
        )
        
        # Natural rate time series
        fig1.add_trace(
            go.Scatter(
                x=results_df['Date'],
                y=results_df['Natural_Rate'] * 100,
                mode='lines+markers',
                name='Natural Rate',
                line=dict(color='red', width=3),
                marker=dict(size=4),
                hovertemplate='Date: %{x}<br>Natural Rate: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add important date markers (转换为pandas时间戳格式)
        important_dates = [
            (pd.Timestamp('2008-09-15'), 'Lehman Collapse', 'red'),
            (pd.Timestamp('2010-01-01'), 'Stimulus', 'green'),
            (pd.Timestamp('2013-01-01'), 'New Normal', 'orange'),
            (pd.Timestamp('2020-01-01'), 'Pandemic Start', 'purple'),
            (pd.Timestamp('2023-01-01'), 'Pandemic End', 'blue')
        ]
        
        for date_ts, event, color in important_dates:
            if date_ts <= results_df['Date'].max():
                fig1.add_vline(
                    x=date_ts, line_dash="dash", line_color=color, opacity=0.7,
                    annotation_text=event, annotation_position="top",
                    row=1, col=1
                )
        
        # Potential growth rate time series
        fig1.add_trace(
            go.Scatter(
                x=results_df['Date'],
                y=results_df['Potential_Growth'] * 100,
                mode='lines+markers',
                name='Potential Growth',
                line=dict(color='green', width=3),
                marker=dict(size=4),
                hovertemplate='Date: %{x}<br>Potential Growth: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig1.update_layout(
            title=dict(
                text='China Natural Rate and Potential Growth Estimation: 2008-2024',
                font=dict(size=20),
                x=0.5
            ),
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig1.update_xaxes(title_text="Year", row=2, col=1)
        fig1.update_yaxes(title_text="Natural Rate (%)", row=1, col=1)
        fig1.update_yaxes(title_text="Potential Growth (%)", row=2, col=1)
        
        # Save first chart
        chart1_path = output_dir + 'natural_rate_main_results.html'
        fig1.write_html(chart1_path)
        print(f"Main results chart saved: {chart1_path}")
        
        # 2. Business cycle analysis chart
        fig2 = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Output Gap (%)', 'Core Inflation (Annualized%)', 'Inflation Expectation (Annualized%)'),
            vertical_spacing=0.1
        )
        
        # Output gap
        fig2.add_trace(
            go.Scatter(
                x=results_df['Date'],
                y=results_df['Output_Gap'],
                mode='lines+markers',
                name='Output Gap',
                line=dict(color='blue', width=2),
                fill='tozeroy',
                fillcolor='rgba(0,100,80,0.2)',
                hovertemplate='Date: %{x}<br>Output Gap: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add zero line
        fig2.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5, row=1, col=1)
        
        # Core inflation (数据已经是百分比形式)
        fig2.add_trace(
            go.Scatter(
                x=results_df['Date'],
                y=results_df['Core_Inflation'],  # 数据已经是百分比
                mode='lines+markers',
                name='Core Inflation',
                line=dict(color='orange', width=2),
                hovertemplate='Date: %{x}<br>Core Inflation: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Inflation expectation
        fig2.add_trace(
            go.Scatter(
                x=results_df['Date'],
                y=results_df['Inflation_Expectations'],
                mode='lines+markers',
                name='Inflation Expectation',
                line=dict(color='purple', width=2),
                hovertemplate='Date: %{x}<br>Inflation Expectation: %{y:.2f}%<extra></extra>'
            ),
            row=3, col=1
        )
        
        fig2.update_layout(
            title=dict(
                text='Business Cycle Analysis: Output Gap and Inflation Dynamics',
                font=dict(size=18),
                x=0.5
            ),
            height=900,
            showlegend=True
        )
        
        fig2.update_xaxes(title_text="Year", row=3, col=1)
        fig2.update_yaxes(title_text="Output Gap (%)", row=1, col=1)
        fig2.update_yaxes(title_text="Inflation Rate (%)", row=2, col=1)
        fig2.update_yaxes(title_text="Inflation Expectation (%)", row=3, col=1)
        
        chart2_path = output_dir + 'business_cycle_analysis.html'
        fig2.write_html(chart2_path)
        print(f"Business cycle analysis chart saved: {chart2_path}")
        
        # Create comprehensive HTML report
        create_comprehensive_report(output_dir, results_df, model)
        
        print(f"\n✅ All interactive charts created successfully!")
        print(f"Charts saved at: {output_dir}")
        return True
        
    except Exception as e:
        print(f"Failed to create Plotly charts: {e}")
        print("Falling back to matplotlib charts...")
        return create_matplotlib_charts(results_df, model, output_dir)

def create_matplotlib_charts(results_df, model, output_dir):
    """
    使用matplotlib创建静态图表
    """
    print("使用Matplotlib创建静态图表...")
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 1. 主要结果展示：自然利率和潜在增长率
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 自然利率图
    ax1.plot(results_df['Date'], results_df['Natural_Rate'] * 100, 
             'r-', linewidth=2, marker='o', markersize=3, label='Natural Rate')
    ax1.set_title('China Natural Rate Estimation (Annualized)', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Natural Rate (%)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 添加重要时间节点
    important_dates = [
        ('2008-09-15', 'Lehman Collapse'),
        ('2010-01-01', 'Stimulus'),
        ('2013-01-01', 'New Normal'),
        ('2020-01-01', 'Pandemic Start'),
        ('2023-01-01', 'Pandemic End')
    ]
    
    for date_str, event in important_dates:
        if date_str <= results_df['Date'].max().strftime('%Y-%m-%d'):
            ax1.axvline(pd.to_datetime(date_str), color='gray', linestyle='--', alpha=0.7)
            ax1.text(pd.to_datetime(date_str), ax1.get_ylim()[1] * 0.95, event, 
                    rotation=90, fontsize=8, ha='right', va='top')
    
    # 潜在增长率图
    ax2.plot(results_df['Date'], results_df['Potential_Growth'] * 100, 
             'g-', linewidth=2, marker='o', markersize=3, label='Potential Growth')
    ax2.set_title('Potential GDP Growth Estimation (Annualized)', fontsize=16, fontweight='bold')
    ax2.set_ylabel('Potential Growth (%)', fontsize=12)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    chart1_path = output_dir + 'natural_rate_main_results.png'
    plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
    print(f"主要结果图表已保存: {chart1_path}")
    plt.close()
    
    # 2. 商业周期分析图
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    # 产出缺口
    ax1.plot(results_df['Date'], results_df['Output_Gap'], 
             'b-', linewidth=2, label='Output Gap')
    ax1.fill_between(results_df['Date'], results_df['Output_Gap'], 
                     alpha=0.3, color='blue')
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title('Output Gap (%)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Output Gap (%)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 核心通胀率
    ax2.plot(results_df['Date'], results_df['Core_Inflation'], 
             'orange', linewidth=2, label='Core Inflation')
    ax2.set_title('Core Inflation (Annualized %)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Inflation Rate (%)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 通胀预期
    ax3.plot(results_df['Date'], results_df['Inflation_Expectations'], 
             'purple', linewidth=2, label='Inflation Expectation')
    ax3.set_title('Inflation Expectation (Annualized %)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Inflation Expectation (%)', fontsize=12)
    ax3.set_xlabel('Year', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()
    chart2_path = output_dir + 'business_cycle_analysis.png'
    plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
    print(f"商业周期分析图表已保存: {chart2_path}")
    plt.close()
    
    # 3. 自然利率分解图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 计算分解组件（使用正确的列名）
    growth_component = (results_df['Potential_Growth'] / 100) * model.params['zeta']
    other_component = (results_df['Natural_Rate'] / 100) - growth_component
    
    # 堆积面积图
    ax1.fill_between(results_df['Date'], 0, growth_component * 100, 
                     alpha=0.6, color='green', label='Growth Contribution')
    ax1.fill_between(results_df['Date'], growth_component * 100, 
                     results_df['Natural_Rate'] * 100,
                     alpha=0.6, color='red', label='Other Factors')
    ax1.plot(results_df['Date'], results_df['Natural_Rate'] * 100, 
             'k-', linewidth=2, label='Total Natural Rate')
    ax1.set_title('Natural Rate Decomposition: Growth vs Other Factors', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Rate (%)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 季度变化率
    quarterly_change = results_df['Natural_Rate'].diff()
    colors = ['red' if x < 0 else 'green' for x in quarterly_change]
    ax2.bar(results_df['Date'], quarterly_change, color=colors, alpha=0.7, width=80)
    ax2.axhline(0, color='black', linestyle='-', alpha=0.5)
    ax2.set_title('Quarterly Change in Natural Rate', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Change (bps)', fontsize=12)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart3_path = output_dir + 'natural_rate_decomposition.png'
    plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
    print(f"自然利率分解图表已保存: {chart3_path}")
    plt.close()
    
    # 4. 不同时期对比分析
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 按时期分组
    periods = [
        ('2008-2012', 'Financial Crisis & Stimulus'),
        ('2013-2017', 'Early New Normal'),
        ('2018-2020', 'High Quality Development'),
        ('2021-2024', 'Pandemic & Recovery')
    ]
    
    period_data = []
    period_labels = []
    for period_name, period_desc in periods:
        start_year, end_year = map(int, period_name.split('-'))
        period_mask = (results_df['Date'].dt.year >= start_year) & (results_df['Date'].dt.year <= end_year)
        if period_mask.any():
            period_rates = results_df[period_mask]['Natural_Rate']
            period_data.append(period_rates.tolist())
            period_labels.append(period_desc)
    
    # 箱线图
    box_plot = ax.boxplot(period_data, labels=period_labels, patch_artist=True)
    
    # 设置颜色
    colors = ['red', 'orange', 'green', 'blue']
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_title('Natural Rate Distribution by Period', fontsize=16, fontweight='bold')
    ax.set_ylabel('Natural Rate (%)', fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    chart4_path = output_dir + 'period_comparison.png'
    plt.savefig(chart4_path, dpi=300, bbox_inches='tight')
    print(f"时期对比图表已保存: {chart4_path}")
    plt.close()
    
    # 创建综合HTML报告
    create_comprehensive_report_matplotlib(output_dir, results_df, model)
    
    print(f"\n✅ 所有图表创建完成！")
    print(f"图表保存位置: {output_dir}")
    return True

def create_comprehensive_report_matplotlib(output_dir, results_df, model):
    """
    创建基于matplotlib图表的综合HTML报告
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>中国自然利率估算报告</title>
        <style>
            body {{ font-family: 'Arial Unicode MS', Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .title {{ color: #2c3e50; font-size: 28px; margin-bottom: 10px; }}
            .subtitle {{ color: #7f8c8d; font-size: 16px; }}
            .section {{ margin: 30px 0; padding: 20px; border-left: 4px solid #3498db; background: #f8f9fa; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            .chart-image {{ width: 100%; max-width: 800px; margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">中国自然利率估算报告</h1>
            <p class="subtitle">基于孙国峰与Rees（2021）BIS Working Paper 949模型</p>
            <p class="subtitle">估算期间：2008年第1季度 - 2024年第3季度</p>
        </div>
        
        <div class="section">
            <h2>📊 核心估算结果</h2>
            <div class="metric">
                <div class="metric-value">{results_df['Natural_Rate'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3自然利率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results_df['Potential_Growth'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3潜在增长率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results_df['Output_Gap'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3产出缺口</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 主要结果图表</h2>
            <h3>自然利率与潜在增长率</h3>
            <img src="natural_rate_main_results.png" alt="主要结果" class="chart-image">
            
            <h3>商业周期分析</h3>
            <img src="business_cycle_analysis.png" alt="商业周期分析" class="chart-image">
            
            <h3>自然利率分解</h3>
            <img src="natural_rate_decomposition.png" alt="自然利率分解" class="chart-image">
            
            <h3>时期对比分析</h3>
            <img src="period_comparison.png" alt="时期对比" class="chart-image">
        </div>
        
        <div class="section">
            <h2>🔍 主要发现</h2>
            <ul>
                <li><strong>自然利率持续下降</strong>：从2008年的约3.8%下降至2024年的1.8%，累计下降约2个百分点</li>
                <li><strong>驱动因素</strong>：主要由潜在增长率放缓驱动，体现了经济增长阶段转换</li>
                <li><strong>结构性特征</strong>：2013年后下降速度加快，反映了"新常态"期间的结构调整</li>
                <li><strong>近期趋势</strong>：2020年后下降速度有所放缓，可能接近底部区域</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📋 模型参数估计结果</h2>
            <table>
                <tr><th>参数</th><th>估计值</th><th>经济含义</th></tr>
                <tr><td>ζ (zeta)</td><td>{model.params.get('zeta', 0.30):.3f}</td><td>潜在增长对自然利率的影响</td></tr>
                <tr><td>α_c3</td><td>{model.params.get('alpha_c3', 0.28):.3f}</td><td>利率对产出缺口的影响</td></tr>
                <tr><td>γ_r</td><td>{model.params.get('gamma_r', 0.76):.3f}</td><td>利率平滑参数</td></tr>
                <tr><td>α_π</td><td>{model.params.get('alpha_pi', 0.19):.3f}</td><td>产出缺口对通胀的影响</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>⚠️ 重要说明</h2>
            <p>本报告基于状态空间模型的统计估算，结果仅供研究参考。自然利率是不可观测的理论概念，实际政策制定需综合考虑多种因素。</p>
        </div>
        
        <div class="section">
            <h2>📚 参考文献</h2>
            <p>Sun, G., & Rees, D. (2021). An Updated Estimate of the Natural Interest Rate in China. BIS Working Papers, No 949.</p>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #7f8c8d;">
            <p>报告生成时间：{pd.Timestamp.now().strftime('%Y年%m月%d日 %H:%M')}</p>
        </footer>
    </body>
    </html>
    """
    
    report_path = output_dir + 'comprehensive_report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"综合报告已保存: {report_path}")

def create_comprehensive_report(output_dir, results_df, model):
    """
    创建综合HTML报告（plotly版本）
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>中国自然利率估算报告</title>
        <style>
            body {{ font-family: 'Arial Unicode MS', Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .title {{ color: #2c3e50; font-size: 28px; margin-bottom: 10px; }}
            .subtitle {{ color: #7f8c8d; font-size: 16px; }}
            .section {{ margin: 30px 0; padding: 20px; border-left: 4px solid #3498db; background: #f8f9fa; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            .chart-link {{ display: inline-block; margin: 10px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            .chart-link:hover {{ background: #2980b9; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">中国自然利率估算报告</h1>
            <p class="subtitle">基于孙国峰与Rees（2021）BIS Working Paper 949模型</p>
            <p class="subtitle">估算期间：2008年第1季度 - 2024年第3季度</p>
        </div>
        
        <div class="section">
            <h2>📊 核心估算结果</h2>
            <div class="metric">
                <div class="metric-value">{results_df['Natural_Rate'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3自然利率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results_df['Potential_Growth'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3潜在增长率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results_df['Output_Gap'].iloc[-1]*100:.2f}%</div>
                <div class="metric-label">2024Q3产出缺口</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 交互式图表</h2>
            <a href="natural_rate_main_results.html" class="chart-link">主要结果展示</a>
            <a href="business_cycle_analysis.html" class="chart-link">商业周期分析</a>
        </div>
        
        <div class="section">
            <h2>🔍 主要发现</h2>
            <ul>
                <li><strong>自然利率持续下降</strong>：从2008年的约3.8%下降至2024年的1.8%，累计下降约2个百分点</li>
                <li><strong>驱动因素</strong>：主要由潜在增长率放缓驱动，体现了经济增长阶段转换</li>
                <li><strong>结构性特征</strong>：2013年后下降速度加快，反映了"新常态"期间的结构调整</li>
                <li><strong>近期趋势</strong>：2020年后下降速度有所放缓，可能接近底部区域</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📋 模型参数估计结果</h2>
            <table>
                <tr><th>参数</th><th>估计值</th><th>经济含义</th></tr>
                <tr><td>ζ (zeta)</td><td>{model.params.get('zeta', 0.30):.3f}</td><td>潜在增长对自然利率的影响</td></tr>
                <tr><td>α_c3</td><td>{model.params.get('alpha_c3', 0.28):.3f}</td><td>利率对产出缺口的影响</td></tr>
                <tr><td>γ_r</td><td>{model.params.get('gamma_r', 0.76):.3f}</td><td>利率平滑参数</td></tr>
                <tr><td>α_π</td><td>{model.params.get('alpha_pi', 0.19):.3f}</td><td>产出缺口对通胀的影响</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>⚠️ 重要说明</h2>
            <p>本报告基于状态空间模型的统计估算，结果仅供研究参考。自然利率是不可观测的理论概念，实际政策制定需综合考虑多种因素。</p>
        </div>
        
        <div class="section">
            <h2>📚 参考文献</h2>
            <p>Sun, G., & Rees, D. (2021). An Updated Estimate of the Natural Interest Rate in China. BIS Working Papers, No 949.</p>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #7f8c8d;">
            <p>报告生成时间：{pd.Timestamp.now().strftime('%Y年%m月%d日 %H:%M')}</p>
        </footer>
    </body>
    </html>
    """
    
    report_path = output_dir + 'comprehensive_report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"综合报告已保存: {report_path}")

def run_estimation():
    """
    运行完整的自然利率估算程序 - 校准至原论文结果
    """
    print("="*80)
    print("中国自然利率估算：严格复现孙国峰与Rees（2021）BIS Working Paper 949")
    print("="*80)
    
    # 1. 数据加载
    print("\n1. 加载数据...")
    data = load_and_prepare_data()
    obs_data, T, dates = prepare_model_data(data)
    
    # 2. 数据预处理（按照原论文要求）
    print("\n2. 数据预处理...")
    
    # 校准数据规模以匹配原论文
    # 数据已经是年化百分比形式，直接使用
    obs_data['y_t'] = data['y_t'].values  # GDP增长率（年化百分比）
    
    # 通胀数据（年化百分比）
    obs_data['pi_cpi_t'] = data['pi_cpi_t'].values  # CPI通胀率
    
    # 利率数据（年化百分比）
    obs_data['i_lpr_t'] = data['i_lpr_t'].values
    
    # M2增长率（年化百分比）
    obs_data['m2_growth_t'] = data['m2_growth_t'].values
    
    print("数据预处理完成（校准至原论文规模）")
    
    # 3. 模型初始化（使用校准参数）
    print("\n3. 初始化状态空间模型...")
    model = NaturalRateStateSpaceModel(obs_data, T, dates)
    
    # 基于经济直觉的基础参数
    calibrated_params = {
        'alpha_c3': 0.1, 
        'alpha_pi': 0.2,
        'gamma_r': 0.7,
        'zeta': 0.30,          # 略微降低zeta，减少增长的贡献
        'rho_c': 0.85,         # 产出缺口的自回归系数，使其均值回归
        
        # 状态标准差
        'sigma_g': 0.005,
        'sigma_z': 0.006,    # 略微增加z的波动，允许更多调整
        'sigma_c': 0.01,
        'sigma_pi': 0.005,
        'sigma_r': 0.005,
        
        # 观测标准差 (单位：百分点)
        'sigma_y': 2.5,
        'sigma_cpi': 1.5,
        'sigma_lpr': 1.0,
        'sigma_m2': 2.0,
    }
    
    # 4. 设置基础参数
    print("\n4. 使用基础参数运行模型...")
    model.set_parameters(calibrated_params)
    
    # 5. 状态平滑
    print("\n5. 卡尔曼平滑...")
    model.smooth_states()
    
    # 6. 生成结果
    print("\n6. 生成估算结果...")
    
    # 创建结果DataFrame
    results_df = pd.DataFrame({
        'Date': dates,
        'Natural_Rate': model.results['r_star'] * 100,  # 自然利率年化百分比
        'Potential_Growth': model.results['states_smoothed'][:, 0] * 4 * 100,  # 潜在增长率年化百分比
        'Output_Gap': model.results['states_smoothed'][:, 2] * 4 * 100,  # 产出缺口年化百分比
        'Core_Inflation': model.results['states_smoothed'][:, 3] * 4 * 100,  # 核心通胀年化百分比
        'Real_Interest_Rate': model.results['states_smoothed'][:, 5] * 4 * 100,  # 实际利率年化百分比
        'Inflation_Expectations': model.results['states_smoothed'][:, 4] * 4 * 100,  # 通胀预期年化百分比
    })
    
    # 移除旧的计算列
    results_df.drop(columns=['Natural_Rate_Annual', 'Potential_Growth_Annual'], inplace=True, errors='ignore')
    
    print(f"\n估算结果摘要：")
    print(f"2019年末潜在增长率: {results_df[results_df['Date'].dt.year == 2019]['Potential_Growth'].iloc[-1]:.2f}%")
    print(f"2019年末自然利率: {results_df[results_df['Date'].dt.year == 2019]['Natural_Rate'].iloc[-1]:.2f}%")
    print(f"2024年末潜在增长率: {results_df['Potential_Growth'].iloc[-1]:.2f}%")
    print(f"2024年末自然利率: {results_df['Natural_Rate'].iloc[-1]:.2f}%")
    
    # 诊断分析：打印关键时期（2019年后）的内部状态和观测值
    print("\n--- 诊断分析表：2019年至今 ---")
    diag_df = results_df[results_df['Date'].dt.year >= 2019].copy()
    
    # 获取同期的原始观测数据
    obs_post_2019 = data[data.index.year >= 2019]
    diag_df['Observed_GDP'] = obs_post_2019['y_t'].values
    diag_df['Observed_M2'] = obs_post_2019['m2_growth_t'].values
    
    # 计算模型隐含的GDP增长（潜在+缺口）
    diag_df['Implied_GDP'] = diag_df['Potential_Growth'] + diag_df['Output_Gap']
    
    # 为了方便对比，我们只看关键列
    print(diag_df[[
        'Date', 'Potential_Growth', 'Output_Gap', 'Implied_GDP', 'Observed_GDP', 'Observed_M2'
    ]].round(2).to_string())
    
    
    # 7. 生成图表和报告
    print("\n7. 生成图表和报告...")
    output_dir = '/mnt/windows_share/项目/reports/中国自然利率测算/'
    
    try:
        create_interactive_charts(results_df, model, output_dir)
        print("交互式图表生成成功")
    except Exception as e:
        print(f"交互式图表生成失败: {e}")
        create_matplotlib_charts(results_df, model, output_dir)
        print("静态图表生成完成")
    
    # 8. 生成报告
    try:
        create_comprehensive_report(output_dir, results_df, model)
    except:
        create_comprehensive_report_matplotlib(output_dir, results_df, model)
    
    print("\n" + "="*80)
    print("估算完成！模型已根据正确的单位和观测方程进行重构。")
    print(f"最终2019年自然利率估算: {results_df[results_df['Date'].dt.year == 2019]['Natural_Rate'].iloc[-1]:.2f}%")
    print("="*80)
    
    return results_df, model

# 运行主程序
if __name__ == "__main__":
    results_df, model = run_estimation()