# fix_remaining_views.py
"""
修復視圖文件中的直接狀態賦值
"""
import os
import re

def fix_payment_views():
    """修復 payment_views.py"""
    file_path = 'eshop/views/payment_views.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️  文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    
    for i, line in enumerate(lines):
        # 修復第762行附近：order.status = 'waiting'
        if "'waiting'" in line and 'order.status =' in line and '# ✅' not in line:
            print(f"找到 waiting 狀態賦值: 第{i+1}行")
            
            # 檢查是否已經是正確的修復
            if 'OrderStatusManager' in line or 'mark_as_waiting_manually' in line:
                print(f"✅ 第{i+1}行已經使用 OrderStatusManager")
                continue
            
            # 添加修復
            indent = len(line) - len(line.lstrip())
            space = ' ' * indent
            
            replacement = f"{space}# ✅ 已修復：使用 OrderStatusManager\n"
            replacement += f"{space}from eshop.order_status_manager import OrderStatusManager\n"
            replacement += f"{space}result = OrderStatusManager.mark_as_waiting_manually(\n"
            replacement += f"{space}    order_id=order.id,\n"
            replacement += f"{space}    staff_name=request.user.username if hasattr(request, 'user') else 'system'\n"
            replacement += f"{space})\n"
            replacement += f"{space}if not result.get('success'):\n"
            replacement += f"{space}    logger.error(f\"標記訂單 {{order.id}} 為 waiting 失敗: {{result.get('message')}}\")\n"
            
            lines[i] = replacement
            modified = True
            
        # 修復第883行附近：order.status = 'cancelled'
        elif "'cancelled'" in line and 'order.status =' in line and '# ✅' not in line:
            print(f"找到 cancelled 狀態賦值: 第{i+1}行")
            
            if 'OrderStatusManager' in line or 'mark_as_cancelled_manually' in line:
                print(f"✅ 第{i+1}行已經使用 OrderStatusManager")
                continue
            
            indent = len(line) - len(line.lstrip())
            space = ' ' * indent
            
            replacement = f"{space}# ✅ 已修復：使用 OrderStatusManager\n"
            replacement += f"{space}from eshop.order_status_manager import OrderStatusManager\n"
            replacement += f"{space}result = OrderStatusManager.mark_as_cancelled_manually(\n"
            replacement += f"{space}    order_id=order.id,\n"
            replacement += f"{space}    staff_name=request.user.username if hasattr(request, 'user') else 'system',\n"
            replacement += f"{space}    reason='支付失敗或超時'\n"
            replacement += f"{space})\n"
            replacement += f"{space}if not result.get('success'):\n"
            replacement += f"{space}    logger.error(f\"取消訂單 {{order.id}} 失敗: {{result.get('message')}}\")\n"
            
            lines[i] = replacement
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ {file_path} 已修復")
        return True
    else:
        print(f"✅ {file_path} 無需修復")
        return True

def fix_order_views():
    """修復 order_views.py"""
    file_path = 'eshop/views/order_views.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️  文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    
    for i, line in enumerate(lines):
        # 修復第470行附近：order.status = 'pending'
        if "'pending'" in line and 'order.status =' in line and '# ✅' not in line:
            print(f"找到 pending 狀態賦值: 第{i+1}行")
            
            if 'OrderStatusManager' in line or 'process_order_status_change' in line:
                print(f"✅ 第{i+1}行已經使用 OrderStatusManager")
                continue
            
            indent = len(line) - len(line.lstrip())
            space = ' ' * indent
            
            replacement = f"{space}# ✅ 已修復：使用 OrderStatusManager\n"
            replacement += f"{space}from eshop.order_status_manager import OrderStatusManager\n"
            replacement += f"{space}result = OrderStatusManager.process_order_status_change(\n"
            replacement += f"{space}    order_id=order.id,\n"
            replacement += f"{space}    new_status='pending',\n"
            replacement += f"{space}    staff_name=request.user.username if hasattr(request, 'user') else 'system'\n"
            replacement += f"{space})\n"
            replacement += f"{space}if not result.get('success'):\n"
            replacement += f"{space}    logger.error(f\"標記訂單 {{order.id}} 為 pending 失敗: {{result.get('message')}}\")\n"
            
            lines[i] = replacement
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ {file_path} 已修復")
        return True
    else:
        print(f"✅ {file_path} 無需修復")
        return True

def fix_queue_views():
    """修復 queue_views.py"""
    file_path = 'eshop/views/queue_views.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️  文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    
    for i, line in enumerate(lines):
        # 修復第842行附近：order.status = 'waiting'
        if "'waiting'" in line and 'order.status =' in line and '# ✅' not in line:
            print(f"找到 waiting 狀態賦值: 第{i+1}行")
            
            if 'OrderStatusManager' in line or 'mark_as_waiting_manually' in line:
                print(f"✅ 第{i+1}行已經使用 OrderStatusManager")
                continue
            
            indent = len(line) - len(line.lstrip())
            space = ' ' * indent
            
            replacement = f"{space}# ✅ 已修復：使用 OrderStatusManager\n"
            replacement += f"{space}from eshop.order_status_manager import OrderStatusManager\n"
            replacement += f"{space}result = OrderStatusManager.mark_as_waiting_manually(\n"
            replacement += f"{space}    order_id=order.id,\n"
            replacement += f"{space}    staff_name=request.user.username if hasattr(request, 'user') else 'system'\n"
            replacement += f"{space})\n"
            replacement += f"{space}if not result.get('success'):\n"
            replacement += f"{space}    logger.error(f\"標記訂單 {{order.id}} 為 waiting 失敗: {{result.get('message')}}\")\n"
            
            lines[i] = replacement
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ {file_path} 已修復")
        return True
    else:
        print(f"✅ {file_path} 無需修復")
        return True

def check_remaining_issues():
    """檢查是否還有直接狀態賦值"""
    print("\n=== 檢查剩餘問題 ===")
    
    files_to_check = [
        'eshop/views/payment_views.py',
        'eshop/views/order_views.py',
        'eshop/views/queue_views.py'
    ]
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            issues = []
            for i, line in enumerate(lines, 1):
                if re.search(r'order\.status\s*=', line.strip()):
                    stripped = line.strip()
                    # 排除註釋和 OrderStatusManager 調用
                    if not stripped.startswith('#') and 'OrderStatusManager' not in stripped:
                        issues.append({
                            'line': i,
                            'code': stripped
                        })
            
            if issues:
                print(f"\n❌ {file_path}: 仍有 {len(issues)} 個問題")
                for issue in issues:
                    print(f"   第{issue['line']}行: {issue['code']}")
            else:
                print(f"\n✅ {file_path}: 沒有直接狀態賦值")

def main():
    """主函數"""
    print("開始修復視圖文件中的直接狀態賦值...")
    
    # 修復各個文件
    fix_payment_views()
    fix_order_views()
    fix_queue_views()
    
    # 檢查剩餘問題
    check_remaining_issues()
    
    print("\n=== 修復完成 ===")
    print("請運行測試驗證修復是否正確:")
    print("1. python manage.py test eshop.tests.test_payments")
    print("2. python manage.py test eshop.tests.test_order_comprehensive")
    print("3. python manage.py test eshop.tests.test_queues")

if __name__ == '__main__':
    main()