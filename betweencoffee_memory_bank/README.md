# Between Coffee Memory Bank

## 📚 概述

Between Coffee Memory Bank 是一個持久化的項目知識庫，專門為 Cline AI 助理設計，用於存儲和管理 Between Coffee 系統的完整項目上下文信息。

### 主要目的
1. **持久化項目知識**: 保存項目的技術架構、業務邏輯、開發標準等關鍵信息
2. **AI助理上下文**: 為 Cline AI 助理提供完整的項目背景，減少重複解釋
3. **項目狀態跟踪**: 記錄系統當前狀態、已知問題和優先任務
4. **知識傳承**: 便於新開發者快速了解項目，減少學習成本

## 🏗️ 系統架構

### 目錄結構
```
betweencoffee_memory_bank/
├── README.md                          # 本文件
├── 00_PROJECT_OVERVIEW.md            # 項目總覽和業務背景
├── 01_TECHNICAL_ARCHITECTURE.md      # 技術架構和系統設計
├── 02_BUSINESS_LOGIC.md              # 業務邏輯和流程（待創建）
├── 03_DEVELOPMENT_STANDARDS.md       # 開發標準和最佳實踐
├── 04_SYSTEM_STATE.md                # 系統狀態和已知問題
├── 05_PRIORITY_TASKS.md              # 優先任務和實施計劃
├── 06_DECISION_LOG.md                # 技術決策記錄（待創建）
├── 07_KNOWLEDGE_BASE.md              # 知識庫和經驗總結（待創建）
├── 08_WORKFLOW_TEMPLATES.md          # 工作流模板（待創建）
└── config/
    ├── cline_config.json             # Cline 配置
    ├── auto_load_script.py           # 自動載入腳本
    └── validation_tests.py           # 驗證測試
```

### 核心文件說明

#### 1. 項目總覽 (00_PROJECT_OVERVIEW.md)
- 項目基本信息和業務背景
- 核心業務流程和價值主張
- 系統架構概覽和技術棧
- 項目狀態和歷史記錄

#### 2. 技術架構 (01_TECHNICAL_ARCHITECTURE.md)
- 詳細的技術架構設計
- 系統組件和模塊關係
- 數據庫設計和API接口
- 部署架構和配置

#### 3. 開發標準 (03_DEVELOPMENT_STANDARDS.md)
- 代碼質量要求和文檔標準
- 安全要求和性能優化
- Django和前端開發規範
- 部署和維護流程

#### 4. 系統狀態 (04_SYSTEM_STATE.md)
- 當前系統健康狀態評估
- 核心功能完整度分析
- 已知問題和限制
- 性能指標和監控

#### 5. 優先任務 (05_PRIORITY_TASKS.md)
- 任務優先級分類和定義
- 緊急任務詳細描述和解決方案
- 實施步驟和工作量評估
- 任務管理流程

## 🚀 快速開始

### 1. 手動載入 Memory Bank
```bash
# 進入項目根目錄
cd /home/kei/Desktop/betweencoffee_delivery_enhance

# 運行自動載入腳本
python betweencoffee_memory_bank/config/auto_load_script.py

# 僅驗證 Memory Bank 結構
python betweencoffee_memory_bank/config/auto_load_script.py --validate-only

# 保存上下文到文件
python betweencoffee_memory_bank/config/auto_load_script.py --output context.txt
```

### 2. 在 Python 代碼中使用
```python
from betweencoffee_memory_bank.config.auto_load_script import load_memory_bank

# 載入 Memory Bank
context = load_memory_bank()

# 使用上下文
print(f"載入的上下文大小: {len(context)} 字符")
```

### 3. 運行驗證測試
```bash
# 運行所有驗證測試
python betweencoffee_memory_bank/config/validation_tests.py

# 發現錯誤時退出碼為1
python betweencoffee_memory_bank/config/validation_tests.py --exit-on-error
```

## 🔧 配置說明

