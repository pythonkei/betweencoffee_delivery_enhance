#!/usr/bin/env python3
"""
JavaScript文件依賴關係分析工具
分析項目中的JavaScript文件，找出重複代碼和依賴關係
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
from datetime import datetime

def read_js_file(filepath):
    """讀取JavaScript文件內容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return ""

def calculate_file_hash(content):
    """計算文件內容的哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def extract_imports(content):
    """從JavaScript內容中提取導入語句"""
    imports = []
    
    # 匹配各種導入語句
    patterns = [
        r'import\s+.*?from\s+[\'"](.+?)[\'"]',  # ES6 import
        r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)',  # CommonJS require
        r'src\s*=\s*[\'"](.+?\.js)[\'"]',        # script src
        r'load\s*\(\s*[\'"](.+?\.js)[\'"]\s*\)', # 動態加載
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        imports.extend(matches)
    
    return imports

def extract_functions(content):
    """從JavaScript內容中提取函數定義"""
    functions = []
    
    # 匹配函數定義
    patterns = [
        r'function\s+(\w+)\s*\(',                # function name()
        r'const\s+(\w+)\s*=\s*\(.*?\)\s*=>',     # const name = () =>
        r'let\s+(\w+)\s*=\s*\(.*?\)\s*=>',       # let name = () =>
        r'var\s+(\w+)\s*=\s*\(.*?\)\s*=>',       # var name = () =>
        r'const\s+(\w+)\s*=\s*function',         # const name = function
        r'let\s+(\w+)\s*=\s*function',           # let name = function
        r'var\s+(\w+)\s*=\s*function',           # var name = function
        r'\.(\w+)\s*=\s*function',               # .name = function
        r'(\w+)\s*:\s*function\s*\(',            # name: function(
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        functions.extend(matches)
    
    return list(set(functions))  # 去重

def extract_variables(content):
    """從JavaScript內容中提取全局變量"""
    variables = []
    
    # 匹配全局變量定義
    patterns = [
        r'const\s+(\w+)\s*=',     # const variable =
        r'let\s+(\w+)\s*=',       # let variable =
        r'var\s+(\w+)\s*=',       # var variable =
        r'window\.(\w+)\s*=',     # window.variable =
        r'global\.(\w+)\s*=',     # global.variable =
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        variables.extend(matches)
    
    return list(set(variables))

def find_duplicate_code(files_content, min_length=50):
    """查找重複的代碼片段"""
    code_segments = defaultdict(list)
    
    for filepath, content in files_content.items():
        # 將代碼按行分割
        lines = content.split('\n')
        
        # 提取有意義的代碼塊（去除空行和註釋）
        meaningful_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                meaningful_lines.append(stripped)
        
        # 生成代碼片段
        for i in range(len(meaningful_lines) - 5):  # 至少5行
            segment = '\n'.join(meaningful_lines[i:i+10])  # 10行片段
            if len(segment) >= min_length:
                segment_hash = hashlib.md5(segment.encode('utf-8')).hexdigest()
                code_segments[segment_hash].append((filepath, i))
    
    # 過濾出重複的代碼片段
    duplicates = {hash: files for hash, files in code_segments.items() if len(files) > 1}
    
    return duplicates

def analyze_file_dependencies(js_files):
    """分析文件之間的依賴關係"""
    dependencies = defaultdict(set)
    dependents = defaultdict(set)
    
    for filepath in js_files:
        content = read_js_file(filepath)
        imports = extract_imports(content)
        
        for imp in imports:
            # 嘗試解析導入路徑
            if imp.startswith('.'):
                # 相對路徑
                imp_path = os.path.normpath(os.path.join(os.path.dirname(filepath), imp))
                # 查找對應的.js文件
                if os.path.exists(imp_path):
                    dependencies[filepath].add(imp_path)
                    dependents[imp_path].add(filepath)
                elif os.path.exists(imp_path + '.js'):
                    dependencies[filepath].add(imp_path + '.js')
                    dependents[imp_path + '.js'].add(filepath)
            else:
                # 可能是外部庫或絕對路徑
                dependencies[filepath].add(imp)
    
    return dependencies, dependents

def generate_report(js_files, output_dir='js_analysis_report'):
    """生成分析報告"""
    print("開始分析JavaScript文件...")
    
    # 創建輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 收集文件信息
    files_info = {}
    all_functions = defaultdict(list)
    all_variables = defaultdict(list)
    files_content = {}
    
    for filepath in js_files:
        print(f"分析文件: {filepath}")
        content = read_js_file(filepath)
        files_content[filepath] = content
        
        file_hash = calculate_file_hash(content)
        imports = extract_imports(content)
        functions = extract_functions(content)
        variables = extract_variables(content)
        
        files_info[filepath] = {
            'size': len(content),
            'hash': file_hash,
            'imports': imports,
            'functions': functions,
            'variables': variables,
            'line_count': content.count('\n') + 1
        }
        
        # 收集所有函數和變量
        for func in functions:
            all_functions[func].append(filepath)
        for var in variables:
            all_variables[var].append(filepath)
    
    # 分析依賴關係
    dependencies, dependents = analyze_file_dependencies(js_files)
    
    # 查找重複代碼
    print("查找重複代碼...")
    duplicate_code = find_duplicate_code(files_content)
    
    # 生成統計數據
    stats = {
        'total_files': len(js_files),
        'total_size': sum(info['size'] for info in files_info.values()),
        'total_lines': sum(info['line_count'] for info in files_info.values()),
        'unique_functions': len(all_functions),
        'duplicate_functions': sum(1 for files in all_functions.values() if len(files) > 1),
        'duplicate_code_segments': len(duplicate_code),
        'analysis_date': datetime.now().isoformat()
    }
    
    # 生成合併建議
    merge_suggestions = []
    
    # 1. 查找相似的文件（基於函數重疊）
    for i, file1 in enumerate(js_files):
        for file2 in js_files[i+1:]:
            funcs1 = set(files_info[file1]['functions'])
            funcs2 = set(files_info[file2]['functions'])
            common_funcs = funcs1.intersection(funcs2)
            
            if len(common_funcs) >= 3:  # 至少有3個相同函數
                overlap_ratio = len(common_funcs) / max(len(funcs1), len(funcs2))
                if overlap_ratio > 0.3:  # 重疊率超過30%
                    merge_suggestions.append({
                        'files': [file1, file2],
                        'common_functions': list(common_funcs),
                        'overlap_ratio': overlap_ratio,
                        'reason': f"有 {len(common_funcs)} 個相同函數，重疊率 {overlap_ratio:.1%}"
                    })
    
    # 2. 查找依賴關係緊密的文件
    for filepath, deps in dependencies.items():
        if len(deps) == 1:
            dep = next(iter(deps))
            if dep in js_files:  # 確保是項目內的文件
                merge_suggestions.append({
                    'files': [filepath, dep],
                    'reason': f"{os.path.basename(filepath)} 只依賴於 {os.path.basename(dep)}",
                    'type': 'dependency'
                })
    
    # 生成報告文件
    report = {
        'stats': stats,
        'files': files_info,
        'dependencies': {k: list(v) for k, v in dependencies.items()},
        'dependents': {k: list(v) for k, v in dependents.items()},
        'function_usage': {func: files for func, files in all_functions.items() if len(files) > 1},
        'variable_usage': {var: files for var, files in all_variables.items() if len(files) > 1},
        'duplicate_code': {hash: files for hash, files in duplicate_code.items()},
        'merge_suggestions': merge_suggestions,
        'optimization_recommendations': []
    }
    
    # 添加優化建議
    if stats['duplicate_functions'] > 0:
        report['optimization_recommendations'].append({
            'type': 'duplicate_functions',
            'description': f"發現 {stats['duplicate_functions']} 個重複定義的函數",
            'suggestion': "考慮將重複函數提取到共用模塊中"
        })
    
    if stats['duplicate_code_segments'] > 0:
        report['optimization_recommendations'].append({
            'type': 'duplicate_code',
            'description': f"發現 {stats['duplicate_code_segments']} 個重複代碼片段",
            'suggestion': "合併重複代碼以減少維護成本"
        })
    
    # 保存報告
    report_file = os.path.join(output_dir, 'js_analysis_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 生成HTML報告
    generate_html_report(report, output_dir)
    
    print(f"\n分析完成！報告已保存到: {output_dir}/")
    print(f"統計數據:")
    print(f"  總文件數: {stats['total_files']}")
    print(f"  總代碼行數: {stats['total_lines']}")
    print(f"  總文件大小: {stats['total_size'] / 1024:.1f} KB")
    print(f"  唯一函數數: {stats['unique_functions']}")
    print(f"  重複函數數: {stats['duplicate_functions']}")
    print(f"  重複代碼片段: {stats['duplicate_code_segments']}")
    print(f"  合併建議: {len(merge_suggestions)} 個")
    
    return report

def generate_html_report(report, output_dir):
    """生成HTML格式的報告"""
    html_template = """<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JavaScript代碼分析報告</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1, h2, h3 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 14px;
        }
        
        .recommendation {
            background: #e8f4fc;
            border: 1px solid #3498db;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .recommendation.warning {
            background: #fff3cd;
            border-color: #ffc107;
        }
        
        .recommendation.error {
            background: #f8d7da;
            border-color: #dc3545;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #f8f9fa;
            font-weight: bold;
        }
        
        tr:hover {
            background: #f5f5f5;
        }
        
        .code {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin: 0 5px;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .file-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        
        .timestamp {
            color: #7f8c8d;
            font-size: 14px;
            text-align: right;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 JavaScript代碼分析報告</h1>
        <div class="timestamp">生成時間: {{analysis_date}}</div>
        
        <h2>📈 統計概覽</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{total_files}}</div>
                <div class="stat-label">總文件數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{total_lines}}</div>
                <div class="stat-label">總代碼行數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{total_size_kb}} KB</div>
                <div class="stat-label">總文件大小</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{unique_functions}}</div>
                <div class="stat-label">唯一函數數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{duplicate_functions}}</div>
                <div class="stat-label">重複函數數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{duplicate_code_segments}}</div>
                <div class="stat-label">重複代碼片段</div>
            </div>
        </div>
        
        <h2>🚨 優化建議</h2>
        {{#optimization_recommendations}}
        <div class="recommendation {{type}}">
            <h3>{{description}}</h3>
            <p>{{suggestion}}</p>
        </div>
        {{/optimization_recommendations}}
        
        <h2>📁 文件列表</h2>
        <div class="file-list">
            {{#files}}
            <div><span class="code">{{@key}}</span> - {{size}} bytes, {{line_count}} 行, {{functions|length}} 個函數</div>
            {{/files}}
        </div>
        
        <h2>🔗 依賴關係</h2>
        <table>
            <thead>
                <tr>
                    <th>文件</th>
                    <th>依賴的文件</th>
                    <th>被依賴的文件</th>
                </tr>
            </thead>
            <tbody>
                {{#files}}
                <tr>
                    <td><span class="code">{{@key}}</span></td>
                    <td>
                        {{#dependencies[@key]}}
                        <span class="badge badge-success">{{.}}</span>
                        {{/dependencies[@key]}}
                    </td>
                    <td>
                        {{#dependents[@key]}}
                        <span class="badge badge-warning">{{.}}</span>
                        {{/dependents[@key]}}
                    </td>
                </tr>
                {{/files}}
            </tbody>
        </table>
        
        <h2>🔄 合併建議</h2>
        {{#merge_suggestions}}
        <div class="recommendation">
            <h3>合併建議 {{@index}}</h3>
            <p>{{reason}}</p>
            <p>涉及文件:</p>
            <ul>
                {{#files}}
                <li><span class="code">{{.}}</span></li>
                {{/files}}
            </ul>
            {{#common_functions}}
            <p>共同函數: {{#.}}<span class="badge">{{.}}</span> {{/.}}</p>
            {{/common_functions}}
        </div>
        {{/merge_suggestions}}
        
        <h2>📝 重複函數</h2>
        <table>
            <thead>
                <tr>
                    <th>函數名</th>
                    <th>出現的文件</th>
                </tr>
            </thead>
            <tbody>
                {{#function_usage}}
                <tr>
                    <td><span class="code">{{@key}}</span></td>
                    <td>
                        {{#.}}
                        <span class="badge badge-danger">{{.}}</span>
                        {{/.}}
                    </td>
                </tr>
                {{/function_usage}}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    
    # 準備模板數據
    template_data = {
        'analysis_date': report['stats']['analysis_date'],
        'total_files': report['stats']['total_files'],
        'total_lines': report['stats']['total_lines'],
        'total_size_kb': f"{report['stats']['total_size'] / 1024:.1f}",
        'unique_functions': report['stats']['unique_functions'],
        'duplicate_functions': report['stats']['duplicate_functions'],
        'duplicate_code_segments': report['stats']['duplicate_code_segments'],
        'optimization_recommendations': report['optimization_recommendations'],
        'files': report['files'],
        'dependencies': report['dependencies'],
        'dependents': report['dependents'],
        'function_usage': report['function_usage'],
        'merge_suggestions': report['merge_suggestions']
    }
    
    # 簡單的模板替換
    html_content = html_template
    for key, value in template_data.items():
        if isinstance(value, (str, int, float)):
            html_content = html_content.replace(f'{{{{{key}}}}}', str(value))
    
    # 保存HTML文件
    html_file = os.path.join(output_dir, 'js_analysis_report.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML報告已生成: {html_file}")

def find_js_files(directory='static/js'):
    """查找指定目錄下的所有JavaScript文件"""
    js_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.js'):
                js_files.append(os.path.join(root, file))
    
    return js_files

def main():
    """主函數"""
    print("=" * 60)
    print("JavaScript文件依賴關係分析工具")
    print("=" * 60)
    
    # 查找JavaScript文件
    js_files = find_js_files('static/js')
    
    if not js_files:
        print("未找到JavaScript文件！")
        return
    
    print(f"找到 {len(js_files)} 個JavaScript文件")
    
    # 生成報告
    report = generate_report(js_files)
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
