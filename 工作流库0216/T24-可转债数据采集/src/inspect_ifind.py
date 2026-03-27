import inspect
from iFinDPy import THS_DS

# 获取函数的源代码
print("=== THS_DS 函数信息 ===")
print(inspect.getsource(THS_DS))

# 获取函数的签名
print("\n=== THS_DS 函数签名 ===")
print(inspect.signature(THS_DS))

# 获取函数的文档字符串
print("\n=== THS_DS 函数文档 ===")
print(inspect.getdoc(THS_DS)) 