### 配置文件 (cline_config.json)
配置文件定義了 Memory Bank 的結構和行為：

```json
{
  "memory_bank": {
    "name": "Between Coffee System Memory Bank",
    "version": "1.0.0",
    "description": "持久化項目上下文和知識庫"
  },
  "auto_load_config": {
    "enabled": true,
    "load_order": ["00_PROJECT_OVERVIEW.md", "01_TECHNICAL_ARCHITECTURE.md"],
    "max_tokens_per_file": 8000,
    "summarize_large_files": true
  },
  "validation": {
    "required_files": ["00_PROJECT_OVERVIEW.md", "01_TECHNICAL_ARCHITECTURE.md"],
    "check_timestamps": true,
    "max_file_age_days": 30
  }
}
```

### 配置選項說明

#### auto_load_config
- **load_order**: 文件載入順序，影響上下文組織
- **max_tokens_per_file**: 單個文件最大token數，超過會創建摘要
- **summarize_large_files**: 是否為大文件創建摘要

#### validation
- **required_files**: 必要文件列表，驗證時檢查
- **check_timestamps**: 是否檢查文件時間戳
- **max_file_age_days**: 文件最大年齡（天）

## 📊 驗證和測試

### 驗證測試內容
1. **文件結構驗證**: 檢查必要文件是否存在
2. **配置文件驗證**: 驗證配置文件的JSON格式和必要字段
3. **內容格式驗證**: 檢查Markdown格式和內容質量
4. **鏈接驗證**: 檢查內部鏈接是否有效
5. **時間戳驗證**: 檢查文件是否最近更新

### 測試結果解讀
- **✅ 通過**: 測試完全通過
- **⚠️ 警告**: 有問題但不影響功能，建議修復
- **❌ 錯誤**: 嚴重問題，需要立即修復

## 🔄 維護和更新

### 更新流程
1. **定期更新**: 每次重要變更後更新相關文檔
2. **版本控制**: 使用Git管理Memory Bank變更
3. **備份策略**: 重要更新前備份現有文件

### 更新指南
```bash
# 1. 檢查當前狀態
python betweencoffee_memory_bank/config/validation_tests.py

# 2. 更新文檔內容
# 編輯相應的 .md 文件

# 3. 更新配置文件（如果需要）
# 編輯 config/cline_config.json

# 4. 驗證更新
python betweencoffee_memory_bank/config/validation_tests.py --exit-on-error

# 5. 測試載入功能
python betweencoffee_memory_bank/config/auto_load_script.py --validate-only
```

### 最佳實踐
1. **保持時效性**: 重要變更後立即更新相關文檔
2. **版本對應**: Memory Bank版本應與項目版本對應
3. **定期審查**: 每月審查一次Memory Bank內容
4. **錯誤修復**: 發現問題時及時修復並更新

## 🎯 使用場景

### 1. 新任務開始時
```python
# 在Cline任務開始時自動載入
context = load_memory_bank()
# 將context作為系統提示詞的一部分
```

### 2. 項目交接時
- 新開發者通過Memory Bank快速了解項目
- 減少口頭解釋和文檔查找時間
- 確保知識傳承的一致性

### 3. 技術決策時
- 參考技術架構和開發標準
- 了解系統當前狀態和限制
- 查看優先任務和實施計劃

### 4. 問題排查時
- 查看已知問題和解決方案
- 參考系統配置和部署信息
- 了解性能指標和監控點

## 📈 性能考慮

### 上下文大小管理
- **默認配置**: 每個文件最大8000 tokens
- **摘要功能**: 大文件自動創建摘要
- **載入順序**: 按重要性排序載入文件

### 優化建議
1. **分塊載入**: 根據任務類型選擇性載入
2. **緩存機制**: 頻繁使用的上下文可以緩存
3. **增量更新**: 只更新變更的部分

## 🔗 集成指南

