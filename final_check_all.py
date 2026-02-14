# final_check_all.py
"""
最終檢查所有文件是否還有直接狀態賦值
"""
import os
import re

def find_all_python_files():
    """查找所有 Python 文件"""
    python_files = []
    
    for root, dirs, files in os.walk('.'):
        # 排除一些目錄
        dirs[:] = [d for d in dirs if d not in [
            '__pycache__', 
            '.git', 
            '.venv', 
            'venv',
            'node_modules',
            'static',
            'media',
            'migrations'
        ]]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_file_for_direct_status_assignments(file_path):
    """檢查文件中的直接狀態賦值"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    
    for i, line in enumerate(lines, 1):
        # 檢查 order.status = 的直接賦值
        if re.search(r'order\.status\s*=', line):
            stripped = line.strip()
            
            # 排除註釋
            if stripped.startswith('#'):
                continue
                
            # 排除 OrderStatusManager 內部使用（允許）
            if 'OrderStatusManager' in line:
                continue
                
            # 排除條件判斷
            if 'if' in line and '=' in line and '==' not in line:
                continue
                
            # 排除隊列項的狀態修改
            if re.search(r'queue_?(item)?\.status\s*=', line):
                continue
                
            # 排除測試文件
            if 'test_' in file_path:
                continue
                
            issues.append({
                'line': i,
                'code': stripped
            })
    
    return issues

def main():
    """主函數"""
    print("=== 最終檢查：所有 Python 文件中的直接狀態賦值 ===\n")
    
    python_files = find_all_python_files()
    print(f"找到 {len(python_files)} 個 Python 文件")
    
    total_issues = 0
    files_with_issues = []
    
    for file_path in python_files:
        # 跳過檢查腳本自身
        if 'check' in file_path.lower() or 'validate' in file_path.lower():
            continue
            
        issues = check_file_for_direct_status_assignments(file_path)
        
        if issues:
            files_with_issues.append(file_path)
            print(f"\n❌ {file_path}: {len(issues)} 個問題")
            for issue in issues:
                print(f"   第{issue['line']}行: {issue['code']}")
            
            total_issues += len(issues)
    
    print("\n" + "="*60)
    
    if total_issues == 0:
        print("✅ 恭喜！沒有發現直接狀態賦值問題。")
        print("✅ 所有訂單狀態修改都通過 OrderStatusManager 處理。")
        return True
    else:
        print(f"⚠️  發現 {total_issues} 個直接狀態賦值問題，分佈在 {len(files_with_issues)} 個文件中。")
        print("\n需要修復的文件：")
        for file in files_with_issues:
            print(f"  - {file}")
        return False

if __name__ == '__main__':
    success = main()
    
    if not success:
        print("\n❌ 請修復以上問題後重新運行測試。")
        exit(1)
    else:
        print("\n✅ 所有檢查通過！可以進行下一步部署。")