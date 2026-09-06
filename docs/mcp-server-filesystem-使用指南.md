# MCP Server Filesystem 使用指南

## 概述
本指南詳細介紹如何通過 Cline AI Agent 使用 mcp-server-filesystem 工具進行文件系統操作。

## 📋 可用工具列表

安裝 mcp-server-filesystem 後，以下工具將自動可用：

### 1. 文件讀取工具
- `read_text_file` - 讀取文本文件內容
- `read_multiple_files` - 同時讀取多個文件
- `read_media_file` - 讀取圖像或音頻文件（Base64 編碼）

### 2. 文件寫入工具
- `write_file` - 創建新文件或完全覆蓋現有文件
- `edit_file` - 進行基於行的文件編輯

### 3. 目錄操作工具
- `list_directory` - 列出目錄內容
- `list_directory_with_sizes` - 列出帶大小的目錄內容
- `directory_tree` - 獲取遞歸樹狀視圖
- `create_directory` - 創建新目錄

### 4. 文件管理工具
- `move_file` - 移動或重命名文件
- `search_files` - 使用模式搜索文件
- `get_file_info` - 獲取文件詳細信息
- `list_allowed_directories` - 列出允許訪問的目錄

---

## 🚀 基本使用方法

### 方法一：直接通過 Cline AI Agent 使用
當您與 Cline AI Agent 對話時，可以直接請求文件操作：

```
請讀取文件 /home/kei/Desktop/betweencoffee_delivery_enhance/README.md
```

Cline AI Agent 會自動識別並使用 `read_text_file` 工具。

### 方法二：在代碼中明確調用
您也可以在對話中明確指定要使用的工具：

```
使用 read_text_file 工具讀取 manage.py 文件
```

---

## 📖 詳細工具使用示例

### 1. 讀取單個文件
```javascript
// Cline AI Agent 會自動調用
read_text_file('/home/kei/Desktop/betweencoffee_delivery_enhance/manage.py')
```

**對話示例**：
```
用戶：請讀取 manage.py 文件的前10行
Cline：我將使用 read_text_file 工具讀取該文件...
```

### 2. 讀取多個文件
```javascript
read_multiple_files([
  '/path/to/file1.txt',
  '/path/to/file2.txt',
  '/path/to/file3.txt'
])
```

**對話示例**：
```
用戶：同時讀取 requirements.txt 和 package.json 文件
Cline：我將使用 read_multiple_files 工具讀取這兩個文件...
```

### 3. 列出目錄內容
```javascript
list_directory('/home/kei/Desktop/betweencoffee_delivery_enhance')
```

**對話示例**：
```
用戶：列出項目根目錄下的所有文件
Cline：我將使用 list_directory 工具列出目錄內容...
```

### 4. 搜索文件
```javascript
search_files('/home/kei/Desktop/betweencoffee_delivery_enhance', '*.py')
```

**對話示例**：
```
用戶：搜索項目中所有的 Python 文件
Cline：我將使用 search_files 工具搜索 *.py 文件...
```

### 5. 創建新文件
```javascript
write_file('/home/kei/Desktop/betweencoffee_delivery_enhance/new_file.txt', '文件內容')
```

**對話示例**：
```
用戶：創建一個名為 test.txt 的文件，內容為 "Hello World"
Cline：我將使用 write_file 工具創建文件...
```

### 6. 編輯文件
```javascript
edit_file('/path/to/file.txt', [
  { oldText: '舊內容', newText: '新內容' }
])
```

**對話示例**：
```
用戶：將 manage.py 文件中的 "DEBUG = True" 改為 "DEBUG = False"
Cline：我將使用 edit_file 工具進行修改...
```

---

## 🔍 如何知道 Cline AI Agent 正在使用 file system 功能

### 視覺指示器
1. **工具調用提示**：Cline AI Agent 在執行文件操作前會顯示類似訊息：
   ```
   我將使用 read_text_file 工具讀取該文件...
   ```

2. **工具名稱顯示**：在對話中會明確提到使用的工具名稱

3. **執行結果反饋**：操作完成後會顯示結果摘要

### 日誌監控
您可以在系統日誌中查看 MCP 工具調用記錄：

```bash
# 查看 Claude Dev 的日誌
tail -f ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/logs/*
```

### 測試腳本
創建測試腳本監控工具調用：

```javascript
// test_tool_usage.js
console.log('監測 MCP 工具調用...');
// 這裡可以添加監控邏輯
```

---

