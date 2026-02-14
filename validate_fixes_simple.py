# detailed_check.py
"""
詳細檢查所有 Python 文件中的直接狀態賦值
"""
import os
import re

def find_all_py_files():
    """查找所有 Python 文件"""
    py_files = []
    
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
                full_path = os.path.join(root, file)
                py_files.append(full_path)
    
    return py_files

def check_file_for_direct_assignments(file_path):
    """檢查文件中的直接狀態賦值"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 檢查 order.status = 的直接賦值
            if re.search(r'order\.status\s*=', line):
                stripped = line.strip()
                
                # 排除註釋
                if stripped.startswith('#'):
                    continue
                    
                # 排除 OrderStatusManager 內部
                if 'OrderStatusManager' in line and 'def ' not in line:
                    continue
                    
                # 排除函數定義
                if 'def ' in line:
                    continue
                    
                issues.append({
                    'line': i,
                    'code': stripped
                })
    
    return issues

def main():
    """主函數"""
    print("詳細檢查所有 Python 文件中的直接狀態賦值...")
    
    py_files = find_all_py_files()
    print(f"找到 {len(py_files)} 個 Python 文件")
    
    total_issues = 0
    
    for file_path in py_files:
        issues = check_file_for_direct_assignments(file_path)
        
        if issues:
            print(f"\n❌ {file_path}: 發現 {len(issues)} 個問題")
            for issue in issues:
                print(f"   第{issue['line']}行: {issue['code']}")
            
            total_issues += len(issues)
    
    if total_issues == 0:
        print("\n✅ 恭喜！沒有發現直接狀態賦值。")
    else:
        print(f"\n⚠️  總共發現 {total_issues} 個直接狀態賦值問題需要修復。")

if __name__ == '__main__':
    main()