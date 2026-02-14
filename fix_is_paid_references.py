# fix_is_paid_references.py
import os
import re
from pathlib import Path

def fix_python_file(filepath):
    """修复Python文件中的is_paid引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 模式1: 查询条件中的 is_paid=True/False
    content = re.sub(
        r'is_paid\s*=\s*True',
        'payment_status="paid"',
        content
    )
    content = re.sub(
        r'is_paid\s*=\s*False',
        'payment_status="pending"',
        content
    )
    
    # 模式2: filter()中的is_paid
    content = re.sub(
        r'\.filter\([^)]*is_paid=True[^)]*\)',
        lambda m: re.sub(r'is_paid=True', 'payment_status="paid"', m.group(0)),
        content
    )
    
    # 模式3: 属性访问 if order.is_paid:
    content = re.sub(
        r'if\s+(?:not\s+)?(\w+\.)?is_paid:',
        lambda m: f'if {m.group(1) or ""}payment_status == "paid":' 
                  if 'not' not in m.group(0) else 
                  f'if {m.group(1) or ""}payment_status != "paid":',
        content
    )
    
    # 模式4: 赋值操作 order.is_paid = True/False
    content = re.sub(
        r'(\w+)\.is_paid\s*=\s*True',
        r'\1.payment_status = "paid"',
        content
    )
    content = re.sub(
        r'(\w+)\.is_paid\s*=\s*False',
        r'\1.payment_status = "pending"',
        content
    )
    
    # 模式5: 序列化器中的is_paid字段
    content = re.sub(
        r"'is_paid':\s*(\w+)\.is_paid",
        r"'is_paid': \1.payment_status == 'paid'",
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复: {filepath}")

def fix_all_eshop_files():
    """修复eshop目录下所有相关文件"""
    eshop_dir = Path("eshop")
    
    # 需要修复的文件列表（基于grep结果）
    critical_files = [
        "views/queue_views.py",
        "views/payment_views.py", 
        "views/api_views.py",
        "views/order_views.py",
        "views/staff_views.py",
        "order_status_manager.py",
        "queue_manager.py",
        "payment_utils.py",
        "view_utils.py",
        "serializers.py",
        "tasks.py",
        "management/commands/fix_queue_data.py",
        "management/commands/monitor_payments.py"
    ]
    
    # 修复关键文件
    for file in critical_files:
        filepath = eshop_dir / file
        if filepath.exists():
            fix_python_file(str(filepath))
    
    # 修复其他可能的视图文件
    for py_file in eshop_dir.rglob("*.py"):
        # 跳过测试文件和已处理的文件
        if "test" in str(py_file) or py_file.name == "models.py":
            continue
        
        with open(py_file, 'r', encoding='utf-8') as f:
            if "is_paid" in f.read():
                print(f"发现残留引用: {py_file}")
                # 可以选择自动修复或手动检查

if __name__ == "__main__":
    fix_all_eshop_files()