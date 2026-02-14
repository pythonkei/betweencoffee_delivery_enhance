#!/usr/bin/env python
"""
修復 tests 目錄的 __init__.py 文件
"""

import os

# 創建 __init__.py 內容
init_content = '''"""
eshop 應用測試套件
這個文件確保 tests 目錄被正確識別為 Python 包
"""

# 導入測試模組（可選）
try:
    from .test_basic import *
except ImportError:
    pass

try:
    from .test_models import *
except ImportError:
    pass

try:
    from .test_order_comprehensive import *
except ImportError:
    pass

try:
    from .test_queue import *
except ImportError:
    pass

try:
    from .test_payment import *
except ImportError:
    pass

try:
    from .test_views import *
except ImportError:
    pass

# 定義公開的模組
__all__ = []
'''

# 寫入文件
init_path = 'eshop/tests/__init__.py'
os.makedirs(os.path.dirname(init_path), exist_ok=True)

with open(init_path, 'w', encoding='utf-8') as f:
    f.write(init_content)

print(f"已創建 {init_path}")
print("現在可以運行測試了")
