#!/usr/bin/env python3
"""
Between Coffee Memory Bank 使用演示

此腳本演示如何使用 Memory Bank 系統，包括：
1. 載入 Memory Bank 上下文
2. 查詢項目信息
3. 分析系統狀態
4. 查看優先任務
"""

import sys
from pathlib import Path

# 添加 config 目錄到 Python 路徑
config_dir = Path(__file__).parent / "config"
sys.path.insert(0, str(config_dir.parent))

from config.auto_load_script import load_memory_bank
from config.validation_tests import run_validation

def demo_basic_usage():
    """演示基本使用方式"""
    print("=" * 60)
    print("🧠 Between Coffee Memory Bank 使用演示")
    print("=" * 60)
    
    # 1. 載入 Memory Bank
    print("\n1. 📚 載入 Memory Bank 上下文...")
    context = load_memory_bank()
    
    if "Memory Bank 載入失敗" in context:
        print("❌ Memory Bank 載入失敗")
        print(context)
        return
    
    print(f"✅ Memory Bank 載入成功")
    print(f"   上下文大小: {len(context)} 字符")
    print(f"   估計 tokens: {len(context) // 4}")
    
    # 2. 顯示摘要信息
    print("\n2. 📊 顯示摘要信息...")
    
    # 從上下文中提取關鍵信息
    lines = context.split('\n')
    
    # 查找項目信息
    project_info = []
    tech_stack = []
    
    for i, line in enumerate(lines):
        if "**項目**:" in line:
            project_info.append(line.strip())
        elif "**狀態**:" in line:
            project_info.append(line.strip())
        elif "**版本**:" in line:
            project_info.append(line.strip())
        elif "**最後更新**:" in line:
            project_info.append(line.strip())
        elif "## 技術棧摘要" in line:
            # 獲取技術棧信息
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].startswith("##"):
                    tech_stack.append(lines[j].strip())
                else:
                    break
    
    print("📋 項目信息:")
    for info in project_info:
        print(f"   {info}")
    
    print("\n🔧 技術棧:")
    for tech in tech_stack:
        print(f"   {tech}")
    
    # 3. 運行驗證測試
    print("\n3. 🧪 運行驗證測試...")
    is_valid = run_validation()
    
    if is_valid:
        print("✅ Memory Bank 驗證通過")
    else:
        print("❌ Memory Bank 驗證失敗，請檢查問題")
    
    return context

def demo_context_analysis(context):
    """演示上下文分析"""
    print("\n" + "=" * 60)
    print("🔍 上下文分析")
    print("=" * 60)
    
    # 分析上下文結構
    lines = context.split('\n')
    
    # 統計各類信息
    sections = {}
    current_section = None
    
    for line in lines:
        if line.startswith("# "):
            current_section = line[2:].strip()
            sections[current_section] = sections.get(current_section, 0) + 1
        elif line.startswith("## "):
            subsection = line[3:].strip()
            sections[subsection] = sections.get(subsection, 0) + 1
    
    print("📊 上下文結構分析:")
    print(f"   總行數: {len(lines)}")
    print(f"   章節數量: {len(sections)}")
    
    # 顯示主要章節
    print("\n📑 主要章節:")
    for section, count in list(sections.items())[:10]:
        print(f"   • {section}")
    
    # 查找關鍵內容
    print("\n🔑 關鍵內容位置:")
    keywords = ["優先任務", "已知問題", "技術架構", "開發標準", "系統狀態"]
    
    for keyword in keywords:
        for i, line in enumerate(lines):
            if keyword in line:
                print(f"   {keyword}: 第 {i+1} 行附近")
                break
    
    # 檢查文件載入情況
    print("\n📁 載入的文件:")
    for i, line in enumerate(lines):
        if "### " in line and ".md" in line:
            print(f"   {line[4:].strip()}")

def demo_priority_tasks(context):
    """演示優先任務查詢"""
    print("\n" + "=" * 60)
    print("🎯 優先任務查詢")
    print("=" * 60)
    
    lines = context.split('\n')
    
    # 查找優先任務部分
    priority_section_start = -1
    for i, line in enumerate(lines):
        if "## 🚨 P0 - 緊急任務" in line or "## P0 - 緊急任務" in line:
            priority_section_start = i
            break
    
    if priority_section_start == -1:
        print("❌ 未找到優先任務部分")
        return
    
    print("🔴 緊急任務 (P0):")
    task_count = 0
    
    for i in range(priority_section_start, min(priority_section_start + 50, len(lines))):
        line = lines[i]
        
        if "### " in line and "ID重複問題" in line:
            print(f"\n1. {line[4:]}")
            task_count += 1
            # 顯示任務描述
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"   {lines[j].strip()}")
                else:
                    break
        
        elif "### " in line and "WebSocket連接穩定性" in line:
            print(f"\n2. {line[4:]}")
            task_count += 1
            # 顯示任務描述
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"   {lines[j].strip()}")
                else:
                    break
        
        if task_count >= 2:
            break
    
    if task_count == 0:
        print("⚠️  未找到具體的緊急任務")

def demo_system_state(context):
    """演示系統狀態查詢"""
    print("\n" + "=" * 60)
    print("📈 系統狀態查詢")
    print("=" * 60)
    
    lines = context.split('\n')
    
    # 查找系統狀態部分
    state_section_start = -1
    for i, line in enumerate(lines):
        if "## 📊 當前系統狀態概覽" in line or "系統狀態概覽" in line:
            state_section_start = i
            break
    
    if state_section_start == -1:
        print("❌ 未找到系統狀態部分")
        return
    
    print("🏥 系統健康狀態:")
    
    for i in range(state_section_start, min(state_section_start + 20, len(lines))):
        line = lines[i]
        
        if "✅" in line or "⚠️" in line or "❌" in line:
            print(f"   {line.strip()}")
        
        if "### 系統健康狀態" in line:
            # 顯示健康狀態
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"   {lines[j].strip()}")
                else:
                    break
    
    # 查找核心功能狀態
    print("\n🎯 核心功能狀態:")
    
    for i, line in enumerate(lines):
        if "## 🎯 核心功能狀態" in line or "核心功能狀態" in line:
            for j in range(i + 1, min(i + 15, len(lines))):
                if lines[j].strip() and ("✅" in lines[j] or "⚠️" in lines[j]):
                    print(f"   {lines[j].strip()}")
            break

def main():
    """主函數"""
    print("🚀 Between Coffee Memory Bank 演示腳本")
    print("=" * 60)
    
    # 演示基本使用
    context = demo_basic_usage()
    
    if context and "Memory Bank 載入失敗" not in context:
        # 演示其他功能
        demo_context_analysis(context)
        demo_priority_tasks(context)
        demo_system_state(context)
        
        print("\n" + "=" * 60)
        print("✅ 演示完成!")
        print("=" * 60)
        print("\n📝 使用建議:")
        print("1. 在 Cline 任務開始時自動載入 Memory Bank")
        print("2. 參考開發標準進行代碼開發")
        print("3. 根據優先任務安排工作")
        print("4. 定期更新 Memory Bank 內容")
    else:
        print("\n❌ 演示失敗，請檢查 Memory Bank 配置")

if __name__ == "__main__":
    main()