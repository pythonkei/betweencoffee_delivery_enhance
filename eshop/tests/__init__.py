"""
eshop 測試包 - 動態版本
"""

import pkgutil
import importlib

# 動態導入所有測試模組
package_path = __path__
for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
    if module_name.startswith('test_') and not is_pkg:
        try:
            module = importlib.import_module(f'.{module_name}', __package__)
            globals()[module_name] = module
            print(f"已導入: {module_name}")
        except ImportError as e:
            print(f"導入失敗 {module_name}: {e}")