## 🧪 實用測試場景

### 測試 1：驗證文件讀取功能
```
用戶：請讀取 README.md 文件並告訴我文件大小
Cline：我將使用 read_text_file 工具讀取文件，然後使用 get_file_info 獲取文件信息...
```

### 測試 2：驗證目錄瀏覽功能
```
用戶：顯示 static/js/ 目錄下的所有 JavaScript 文件
Cline：我將使用 list_directory 工具列出目錄，然後過濾 .js 文件...
```

### 測試 3：驗證文件搜索功能
```
用戶：在整個項目中搜索包含 "WebSocket" 的文件
Cline：我將使用 search_files 工具搜索文件，然後讀取內容進行匹配...
```

### 測試 4：驗證文件寫入功能
```
用戶：創建一個測試文件 test_mcp.txt，內容為當前時間戳
Cline：我將使用 write_file 工具創建文件...
```

---

## 📁 項目文件操作示例

### 1. 查看項目結構
```
用戶：顯示項目的完整目錄樹結構
Cline：我將使用 directory_tree 工具獲取項目結構...
```

### 2. 分析代碼文件
```
用戶：統計項目中有多少個 Python 文件
Cline：我將使用 search_files 搜索 *.py 文件，然後統計數量...
```

### 3. 檢查配置文件
```
用戶：查看 settings.py 文件中的數據庫配置
Cline：我將使用 read_text_file 讀取文件，然後提取數據庫配置部分...
```

### 4. 備份重要文件
```
用戶：備份 models.py 文件到 backup/ 目錄
Cline：我將使用 read_text_file 讀取文件，然後使用 write_file 寫入備份位置...
```

---

## ⚠️ 安全注意事項

### 權限控制
1. **訪問範圍限制**：配置為僅訪問項目目錄
2. **敏感文件保護**：避免操作包含敏感信息的文件
3. **備份重要數據**：重要操作前建議備份

### 操作確認
1. **寫入操作確認**：Cline AI Agent 通常會確認寫入操作
2. **刪除操作警告**：文件刪除操作會有明確警告
3. **路徑驗證**：工具會驗證路徑是否在允許範圍內

### 錯誤處理
1. **文件不存在**：工具會返回明確的錯誤信息
2. **權限不足**：會提示權限錯誤
3. **路徑無效**：會驗證路徑有效性

---

## 🔧 故障排除

### 常見問題 1：工具不可用
**症狀**：Cline AI Agent 不識別文件操作請求
**解決方案**：
1. 檢查 MCP 配置是否正確
2. 重啟 Claude Dev 擴展
3. 驗證 mcp-server-filesystem 是否正常運行

### 常見問題 2：權限錯誤
**症狀**：操作失敗，提示權限不足
**解決方案**：
1. 檢查文件/目錄權限
2. 驗證配置中的根目錄路徑
3. 確保在允許的目錄範圍內操作

### 常見問題 3：路徑錯誤
**症狀**：找不到文件或目錄
**解決方案**：
1. 使用絕對路徑而非相對路徑
2. 驗證路徑是否存在
3. 使用 `list_directory` 確認目錄內容

---

## 🎯 最佳實踐

### 1. 明確的路徑指定
```
✅ 好的做法：請讀取 /home/kei/Desktop/betweencoffee_delivery_enhance/manage.py
❌ 不好的做法：請讀取 manage.py（可能路徑不明確）
```

### 2. 逐步操作
```
✅ 好的做法：
1. 先列出目錄內容
2. 再讀取特定文件
3. 最後進行編輯

❌ 不好的做法：直接進行複雜的多步操作
```

### 3. 操作確認
```
✅ 好的做法：在寫入或刪除文件前要求確認
❌ 不好的做法：直接執行可能破壞性的操作
```

### 4. 錯誤處理
```
✅ 好的做法：預期可能錯誤並提供備用方案
❌ 不好的做法：假設所有操作都會成功
```

---

## 📊 監控工具使用情況

### 1. 創建使用日誌
```javascript
// 記錄工具調用
function logToolUsage(toolName, parameters) {
  console.log(`[${new Date().toISOString()}] 工具調用: ${toolName}`);
  console.log(`參數: ${JSON.stringify(parameters)}`);
}
```

### 2. 監控特定工具
```bash
# 監控 read_text_file 調用
grep -r "read_text_file" ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/logs/
```

### 3. 統計工具使用頻率
```python
# 分析工具使用統計
import json
from collections import Counter

# 讀取日誌文件，統計工具調用次數
```

