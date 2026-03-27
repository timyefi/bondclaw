# 债券数据处理脚本

此仓库包含了一系列用于处理债券数据的Python脚本。以下是每个脚本及其功能的说明。

执行顺序和排序一致

## 脚本列表

1. `ths_bond.py`
   - 处理债券曲线数据的核心脚本。
   
2. `ths_bond_basicinfo.py`
   - 确定需要更新的债券。
   
3. `ths_bond_delete_finance_in_rate.py`
   - 删除一些在利率债内的金融债数据。

4. `ths_bond_dealtinfo.py`
   - 拉取债券交易的信息。
   
5. `ths_bond_basicinfo_columns.py`
   - 拉取债券基本信息数据集的列。
   
6. `ths_bond_finance_to_rate_migration.py`
   - 将部分金融债迁移到利率债中。
   
7. `ths_bond_basicinfo_purge.py`
   - 清洗数据。

8. `basicinfo_postgres.py`
   - 移动基本债券信息数据到PostgreSQL数据库。
   
9. `ths_bond_marketinfo_columns.py`
   - 拉取债券行情数据。
   
10. `hzcurve.py`
    - 计算HZ债券的收益率曲线数据。
    
11. `hzcurve_long.py`
    - 计算HZ长期债券的收益率曲线数据。
    
12. `hzcurve_postgres.py`
    - 将收益率曲线数据移动到PostgreSQL数据库。
    
13. `hzcurve_after.py`
    - 对收益率曲线数据结果的后期处理脚本。
    
14. `update_all_bond_after.py`
    - 刷新图表缓存。
    
15. `ths_bond_basicinfo_credit外评.py`
    - 拉取债券的外部信用评级。
    
16. `hzcurve_基础曲线构建.py`
    - 见文件名。
