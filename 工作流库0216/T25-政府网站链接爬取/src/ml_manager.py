"""机器学习管理模块"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from services.config.config_manager import ConfigManager
from utils.log_manager import log_manager

logger = log_manager.get_logger('ml_manager')

class MLManager:
    """机器学习管理器"""
    
    def __init__(self):
        """初始化ML管理器"""
        self.config_manager = ConfigManager()
        self.models = {}
        self.vectorizers = {}
        self.feature_selectors = {}
        self.model_metadata = {}
        self.training_history = []
        
    async def initialize(self):
        """初始化ML系统"""
        try:
            # 从配置管理器获取ML配置
            self.ml_config = self.config_manager.get('ml', {})
            
            # 加载已有模型
            await self._load_models()
            
            # 初始化特征提取器
            await self._init_feature_extractors()
            
            logger.info("ML管理器初始化完成")
            
        except Exception as e:
            logger.error(f"ML管理器初始化失败: {str(e)}")
            raise
            
    async def _load_models(self):
        """加载已有模型"""
        try:
            models_dir = self.ml_config.get('models_dir', 'models')
            os.makedirs(models_dir, exist_ok=True)
            
            for model_file in os.listdir(models_dir):
                if model_file.endswith('.joblib'):
                    model_path = os.path.join(models_dir, model_file)
                    model_name = model_file[:-7]  # 去掉.joblib后缀
                    
                    # 加载模型
                    self.models[model_name] = joblib.load(model_path)
                    
                    # 加载元数据
                    metadata_path = os.path.join(
                        models_dir,
                        f"{model_name}_metadata.json"
                    )
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            self.model_metadata[model_name] = json.load(f)
                            
            logger.info(f"已加载 {len(self.models)} 个模型")
            
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            raise
            
    async def _init_feature_extractors(self):
        """初始化特征提取器"""
        try:
            # 获取特征提取配置
            feature_config = self.ml_config.get('feature_extraction', {})
            
            # 初始化TF-IDF向量化器
            self.vectorizers['tfidf'] = TfidfVectorizer(
                max_features=feature_config.get('max_features', 1000),
                min_df=feature_config.get('min_df', 5),
                max_df=feature_config.get('max_df', 0.95),
                ngram_range=feature_config.get('ngram_range', (1, 2))
            )
            
            # 初始化特征选择器
            self.feature_selectors['chi2'] = SelectKBest(
                chi2,
                k=feature_config.get('select_k_best', 100)
            )
            
            logger.info("特征提取器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化特征提取器失败: {str(e)}")
            raise
            
    async def train_model(
        self,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = 'rf'
    ) -> bool:
        """训练模型
        
        Args:
            model_name: 模型名称
            X_train: 训练特征
            y_train: 训练标签
            model_type: 模型类型 ('rf' 或 'xgb')
            
        Returns:
            bool: 是否训练成功
        """
        try:
            # 获取模型配置
            model_config = self.ml_config.get('models', {}).get(model_type, {})
            
            # 创建模型
            if model_type == 'rf':
                model = RandomForestClassifier(
                    n_estimators=model_config.get('n_estimators', 100),
                    max_depth=model_config.get('max_depth', 10),
                    min_samples_split=model_config.get('min_samples_split', 2),
                    min_samples_leaf=model_config.get('min_samples_leaf', 1),
                    random_state=42
                )
            elif model_type == 'xgb':
                model = xgb.XGBClassifier(
                    n_estimators=model_config.get('n_estimators', 100),
                    max_depth=model_config.get('max_depth', 6),
                    learning_rate=model_config.get('learning_rate', 0.1),
                    random_state=42
                )
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
                
            # 训练模型
            model.fit(X_train, y_train)
            
            # 评估模型
            cv_results = cross_validate(
                model,
                X_train,
                y_train,
                cv=5,
                scoring=['accuracy', 'precision', 'recall', 'f1']
            )
            
            # 保存模型
            self.models[model_name] = model
            
            # 保存元数据
            self.model_metadata[model_name] = {
                'type': model_type,
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': float(cv_results['test_accuracy'].mean()),
                    'precision': float(cv_results['test_precision'].mean()),
                    'recall': float(cv_results['test_recall'].mean()),
                    'f1': float(cv_results['test_f1'].mean())
                },
                'parameters': model.get_params()
            }
            
            # 保存到文件
            await self._save_model(model_name)
            
            # 记录训练历史
            self.training_history.append({
                'model_name': model_name,
                'timestamp': datetime.now().isoformat(),
                'metrics': self.model_metadata[model_name]['metrics']
            })
            
            logger.info(f"模型 {model_name} 训练完成")
            return True
            
        except Exception as e:
            logger.error(f"训练模型 {model_name} 失败: {str(e)}")
            return False
            
    async def _save_model(self, model_name: str):
        """保存模型到文件
        
        Args:
            model_name: 模型名称
        """
        try:
            models_dir = self.ml_config.get('models_dir', 'models')
            os.makedirs(models_dir, exist_ok=True)
            
            # 保存模型
            model_path = os.path.join(models_dir, f"{model_name}.joblib")
            joblib.dump(self.models[model_name], model_path)
            
            # 保存元数据
            metadata_path = os.path.join(models_dir, f"{model_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata[model_name], f, indent=2)
                
        except Exception as e:
            logger.error(f"保存模型 {model_name} 失败: {str(e)}")
            raise
            
    async def predict(
        self,
        model_name: str,
        X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """使用模型进行预测
        
        Args:
            model_name: 模型名称
            X: 特征数据
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: 预测标签和概率
        """
        try:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 不存在")
                
            model = self.models[model_name]
            
            # 预测
            y_pred = model.predict(X)
            y_prob = model.predict_proba(X)
            
            return y_pred, y_prob
            
        except Exception as e:
            logger.error(f"模型 {model_name} 预测失败: {str(e)}")
            raise
            
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict]: 模型信息
        """
        return self.model_metadata.get(model_name)
        
    def get_training_history(self) -> List[Dict]:
        """获取训练历史
        
        Returns:
            List[Dict]: 训练历史记录
        """
        return self.training_history
        
    async def cleanup(self):
        """清理资源"""
        self.models.clear()
        self.vectorizers.clear()
        self.feature_selectors.clear()
        self.model_metadata.clear()
        self.training_history.clear() 