---

## 🔄 與其他 MCP 工具協同工作

### 1. 與 mcp-server-fetch 結合
```
用戶：從網頁獲取內容，然後保存到本地文件
Cline：我將使用 mcp-server-fetch 獲取網頁內容，然後使用 write_file 保存到文件...
```

### 2. 與 simple-postgres 結合
```
用戶：從數據庫導出數據到 CSV 文件
Cline：我將使用 simple-postgres 查詢數據，然後使用 write_file 創建 CSV 文件...
```

### 3. 與 mcp-installer 結合
```
用戶：檢查項目依賴並生成報告文件
Cline：我將使用 mcp-installer 檢查依賴，然後使用 write_file 生成報告...
```

---

## 🚨 緊急情況處理

### 1. 意外文件刪除
**恢復步驟**：
1. 立即停止所有文件操作
2. 檢查備份文件
3. 使用版本控制系統恢復（如 git）

### 2. 配置錯誤
**恢復步驟**：
1. 從備份恢復配置文件
2. 重新啟動 MCP 伺服器
3. 驗證配置正確性

### 3. 工具故障
**恢復步驟**：
1. 重啟 mcp-server-filesystem
2. 檢查伺服器日誌
3. 重新安裝必要時

---

## 📈 進階使用技巧

### 1. 批量文件處理
```
用戶：將所有 .js 文件中的 "var" 替換為 "const"
Cline：我將：
1. 使用 search_files 找到所有 .js 文件
2. 對每個文件使用 read_text_file 讀取
3. 使用 edit_file 進行替換
4. 使用 write_file 保存修改
```

### 2. 文件內容分析
```
用戶：分析項目中所有 Python 文件的導入語句
Cline：我將：
1. 搜索所有 .py 文件
2. 讀取每個文件內容
3. 提取 import 語句
4. 統計最常用的庫
```

### 3. 自動化文檔生成
```
用戶：為項目生成文件結構文檔
Cline：我將：
1. 使用 directory_tree 獲取完整結構
2. 使用 get_file_info 獲取文件信息
3. 使用 write_file 生成 Markdown 文檔
```

---

## 💡 實用命令參考

### 常用文件操作命令
```
# 讀取文件
read_text_file('路徑/文件名')

# 寫入文件  
write_file('路徑/文件名', '內容')

# 列出目錄
list_directory('目錄路徑')

# 搜索文件
search_files('目錄路徑', '*.擴展名')

# 獲取文件信息
get_file_info('文件路徑')
```

### 路徑處理提示
```
# 使用絕對路徑
/home/kei/Desktop/betweencoffee_delivery_enhance/manage.py

# 項目相對路徑（從配置的根目錄開始）
manage.py
static/css/style.css
templates/base.html
```

---

## 🏁 快速開始檢查清單

### 環境驗證
- [ ] MCP 配置正確
- [ ] mcp-server-filesystem 正常運行
- [ ] 路徑權限設置正確

### 功能測試
- [ ] 文件讀取功能正常
- [ ] 目錄列表功能正常
- [ ] 文件搜索功能正常
- [ ] 文件寫入功能正常

### 安全檢查
- [ ] 訪問範圍限制正確
- [ ] 重要文件已備份
- [ ] 操作確認機制有效

---

## 📞 獲取幫助

### 1. 官方文檔
- MCP 官方文檔：https://modelcontextprotocol.io
- mcp-server-filesystem GitHub：https://github.com/modelcontextprotocol/servers

### 2. 社區支持
- MCP 開發者 Discord
- Claude Dev 社區論壇

### 3. 本地幫助
```bash
# 查看伺服器幫助
npx @modelcontextprotocol/server-filesystem --help

# 檢查配置
cat ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

---

## 總結

通過本指南，您應該能夠：

1. **理解可用工具**：知道有哪些文件系統工具可用
2. **正確使用工具**：通過適當的對話方式調用工具
3. **監控工具使用**：了解如何確認工具正在被調用
4. **處理常見問題**：解決使用過程中遇到的問題
5. **遵循最佳實踐**：安全高效地使用文件系統功能

記住，Cline AI Agent 會自動識別您的文件操作需求並調用相應的 MCP 工具。您只需要以自然語言描述您想要的操作即可。

**最後更新**: 2026年4月5日  
**適用版本**: mcp-server-filesystem 2026.1.14  
**配置路徑**: `/home/kei/Desktop/betweencoffee_delivery_enhance`