#!/usr/bin/env python
"""
清理對 is_paid 字段的引用

掃描項目中的 Python 和 HTML 文件，
查找並報告對 is_paid 字段的引用。
"""

import ast
import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class PaymentReferenceCleaner:
    """清理對 is_paid 字段的引用"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.files_to_check = [
            'eshop/models.py',
            'eshop/views/',
            'eshop/order_status_manager.py',
            'eshop/queue_manager.py',
            'eshop/payment_utils.py',
            'templates/',
        ]
        self.references = []
    
    def find_is_paid_references(self):
        """查找所有對 is_paid 的引用"""
        self.references = []
        
        for file_pattern in self.files_to_check:
            path = self.project_root / file_pattern
            
            if path.is_dir():
                # 掃描目錄
                for file_path in path.rglob('*.py'):
                    self._check_python_file(file_path)
                for file_path in path.rglob('*.html'):
                    self._check_html_file(file_path)
            else:
                # 掃描單個文件
                if path.exists():
                    if path.suffix == '.py':
                        self._check_python_file(path)
                    elif path.suffix == '.html':
                        self._check_html_file(path)
        
        return self.references
    
    def _check_python_file(self, file_path):
        """檢查 Python 文件中的 is_paid 引用"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if self._contains_is_paid_reference(line):
                    self.references.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'content': line.strip(),
                        'type': 'python',
                    })
                    
        except Exception as e:
            logger.error(f"檢查文件 {file_path} 失敗: {str(e)}")
    
    def _check_html_file(self, file_path):
        """檢查 HTML 文件中的 is_paid 引用"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if self._contains_is_paid_reference(line):
                    self.references.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'content': line.strip(),
                        'type': 'html',
                    })
                    
        except Exception as e:
            logger.error(f"檢查文件 {file_path} 失敗: {str(e)}")
    
    def _contains_is_paid_reference(self, line):
        """檢查行是否包含 is_paid 引用"""
        line_lower = line.lower()
        
        # 檢查各種可能的引用模式
        patterns = [
            '.is_paid',
            'is_paid=',
            'is_paid ',
            '"is_paid"',
            "'is_paid'",
            'is_paid:',
            'is_paid,',
        ]
        
        return any(pattern in line_lower for pattern in patterns)
    
    def generate_report(self):
        """生成報告"""
        if not self.references:
            return "未找到對 is_paid 字段的引用。"
        
        report_lines = []
        report_lines.append(f"找到 {len(self.references)} 個對 is_paid 字段的引用:")
        report_lines.append("=" * 80)
        
        # 按文件分組
        files_dict = {}
        for ref in self.references:
            file_path = ref['file']
            if file_path not in files_dict:
                files_dict[file_path] = []
            files_dict[file_path].append(ref)
        
        for file_path, refs in files_dict.items():
            report_lines.append(f"\n文件: {file_path}")
            report_lines.append("-" * 40)
            
            for ref in refs:
                report_lines.append(f"  行 {ref['line']}: {ref['content']}")
        
        # 添加建議
        report_lines.append("\n" + "=" * 80)
        report_lines.append("建議的修復方法:")
        report_lines.append("1. 將 '.is_paid' 替換為 '.payment_status'")
        report_lines.append("2. 將 'is_paid=True' 替換為 \"payment_status='paid'\"")
        report_lines.append("3. 將 'is_paid=False' 替換為 \"payment_status='pending'\"")
        report_lines.append("4. 更新模板中的變量引用")
        
        return "\n".join(report_lines)


class Command(BaseCommand):
    help = '查找並報告對 is_paid 字段的引用'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自動修復找到的引用（謹慎使用）'
        )
    
    def handle(self, *args, **options):
        fix_mode = options['fix']
        project_root = Path.cwd()
        
        self.stdout.write("開始掃描 is_paid 字段引用...")
        
        cleaner = PaymentReferenceCleaner(project_root)
        references = cleaner.find_is_paid_references()
        
        # 生成報告
        report = cleaner.generate_report()
        self.stdout.write(report)
        
        if fix_mode:
            self.stdout.write("\n⚠️  自動修復功能尚未實現")
            self.stdout.write("請手動修復上述引用")
        
        # 統計信息
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("統計信息:")
        
        by_type = {}
        for ref in references:
            file_type = ref['type']
            by_type[file_type] = by_type.get(file_type, 0) + 1
        
        for file_type, count in by_type.items():
            self.stdout.write(f"  {file_type} 文件: {count} 個引用")
        
        if references:
            self.stdout.write("\n⚠️  發現需要修復的引用")
            self.stdout.write("請在運行支付狀態遷移後修復這些引用")
        else:
            self.stdout.write("\n✅ 未發現需要修復的引用")