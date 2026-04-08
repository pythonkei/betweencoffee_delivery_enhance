#!/usr/bin/env python3
"""
Between Coffee 上下文自動加載器

這個腳本用於在 Cline 任務開始時自動加載項目上下文。
可以集成到 Cline 的啟動流程中，或作為手動命令使用。

使用方法:
1. 直接運行: python load_betweencoffee_context.py
2. 集成到 Cline: 在 Cline 配置中設置自動運行
3. 手動調用: 在任務開始時運行此腳本
"""

import os
import sys
import json
from pathlib import Path

def load_clinerules():
    """加載 .clinerules 文件內容"""
    clinerules_path = Path(".clinerules")
    if clinerules_path.exists():
        try:
            with open(clinerules_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ 已加載 .clinerules ({len(content)} 字符)")
            return content
        except Exception as e:
            print(f"❌ 加載 .clinerules 失敗: {e}")
    else:
        print("⚠️  .clinerules 文件不存在")
    return None

def load_memory_bank_summary():
    """加載 Memory Bank 摘要內容"""
    memory_bank_path = Path("betweencoffee_memory_bank")
    if not memory_bank_path.exists():
        print("⚠️  Memory Bank 目錄不存在")
        return None
    
    # 加載配置文件
    config_path = memory_bank_path / "config" / "cline_config.json"
    if not config_path.exists():
        print("⚠️  Memory Bank 配置文件不存在")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 已加載 Memory Bank 配置 (版本: {config.get('memory_bank', {}).get('version', '未知')})")
        
        # 創建摘要內容
        summary_parts = []
        
        # 項目信息
        project_info = config.get('project', {})
        summary_parts.append(f"# Between Coffee 系統 - 上下文摘要")
        summary_parts.append(f"**項目**: {project_info.get('name', '未知')}")
        summary_parts.append(f"**狀態**: {project_info.get('status', '未知')}")
        summary_parts.append(f"**版本**: {project_info.get('version', '未知')}")
        summary_parts.append("")
        
        # 技術棧
        tech_stack = config.get('technology_stack', {})
        summary_parts.append(f"## 技術棧")
        for category, items in tech_stack.items():
            if items:
                summary_parts.append(f"- **{category}**: {', '.join(items)}")
        summary_parts.append("")
        
        # 核心模塊
        core_modules = config.get('core_modules', {})
        summary_parts.append(f"## 核心模塊")
        for module, description in core_modules.items():
            summary_parts.append(f"- **{module}**: {description}")
        summary_parts.append("")
        
        # 系統狀態摘要（從 04_SYSTEM_STATE.md 提取關鍵信息）
        system_state_path = memory_bank_path / "04_SYSTEM_STATE.md"
        if system_state_path.exists():
            try:
                with open(system_state_path, 'r', encoding='utf-8') as f:
                    system_state = f.read()
                # 提取關鍵部分
                lines = system_state.split('\n')
                key_sections = []
                current_section = []
                in_key_section = False
                
                for line in lines:
                    if line.startswith('## ') and ('狀態' in line or '問題' in line or '優先' in line):
                        if current_section:
                            key_sections.append('\n'.join(current_section))
                        current_section = [line]
                        in_key_section = True
                    elif in_key_section and line.startswith('## '):
                        key_sections.append('\n'.join(current_section))
                        current_section = [line]
                    elif in_key_section:
                        current_section.append(line)
                
                if current_section:
                    key_sections.append('\n'.join(current_section))
                
                if key_sections:
                    summary_parts.append(f"## 系統狀態摘要")
                    summary_parts.extend(key_sections[:3])  # 只取前3個關鍵部分
                    summary_parts.append("")
            except Exception as e:
                print(f"⚠️  加載系統狀態摘要失敗: {e}")
        
        # 優先任務摘要（從 05_PRIORITY_TASKS.md 提取）
        priority_tasks_path = memory_bank_path / "05_PRIORITY_TASKS.md"
        if priority_tasks_path.exists():
            try:
                with open(priority_tasks_path, 'r', encoding='utf-8') as f:
                    priority_content = f.read()
                # 提取高優先級任務
                lines = priority_content.split('\n')
                high_priority = []
                in_high_priority = False
                
                for line in lines:
                    if '高優先級' in line or '立即處理' in line:
                        in_high_priority = True
                    elif in_high_priority and line.startswith('### '):
                        break
                    elif in_high_priority and line.strip().startswith('1.'):
                        high_priority.append(line.strip())
                
                if high_priority:
                    summary_parts.append(f"## 高優先級任務")
                    for task in high_priority[:5]:  # 只取前5個
                        summary_parts.append(f"- {task}")
                    summary_parts.append("")
            except Exception as e:
                print(f"⚠️  加載優先任務摘要失敗: {e}")
        
        full_summary = "\n".join(summary_parts)
        print(f"✅ 已生成 Memory Bank 摘要 ({len(full_summary)} 字符)")
        return full_summary
        
    except Exception as e:
        print(f"❌ 加載 Memory Bank 失敗: {e}")
        return None

def generate_context():
    """生成完整的上下文內容"""
    print("=" * 60)
    print("🚀 Between Coffee 上下文加載器")
    print("=" * 60)
    
    # 加載 .clinerules
    clinerules_content = load_clinerules()
    
    # 加載 Memory Bank 摘要
    memory_bank_summary = load_memory_bank_summary()
    
    # 組合上下文
    context_parts = []
    
    if clinerules_content:
        context_parts.append("# 📋 項目規範 (.clinerules)")
        context_parts.append(clinerules_content[:2000] + "..." if len(clinerules_content) > 2000 else clinerules_content)
        context_parts.append("")
    
    if memory_bank_summary:
        context_parts.append(memory_bank_summary)
    
    if not context_parts:
        print("❌ 未成功加載任何上下文內容")
        return None
    
    full_context = "\n".join(context_parts)
    
    # 添加使用說明
    usage_note = """
## 📖 使用說明

此上下文提供了 Between Coffee 系統的關鍵信息：

### 包含內容
1. **項目規範** (.clinerules): 開發標準、安全要求、性能優化
2. **項目總覽**: 業務背景、技術棧、核心模塊
3. **系統狀態**: 當前狀態、已知問題、性能指標
4. **優先任務**: 高優先級待處理問題

### 使用建議
- 在開始任何任務前，先查看相關規範
- 參考系統狀態了解當前限制
- 優先處理高優先級任務
- 遵循項目開發標準

### 完整信息
如需完整信息，請查看：
- `betweencoffee_memory_bank/` 目錄下的詳細文件
- `docs/` 目錄下的技術文檔和報告
"""
    
    full_context += usage_note
    
    print("=" * 60)
    print("✅ 上下文加載完成!")
    print(f"   上下文大小: {len(full_context)} 字符, ~{len(full_context)//4} tokens")
    print("=" * 60)
    
    return full_context

def save_context_to_file(context, filename="betweencoffee_context.txt"):
    """保存上下文到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(context)
        print(f"📁 上下文已保存到: {filename}")
        return True
    except Exception as e:
        print(f"❌ 保存上下文失敗: {e}")
        return False

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Between Coffee 上下文加載器')
    parser.add_argument('--output', type=str, help='輸出文件路徑（可選）', default="betweencoffee_context.txt")
    parser.add_argument('--summary-only', action='store_true', help='僅生成摘要，不包含完整 .clinerules')
    
    args = parser.parse_args()
    
    context = generate_context()
    
    if context:
        if args.output:
            save_context_to_file(context, args.output)
        
        # 顯示部分內容預覽
        print("\n" + "=" * 60)
        print("上下文預覽 (前1000字符):")
        print("=" * 60)
        print(context[:1000] + "..." if len(context) > 1000 else context)
        print("=" * 60)
        
        sys.exit(0)
    else:
        print("❌ 上下文生成失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()