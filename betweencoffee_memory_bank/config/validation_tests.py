#!/usr/bin/env python3
"""
Between Coffee Memory Bank 驗證測試

此腳本用於驗證 Memory Bank 的完整性和正確性。
可以作為 CI/CD 流程的一部分運行，或在手動更新後驗證。

測試內容:
1. 文件結構驗證
2. 配置文件驗證
3. 內容格式驗證
4. 鏈接和引用驗證
5. 時間戳驗證
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set
import re

class MemoryBankValidator:
    """Memory Bank 驗證器類"""
    
    def __init__(self, memory_bank_path: str = None):
        """
        初始化 Memory Bank 驗證器
        
        Args:
            memory_bank_path: Memory Bank 目錄路徑
        """
        if memory_bank_path is None:
            self.memory_bank_path = Path.cwd() / "betweencoffee_memory_bank"
        else:
            self.memory_bank_path = Path(memory_bank_path)
        
        self.config_path = self.memory_bank_path / "config" / "cline_config.json"
        self.errors = []
        self.warnings = []
        self.passed_tests = 0
        self.total_tests = 0
        
    def run_all_tests(self) -> bool:
        """
        運行所有驗證測試
        
        Returns:
            所有測試是否通過
        """
        print("=" * 60)
        print("🧪 Between Coffee Memory Bank 驗證測試")
        print("=" * 60)
        
        test_methods = [
            self.test_config_file_exists,
            self.test_config_file_valid,
            self.test_required_files_exist,
            self.test_file_sizes_reasonable,
            self.test_markdown_formatting,
            self.test_no_broken_links,
            self.test_timestamps_recent,
            self.test_structure_consistency,
            self.test_content_quality,
        ]
        
        for test_method in test_methods:
            test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
            print(f"\n🔍 測試: {test_name}")
            print("-" * 40)
            
            try:
                test_method()
                self.total_tests += 1
            except Exception as e:
                self.errors.append(f"測試 {test_name} 執行失敗: {e}")
                print(f"❌ 測試執行失敗: {e}")
        
        # 輸出總結
        print("\n" + "=" * 60)
        print("📊 測試結果總結")
        print("=" * 60)
        
        passed_tests = self.total_tests - len(self.errors)
        print(f"✅ 通過測試: {passed_tests}/{self.total_tests}")
        
        if self.warnings:
            print(f"⚠️  警告: {len(self.warnings)} 個")
            for warning in self.warnings[:5]:  # 只顯示前5個警告
                print(f"   - {warning}")
            if len(self.warnings) > 5:
                print(f"   ... 還有 {len(self.warnings) - 5} 個警告")
        
        if self.errors:
            print(f"❌ 錯誤: {len(self.errors)} 個")
            for error in self.errors[:10]:  # 只顯示前10個錯誤
                print(f"   - {error}")
            if len(self.errors) > 10:
                print(f"   ... 還有 {len(self.errors) - 10} 個錯誤")
            
            print(f"\n❌ 驗證失敗: {len(self.errors)} 個錯誤需要修復")
            return False
        else:
            print(f"\n✅ 所有測試通過!")
            if self.warnings:
                print(f"   有 {len(self.warnings)} 個警告可以考慮修復")
            return True
    
    def test_config_file_exists(self):
        """測試配置文件是否存在"""
        if not self.config_path.exists():
            self.errors.append(f"配置文件不存在: {self.config_path}")
            print("❌ 配置文件不存在")
        else:
            self.passed_tests += 1
            print("✅ 配置文件存在")
    
    def test_config_file_valid(self):
        """測試配置文件是否有效 JSON"""
        if not self.config_path.exists():
            return  # 已在其他測試中報告
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 檢查必要字段
            required_fields = ['memory_bank', 'project', 'technology_stack']
            missing_fields = []
            
            for field in required_fields:
                if field not in config:
                    missing_fields.append(field)
            
            if missing_fields:
                self.errors.append(f"配置文件缺少必要字段: {', '.join(missing_fields)}")
                print(f"❌ 配置文件缺少 {len(missing_fields)} 個必要字段")
            else:
                self.passed_tests += 1
                print(f"✅ 配置文件格式正確 (版本: {config.get('memory_bank', {}).get('version', '未知')})")
                
        except json.JSONDecodeError as e:
            self.errors.append(f"配置文件 JSON 格式錯誤: {e}")
            print(f"❌ 配置文件 JSON 格式錯誤: {e}")
        except Exception as e:
            self.errors.append(f"讀取配置文件時發生錯誤: {e}")
            print(f"❌ 讀取配置文件時發生錯誤: {e}")
    
    def test_required_files_exist(self):
        """測試必要文件是否存在"""
        if not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_files = config.get('validation', {}).get('required_files', [])
            if not required_files:
                self.warnings.append("配置文件中未定義必要文件列表")
                print("⚠️  配置文件中未定義必要文件列表")
                return
            
            missing_files = []
            
            for file_name in required_files:
                file_path = self.memory_bank_path / file_name
                if not file_path.exists():
                    missing_files.append(file_name)
            
            if missing_files:
                self.errors.append(f"缺少必要文件: {', '.join(missing_files)}")
                print(f"❌ 缺少 {len(missing_files)} 個必要文件")
            else:
                self.passed_tests += 1
                print(f"✅ 所有 {len(required_files)} 個必要文件都存在")
                
        except Exception as e:
            self.errors.append(f"檢查必要文件時發生錯誤: {e}")
            print(f"❌ 檢查必要文件時發生錯誤: {e}")
    
    def test_file_sizes_reasonable(self):
        """測試文件大小是否合理"""
        max_size_mb = 5  # 最大文件大小 5MB
        min_size_kb = 1   # 最小文件大小 1KB
        
        md_files = list(self.memory_bank_path.glob("*.md"))
        
        if not md_files:
            self.warnings.append("未找到 Markdown 文件")
            print("⚠️  未找到 Markdown 文件")
            return
        
        problematic_files = []
        
        for file_path in md_files:
            try:
                file_size = file_path.stat().st_size
                file_size_kb = file_size / 1024
                file_size_mb = file_size_kb / 1024
                
                if file_size_mb > max_size_mb:
                    problematic_files.append((file_path.name, f"太大: {file_size_mb:.1f}MB"))
                elif file_size < min_size_kb * 1024:
                    problematic_files.append((file_path.name, f"太小: {file_size_kb:.1f}KB"))
                    
            except Exception as e:
                self.warnings.append(f"無法檢查文件大小 {file_path.name}: {e}")
        
        if problematic_files:
            for file_name, issue in problematic_files:
                self.warnings.append(f"文件大小問題: {file_name} ({issue})")
            print(f"⚠️  發現 {len(problematic_files)} 個文件大小問題")
        else:
            self.passed_tests += 1
            print(f"✅ 所有 {len(md_files)} 個文件大小合理")
    
    def test_markdown_formatting(self):
        """測試 Markdown 格式是否正確"""
        md_files = list(self.memory_bank_path.glob("*.md"))
        
        if not md_files:
            return
        
        formatting_issues = []
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                issues = self._check_markdown_formatting(content, file_path.name)
                if issues:
                    formatting_issues.extend(issues)
                    
            except Exception as e:
                self.warnings.append(f"無法檢查 Markdown 格式 {file_path.name}: {e}")
        
        if formatting_issues:
            for issue in formatting_issues[:5]:  # 只顯示前5個問題
                self.warnings.append(issue)
            print(f"⚠️  發現 {len(formatting_issues)} 個 Markdown 格式問題")
        else:
            self.passed_tests += 1
            print(f"✅ 所有 {len(md_files)} 個 Markdown 文件格式良好")
    
    def _check_markdown_formatting(self, content: str, file_name: str) -> List[str]:
        """檢查 Markdown 格式問題"""
        issues = []
        
        # 檢查是否有空標題
        empty_headings = re.findall(r'^#+\s*$', content, re.MULTILINE)
        if empty_headings:
            issues.append(f"{file_name}: 發現 {len(empty_headings)} 個空標題")
        
        # 檢查是否有孤立的標題（沒有內容）
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or next_line.startswith('#'):
                    issues.append(f"{file_name}: 第 {i+1} 行標題可能沒有內容")
        
        # 檢查是否有過長的段落（超過 10 行）
        paragraph_lines = 0
        for line in lines:
            if line.strip():
                paragraph_lines += 1
            else:
                if paragraph_lines > 10:
                    issues.append(f"{file_name}: 發現過長段落 ({paragraph_lines} 行)")
                paragraph_lines = 0
        
        return issues
    
    def test_no_broken_links(self):
        """測試沒有損壞的鏈接"""
        md_files = list(self.memory_bank_path.glob("*.md"))
        
        if not md_files:
            return
        
        broken_links = []
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找 Markdown 鏈接
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
                
                for link_text, link_url in links:
                    # 檢查內部文件鏈接
                    if link_url.startswith('./') or link_url.endswith('.md'):
                        target_path = self.memory_bank_path / link_url
                        if not target_path.exists():
                            broken_links.append(f"{file_path.name}: 鏈接 '{link_text}' -> '{link_url}' 不存在")
                
            except Exception as e:
                self.warnings.append(f"無法檢查鏈接 {file_path.name}: {e}")
        
        if broken_links:
            for link in broken_links[:5]:  # 只顯示前5個損壞鏈接
                self.errors.append(link)
            print(f"❌ 發現 {len(broken_links)} 個損壞鏈接")
        else:
            self.passed_tests += 1
            print(f"✅ 所有鏈接都有效")
    
    def test_timestamps_recent(self):
        """測試文件時間戳是否最近更新"""
        max_age_days = 30  # 最大允許天數
        
        md_files = list(self.memory_bank_path.glob("*.md"))
        
        if not md_files:
            return
        
        current_time = datetime.now()
        old_files = []
        
        for file_path in md_files:
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (current_time - file_mtime).total_seconds() / 86400
                
                if age_days > max_age_days:
                    old_files.append((file_path.name, age_days))
                    
            except Exception as e:
                self.warnings.append(f"無法檢查文件時間戳 {file_path.name}: {e}")
        
        if old_files:
            for file_name, age_days in old_files:
                self.warnings.append(f"{file_name}: {age_days:.1f} 天前更新")
            print(f"⚠️  發現 {len(old_files)} 個文件超過 {max_age_days} 天未更新")
        else:
            self.passed_tests += 1
            print(f"✅ 所有文件都在 {max_age_days} 天內更新過")
    
    def test_structure_consistency(self):
        """測試 Memory Bank 結構一致性"""
        if not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 檢查配置中定義的文件是否都存在
            defined_files = config.get('memory_bank_structure', {}).keys()
            existing_files = [f.name for f in self.memory_bank_path.glob("*.md")]
            
            missing_defined = []
            extra_existing = []
            
            for file_name in defined_files:
                if file_name not in existing_files:
                    missing_defined.append(file_name)
            
            for file_name in existing_files:
                if file_name not in defined_files:
                    extra_existing.append(file_name)
            
            issues = []
            if missing_defined:
                issues.append(f"配置中定義但文件缺失: {', '.join(missing_defined)}")
            if extra_existing:
                issues.append(f"文件存在但未在配置中定義: {', '.join(extra_existing)}")
            
            if issues:
                for issue in issues:
                    self.warnings.append(issue)
                print(f"⚠️  發現 {len(issues)} 個結構一致性問題")
            else:
                self.passed_tests += 1
                print(f"✅ Memory Bank 結構一致")
                
        except Exception as e:
            self.errors.append(f"檢查結構一致性時發生錯誤: {e}")
            print(f"❌ 檢查結構一致性時發生錯誤: {e}")
    
    def test_content_quality(self):
        """測試內容質量"""
        md_files = list(self.memory_bank_path.glob("*.md"))
        
        if not md_files:
            return
        
        quality_issues = []
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                issues = self._check_content_quality(content, file_path.name)
                if issues:
                    quality_issues.extend(issues)
                    
            except Exception as e:
                self.warnings.append(f"無法檢查內容質量 {file_path.name}: {e}")
        
        if quality_issues:
            for issue in quality_issues[:5]:  # 只顯示前5個問題
                self.warnings.append(issue)
            print(f"⚠️  發現 {len(quality_issues)} 個內容質量問題")
        else:
            self.passed_tests += 1
            print(f"✅ 所有文件內容質量良好")
    
    def _check_content_quality(self, content: str, file_name: str) -> List[str]:
        """檢查內容質量問題"""
        issues = []
        
        # 檢查是否有 TODO 或 FIXME
        todos = re.findall(r'(TODO|FIXME|XXX|HACK|BUG)', content, re.IGNORECASE)
        if todos:
            issues.append(f"{file_name}: 發現 {len(todos)} 個待辦事項標記")
        
        # 檢查是否有過長的句子（超過 200 字符）
        sentences = re.split(r'[.!?。！？]', content)
        long_sentences = [s for s in sentences if len(s.strip()) > 200]
        if long_sentences:
            issues.append(f"{file_name}: 發現 {len(long_sentences)} 個過長句子")
        
        # 檢查是否有重複的段落（簡單檢查）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        unique_paragraphs = set(paragraphs)
        if len(paragraphs) > len(unique_paragraphs) * 1.5:
            issues.append(f"{file_name}: 可能有多個重複段落")
        
        return issues

def run_validation(memory_bank_path: str = None) -> bool:
    """
    運行驗證的便捷函數
    
    Args:
        memory_bank_path: Memory Bank 目錄路徑
        
    Returns:
        驗證是否通過
    """
    validator = MemoryBankValidator(memory_bank_path)
    return validator.run_all_tests()

def main():
    """主函數：命令行入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Between Coffee Memory Bank 驗證測試')
    parser.add_argument('--path', type=str, help='Memory Bank 目錄路徑')
    parser.add_argument('--exit-on-error', action='store_true', help='發現錯誤時退出碼為1')
    
    args = parser.parse_args()
    
    is_valid = run_validation(args.path)
    
    if args.exit_on_error:
        sys.exit(0 if is_valid else 1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()