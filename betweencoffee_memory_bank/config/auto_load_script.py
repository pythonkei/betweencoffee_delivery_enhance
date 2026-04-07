#!/usr/bin/env python3
"""
Between Coffee Memory Bank 自動載入腳本

此腳本用於自動載入 Memory Bank 內容，為 Cline AI 助理提供項目上下文。
可以集成到 Cline 的啟動流程中，或在任務開始時手動運行。

使用方法:
1. 直接運行: python auto_load_script.py
2. 集成到 Cline: 在 Cline 配置中設置自動運行
3. 手動調用: 在任務開始時調用 load_memory_bank() 函數
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class MemoryBankLoader:
    """Memory Bank 載入器類"""
    
    def __init__(self, memory_bank_path: str = None):
        """
        初始化 Memory Bank 載入器
        
        Args:
            memory_bank_path: Memory Bank 目錄路徑，默認為當前目錄下的 betweencoffee_memory_bank
        """
        if memory_bank_path is None:
            # 默認路徑：當前工作目錄下的 betweencoffee_memory_bank
            self.memory_bank_path = Path.cwd() / "betweencoffee_memory_bank"
        else:
            self.memory_bank_path = Path(memory_bank_path)
        
        self.config_path = self.memory_bank_path / "config" / "cline_config.json"
        self.loaded_content = {}
        self.validation_errors = []
        
    def load_config(self) -> Optional[Dict]:
        """
        載入配置文件
        
        Returns:
            配置字典，如果載入失敗則返回 None
        """
        try:
            if not self.config_path.exists():
                self.validation_errors.append(f"配置文件不存在: {self.config_path}")
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"✅ 已載入 Memory Bank 配置 (版本: {config.get('memory_bank', {}).get('version', '未知')})")
            return config
            
        except json.JSONDecodeError as e:
            self.validation_errors.append(f"配置文件 JSON 解析錯誤: {e}")
            return None
        except Exception as e:
            self.validation_errors.append(f"載入配置文件時發生錯誤: {e}")
            return None
    
    def validate_memory_bank(self, config: Dict) -> bool:
        """
        驗證 Memory Bank 結構和文件
        
        Args:
            config: 配置字典
            
        Returns:
            驗證是否通過
        """
        print("🔍 驗證 Memory Bank 結構...")
        
        # 檢查必要文件
        required_files = config.get('validation', {}).get('required_files', [])
        missing_files = []
        
        for file_name in required_files:
            file_path = self.memory_bank_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            self.validation_errors.append(f"缺少必要文件: {', '.join(missing_files)}")
            print(f"❌ 缺少 {len(missing_files)} 個必要文件")
            return False
        
        # 檢查文件時間戳
        if config.get('validation', {}).get('check_timestamps', False):
            max_age_days = config.get('validation', {}).get('max_file_age_days', 30)
            old_files = self._check_file_ages(required_files, max_age_days)
            
            if old_files:
                print(f"⚠️  發現 {len(old_files)} 個文件超過 {max_age_days} 天未更新")
                for file_name, age_days in old_files:
                    print(f"   - {file_name}: {age_days:.1f} 天前更新")
        
        print(f"✅ Memory Bank 驗證通過 ({len(required_files)} 個必要文件存在)")
        return True
    
    def _check_file_ages(self, file_names: List[str], max_age_days: int) -> List[Tuple[str, float]]:
        """
        檢查文件年齡
        
        Args:
            file_names: 文件名列表
            max_age_days: 最大允許天數
            
        Returns:
            超過最大年齡的文件列表 (文件名, 天數)
        """
        old_files = []
        current_time = datetime.now()
        
        for file_name in file_names:
            file_path = self.memory_bank_path / file_name
            if file_path.exists():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (current_time - file_mtime).total_seconds() / 86400
                
                if age_days > max_age_days:
                    old_files.append((file_name, age_days))
        
        return old_files
    
    def load_memory_bank_files(self, config: Dict) -> Dict[str, str]:
        """
        載入 Memory Bank 文件內容
        
        Args:
            config: 配置字典
            
        Returns:
            文件名到內容的映射字典
        """
        print("📚 載入 Memory Bank 文件...")
        
        load_order = config.get('auto_load_config', {}).get('load_order', [])
        max_tokens = config.get('auto_load_config', {}).get('max_tokens_per_file', 8000)
        summarize_large = config.get('auto_load_config', {}).get('summarize_large_files', True)
        
        loaded_files = {}
        
        for file_name in load_order:
            file_path = self.memory_bank_path / file_name
            
            if not file_path.exists():
                print(f"⚠️  文件不存在，跳過: {file_name}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查文件大小
                estimated_tokens = len(content) // 4  # 粗略估計
                
                if estimated_tokens > max_tokens and summarize_large:
                    print(f"📄 文件較大 ({estimated_tokens} tokens)，創建摘要: {file_name}")
                    content = self._create_summary(content, file_name, max_tokens)
                
                loaded_files[file_name] = content
                print(f"✅ 已載入: {file_name} ({len(content)} 字符)")
                
            except Exception as e:
                print(f"❌ 載入文件失敗 {file_name}: {e}")
                self.validation_errors.append(f"載入文件失敗 {file_name}: {e}")
        
        self.loaded_content = loaded_files
        return loaded_files
    
    def _create_summary(self, content: str, file_name: str, max_tokens: int) -> str:
        """
        為大文件創建摘要
        
        Args:
            content: 原始內容
            file_name: 文件名
            max_tokens: 最大token數
            
        Returns:
            摘要內容
        """
        # 簡單的摘要策略：取開頭和結尾部分
        target_chars = max_tokens * 4  # 轉換為字符數
        
        if len(content) <= target_chars:
            return content
        
        # 取開頭 60% 和結尾 40%
        start_chars = int(target_chars * 0.6)
        end_chars = target_chars - start_chars
        
        summary = (
            f"# {file_name} - 摘要 (原始文件: {len(content)} 字符)\n\n"
            f"## 文件開頭部分:\n\n"
            f"{content[:start_chars]}\n\n"
            f"... [中間內容已省略] ...\n\n"
            f"## 文件結尾部分:\n\n"
            f"{content[-end_chars:]}\n\n"
            f"*註: 這是摘要版本，完整文件請查看 {file_name}*"
        )
        
        return summary
    
    def generate_context_prompt(self, config: Dict, loaded_files: Dict[str, str]) -> str:
        """
        生成上下文提示詞
        
        Args:
            config: 配置字典
            loaded_files: 已載入的文件內容
            
        Returns:
            上下文提示詞字符串
        """
        print("🧠 生成上下文提示詞...")
        
        # 基本項目信息
        project_info = config.get('project', {})
        tech_stack = config.get('technology_stack', {})
        
        prompt_parts = []
        
        # 1. 項目介紹
        prompt_parts.append(f"# Between Coffee 系統 - Memory Bank 上下文\n")
        prompt_parts.append(f"**項目**: {project_info.get('name', '未知')}")
        prompt_parts.append(f"**狀態**: {project_info.get('status', '未知')}")
        prompt_parts.append(f"**版本**: {project_info.get('version', '未知')}")
        prompt_parts.append(f"**最後更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 2. 技術棧摘要
        prompt_parts.append(f"## 技術棧摘要")
        for category, items in tech_stack.items():
            if items:
                prompt_parts.append(f"- **{category}**: {', '.join(items)}")
        
        prompt_parts.append("")
        
        # 3. 載入的文件內容
        prompt_parts.append(f"## Memory Bank 內容 ({len(loaded_files)} 個文件)")
        
        for file_name, content in loaded_files.items():
            prompt_parts.append(f"### {file_name}")
            prompt_parts.append(content)
            prompt_parts.append("")  # 空行分隔
        
        # 4. 使用說明
        prompt_parts.append(f"## 使用說明")
        prompt_parts.append("此上下文提供了 Between Coffee 系統的完整項目信息，包括：")
        prompt_parts.append("1. 項目總覽和業務背景")
        prompt_parts.append("2. 技術架構和系統設計")
        prompt_parts.append("3. 當前系統狀態和已知問題")
        prompt_parts.append("4. 優先任務和實施計劃")
        prompt_parts.append("5. 開發標準和最佳實踐")
        prompt_parts.append("")
        prompt_parts.append("在處理任何任務時，請參考這些信息確保符合項目規範和當前狀態。")
        
        full_prompt = "\n".join(prompt_parts)
        
        # 估計token數
        estimated_tokens = len(full_prompt) // 4
        print(f"📊 上下文提示詞生成完成: {len(full_prompt)} 字符, ~{estimated_tokens} tokens")
        
        return full_prompt
    
    def load_and_prepare_context(self) -> Tuple[Optional[str], List[str]]:
        """
        載入並準備上下文的主要函數
        
        Returns:
            (上下文提示詞, 錯誤列表)
        """
        print("=" * 60)
        print("🚀 Between Coffee Memory Bank 載入器")
        print("=" * 60)
        
        # 1. 載入配置
        config = self.load_config()
        if config is None:
            error_msg = "無法載入配置，請檢查 Memory Bank 結構"
            print(f"❌ {error_msg}")
            return None, self.validation_errors
        
        # 2. 驗證 Memory Bank
        if not self.validate_memory_bank(config):
            print("❌ Memory Bank 驗證失敗")
            return None, self.validation_errors
        
        # 3. 載入文件
        loaded_files = self.load_memory_bank_files(config)
        if not loaded_files:
            error_msg = "未成功載入任何文件"
            print(f"❌ {error_msg}")
            self.validation_errors.append(error_msg)
            return None, self.validation_errors
        
        # 4. 生成上下文提示詞
        context_prompt = self.generate_context_prompt(config, loaded_files)
        
        print("=" * 60)
        print("✅ Memory Bank 載入完成!")
        print(f"   載入文件: {len(loaded_files)} 個")
        print(f"   上下文大小: ~{len(context_prompt) // 4} tokens")
        
        if self.validation_errors:
            print(f"⚠️  發現 {len(self.validation_errors)} 個警告:")
            for error in self.validation_errors:
                print(f"   - {error}")
        
        print("=" * 60)
        
        return context_prompt, self.validation_errors

def load_memory_bank(memory_bank_path: str = None) -> str:
    """
    載入 Memory Bank 的便捷函數
    
    Args:
        memory_bank_path: Memory Bank 目錄路徑
        
    Returns:
        上下文提示詞字符串
    """
    loader = MemoryBankLoader(memory_bank_path)
    context_prompt, errors = loader.load_and_prepare_context()
    
    if context_prompt is None:
        error_summary = "\n".join(errors) if errors else "未知錯誤"
        return f"# Memory Bank 載入失敗\n\n錯誤:\n{error_summary}"
    
    return context_prompt

def main():
    """主函數：命令行入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Between Coffee Memory Bank 載入器')
    parser.add_argument('--path', type=str, help='Memory Bank 目錄路徑')
    parser.add_argument('--output', type=str, help='輸出文件路徑（可選）')
    parser.add_argument('--validate-only', action='store_true', help='僅驗證不生成上下文')
    
    args = parser.parse_args()
    
    loader = MemoryBankLoader(args.path)
    
    if args.validate_only:
        # 僅驗證模式
        config = loader.load_config()
        if config:
            is_valid = loader.validate_memory_bank(config)
            sys.exit(0 if is_valid else 1)
        else:
            print("❌ 配置載入失敗")
            sys.exit(1)
    else:
        # 完整載入模式
        context_prompt, errors = loader.load_and_prepare_context()
        
        if context_prompt:
            if args.output:
                # 輸出到文件
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(context_prompt)
                print(f"📁 上下文已保存到: {args.output}")
            else:
                # 輸出到控制台
                print("\n" + "=" * 60)
                print("生成的上下文提示詞:")
                print("=" * 60)
                print(context_prompt[:2000] + "..." if len(context_prompt) > 2000 else context_prompt)
            
            sys.exit(0)
        else:
            print("❌ Memory Bank 載入失敗")
            sys.exit(1)

if __name__ == "__main__":
    main()