### 與 Cline 集成
1. **自動載入**: 配置Cline在任務開始時自動運行載入腳本
2. **上下文注入**: 將生成的上下文作為系統提示詞
3. **定期更新**: 設置定時任務更新Memory Bank

### 與現有文檔集成
- **.clinerules**: 參考現有的開發規範
- **綜合工作總結**: 整合歷史工作記錄
- **技術文檔**: 鏈接到詳細技術文檔

### 與開發流程集成
- **代碼審查**: 參考開發標準進行審查
- **測試流程**: 根據系統狀態設計測試用例
- **部署流程**: 參考部署配置和監控

## 🛠️ 故障排除

### 常見問題

#### 1. 配置文件錯誤
```
錯誤: 配置文件 JSON 格式錯誤
解決: 檢查 config/cline_config.json 的JSON格式
```

#### 2. 文件缺失
```
錯誤: 缺少必要文件: 00_PROJECT_OVERVIEW.md
解決: 創建缺失的文件或更新配置文件
```

#### 3. 文件過大
```
警告: 文件較大 (12000 tokens)，創建摘要
解決: 考慮拆分文件或調整 max_tokens_per_file 配置
```

#### 4. 鏈接損壞
```
錯誤: 鏈接 '技術文檔' -> './docs/tech.md' 不存在
解決: 修復鏈接或創建目標文件
```

### 調試方法
```bash
# 詳細調試信息
python -m pdb betweencoffee_memory_bank/config/auto_load_script.py

# 檢查配置文件
python -m json.tool betweencoffee_memory_bank/config/cline_config.json

# 檢查文件大小
find betweencoffee_memory_bank -name "*.md" -exec wc -c {} \;
```

## 📝 貢獻指南

### 貢獻流程
1. **Fork 倉庫**: 創建自己的分支
2. **創建分支**: `git checkout -b feature/update-memory-bank`
3. **提交變更**: 遵循約定式提交規範
4. **運行測試**: 確保所有測試通過
5. **創建PR**: 提交Pull Request

### 提交規範
```
feat: 新增功能或文件
fix: 修復問題或錯誤
docs: 文檔更新
refactor: 代碼重構
test: 測試相關
chore: 配置或工具變更
```

### 質量要求
1. **文檔完整**: 所有新增內容必須有完整文檔
2. **測試覆蓋**: 新增功能必須有對應測試
3. **格式規範**: 遵循現有的格式和風格
4. **鏈接有效**: 所有內部鏈接必須有效

## 📞 支持和反饋

### 問題報告
1. **GitHub Issues**: 在項目倉庫創建Issue
2. **詳細描述**: 提供問題的詳細描述和重現步驟
3. **環境信息**: 提供操作系統、Python版本等信息
4. **錯誤日誌**: 附上完整的錯誤日誌

### 功能請求
1. **使用場景**: 描述具體的使用場景和需求
2. **預期效果**: 說明期望的功能和效果
3. **優先級**: 標註功能的優先級和重要性
4. **相關鏈接**: 提供相關的參考資料或鏈接

### 聯繫方式
- **項目倉庫**: https://github.com/pythonkei/betweencoffee_delivery_enhance
- **問題跟踪**: GitHub Issues
- **文檔更新**: 通過Pull Request提交

## 📜 許可證和版權

### 許可證
本 Memory Bank 遵循與 Between Coffee 項目相同的許可證。

### 版權聲明
© 2026 Between Coffee 項目團隊。保留所有權利。

### 使用限制
1. **內部使用**: 主要用於 Between Coffee 項目內部
2. **知識共享**: 鼓勵在團隊內部共享知識
3. **保密要求**: 敏感信息應適當處理

---

**最後更新**: 2026年4月5日  
**版本**: 1.0.0  
**維護者**: Between Coffee 項目團隊  

*此文件為 Between Coffee Memory Bank 的使用指南，幫助用戶了解和使用 Memory Bank 系統。*