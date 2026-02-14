# precise_status_check.py
"""
精確檢查真正的直接狀態賦值，排除條件判斷
"""
import os
import re

def is_condition_check(line):
    """判斷是否為條件判斷語句"""
    line = line.strip()
    
    # 檢查是否為條件判斷
    condition_patterns = [
        r'if\s+order\.status\s*==',           # if order.status ==
        r'elif\s+order\.status\s*==',         # elif order.status ==
        r'and\s+order\.status\s*==',          # and order.status ==
        r'or\s+order\.status\s*==',           # or order.status ==
        r'order\.status\s*==',                # order.status ==
    ]
    
    for pattern in condition_patterns:
        if re.search(pattern, line):
            return True
    
    return False

def is_comment(line):
    """判斷是否為註釋"""
    return line.strip().startswith('#')

def is_order_status_manager_internal(file_path, line):
    """判斷是否為 OrderStatusManager 內部允許的修改"""
    # OrderStatusManager 內部可以直接修改狀態，這是允許的
    if 'order_status_manager.py' in file_path:
        return True
    return False

def check_real_assignments():
    """檢查真正的直接狀態賦值"""
    print("=== 精確檢查：真正的直接狀態賦值 ===\n")
    
    # 需要檢查的文件
    files_to_check = [
        'eshop/admin.py',
        'eshop/view_utils.py',
        'eshop/order_status_manager.py',
        'eshop/queue_manager.py',
        'eshop/views/queue_views.py',
        'eshop/views/payment_views.py',
        'eshop/views/order_views.py'
    ]
    
    total_real_issues = 0
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        file_real_issues = []
        
        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # 跳過註釋
            if is_comment(stripped_line):
                continue
            
            # 檢查是否為直接賦值（order.status = 'xxx'）
            if re.search(r'order\.status\s*=', stripped_line):
                # 排除條件判斷
                if is_condition_check(stripped_line):
                    continue
                
                # 排除 OrderStatusManager 內部的修改（這是允許的）
                if is_order_status_manager_internal(file_path, stripped_line):
                    # 但我們還是要記錄一下，確認這些都是必要的
                    file_real_issues.append({
                        'line': i,
                        'code': stripped_line,
                        'type': 'allowed_internal'
                    })
                else:
                    file_real_issues.append({
                        'line': i,
                        'code': stripped_line,
                        'type': 'needs_fix'
                    })
        
        if file_real_issues:
            print(f"\n📋 {file_path}:")
            
            allowed_count = sum(1 for issue in file_real_issues if issue['type'] == 'allowed_internal')
            fix_count = sum(1 for issue in file_real_issues if issue['type'] == 'needs_fix')
            
            if fix_count > 0:
                print(f"  ❌ 需要修復: {fix_count} 個")
                for issue in file_real_issues:
                    if issue['type'] == 'needs_fix':
                        print(f"    第{issue['line']}行: {issue['code']}")
            
            if allowed_count > 0:
                print(f"  ✅ 允許的內部修改: {allowed_count} 個")
                for issue in file_real_issues:
                    if issue['type'] == 'allowed_internal':
                        print(f"    第{issue['line']}行: {issue['code']} (OrderStatusManager內部)")
            
            total_real_issues += fix_count
    
    print(f"\n{'='*60}")
    
    if total_real_issues == 0:
        print("✅ 恭喜！沒有發現需要修復的直接狀態賦值。")
        print("✅ 所有訂單狀態修改都通過 OrderStatusManager 處理或在其內部。")
        return True
    else:
        print(f"❌ 發現 {total_real_issues} 個需要修復的直接狀態賦值。")
        return False

def main():
    """主函數"""
    success = check_real_assignments()
    
    if success:
        print("\n✅ 可以進行下一步部署。")
        exit(0)
    else:
        print("\n❌ 請修復以上問題後重新運行測試。")
        exit(1)

if __name__ == '__main__':
    main()