# MCP Server Tavily 使用指南

## 概述

Tavily MCP 伺服器是一個基於 Model Context Protocol (MCP) 的搜索工具，專門為 AI 助手提供網絡搜索功能。它使用 Tavily API 進行高效、準確的網絡搜索，並將結果格式化為 AI 友好的格式。

## 安裝與配置

### 1. 系統要求
- Node.js 18 或更高版本
- Tavily API Key（免費或付費帳戶）

### 2. 安裝步驟

#### 方法一：使用 uvx 安裝（推薦）
```bash
uvx install @modelcontextprotocol/sdk
npm install axios
```

#### 方法二：手動安裝
```bash
npm install @modelcontextprotocol/sdk axios
```

### 3. 配置 Tavily API Key

#### 獲取 API Key
1. 訪問 [Tavily 官網](https://tavily.com)
2. 註冊帳戶
3. 在儀表板中獲取 API Key

#### 設置環境變數
```bash
export TAVILY_API_KEY="your_api_key_here"
```

#### 在 MCP 設定文件中配置
編輯 MCP 設定文件（通常位於 `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`）：

```json
{
  "mcpServers": {
    "simple-tavily-search": {
      "command": "node",
      "args": ["/path/to/simple-tavily-mcp.js"],
      "env": {
        "TAVILY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 可用工具

### 1. `search_tavily` - 基本搜索工具

#### 功能描述
使用 Tavily API 進行網絡搜索，返回格式化結果。

#### 參數說明
| 參數 | 類型 | 必填 | 默認值 | 描述 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索查詢關鍵字 |
| `max_results` | number | ❌ | 5 | 最大結果數量 (1-10) |
| `include_answer` | boolean | ❌ | true | 是否包含 AI 生成的答案 |
| `search_depth` | string | ❌ | "basic" | 搜索深度 ("basic" 或 "advanced") |

#### 使用示例
```javascript
// 基本搜索
search_tavily({
  query: "咖啡店管理系統",
  max_results: 5,
  include_answer: true
});

// 進階搜索
search_tavily({
  query: "Django WebSocket 最佳實踐",
  max_results: 8,
  search_depth: "advanced"
});
```

### 2. `search_tavily_with_options` - 進階搜索工具

#### 功能描述
提供更多選項的 Tavily 搜索，包括原始內容和圖片。

#### 參數說明
| 參數 | 類型 | 必填 | 默認值 | 描述 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索查詢關鍵字 |
| `max_results` | number | ❌ | 5 | 最大結果數量 (1-10) |
| `include_answer` | boolean | ❌ | true | 是否包含 AI 生成的答案 |
| `include_raw_content` | boolean | ❌ | false | 是否包含原始內容 |
| `search_depth` | string | ❌ | "basic" | 搜索深度 ("basic" 或 "advanced") |
| `include_images` | boolean | ❌ | false | 是否包含圖片 |

#### 使用示例
```javascript
// 完整選項搜索
search_tavily_with_options({
  query: "咖啡店 POS 系統比較",
  max_results: 10,
  include_answer: true,
  include_raw_content: true,
  search_depth: "advanced",
  include_images: true
});
```

## 輸出格式

### 基本搜索結果格式
```
# Tavily 搜索結果: "查詢關鍵字"

**搜索統計:**
- 查詢: 咖啡店管理系統
- 響應時間: 1.08秒
- 結果數量: 5
- 請求 ID: ff6a360e-1c8c-4b7c-b1aa-bf6b3ac6f977

**搜索結果:**

**1. 搜索结果标题**
網址: https://example.com
相關度: 84.9%
內容: 搜索结果摘要...

**2. 另一个搜索结果**
網址: https://example2.com
相關度: 76.5%
內容: 搜索结果摘要...

**AI 答案:**
AI 生成的答案内容...
```

### 進階搜索結果格式
```
# Tavily 進階搜索結果: "查詢關鍵字"

## 搜索詳情
- **查詢**: 咖啡店 POS 系統比較
- **響應時間**: 1.23秒
- **結果數量**: 10
- **搜索深度**: advanced
- **請求 ID**: abc123def456

## 後續問題建議
1. 哪個 POS 系統最適合小型咖啡店？
2. 如何選擇適合的 POS 系統？
3. POS 系統的主要功能有哪些？

## AI 生成的答案
詳細的 AI 生成答案...

## 搜索結果 (10 個)

### 1. 搜索结果标题
- **網址**: https://example.com
- **相關度**: 89.5%
- **內容**: 搜索结果摘要...
- **原始內容**: 原始內容摘要...

### 2. 另一个搜索结果
- **網址**: https://example2.com
- **相關度**: 82.3%
- **內容**: 搜索结果摘要...

## 相關圖片
1. https://example.com/image1.jpg
2. https://example.com/image2.jpg
```

## 在 Between Coffee 系統中的應用場景

### 1. 市場研究
```javascript
// 研究競爭對手
search_tavily({
  query: "咖啡店外帶系統 競爭對手",
  max_results: 8,
  search_depth: "advanced"
});

// 市場趨勢分析
search_tavily_with_options({
  query: "2024 咖啡店行業趨勢",
  include_answer: true,
  include_raw_content: true
});
```

### 2. 技術問題解決
```javascript
// 解決 Django 問題
search_tavily({
  query: "Django Channels WebSocket 連接中斷",
  max_results: 5,
  include_answer: true
});

// 性能優化建議
search_tavily_with_options({
  query: "PostgreSQL 查詢優化 索引策略",
  search_depth: "advanced"
});
```

### 3. 業務決策支持
```javascript
// 價格策略研究
search_tavily({
  query: "咖啡店定價策略 香港市場",
  max_results: 6
});

// 客戶體驗優化
search_tavily_with_options({
  query: "咖啡店客戶忠誠度計劃 最佳實踐",
  include_answer: true
});
```

## 最佳實踐

### 1. 查詢優化技巧
- **具體化查詢**: 使用具體的關鍵詞組合
  - ❌ "咖啡店系統"
  - ✅ "咖啡店外帶訂單管理系統 Django"
  
- **使用限定詞**: 添加時間、地點、類型等限定詞
  - "2024 年最佳咖啡店 POS 系統"
  - "香港小型咖啡店庫存管理"

- **問題形式**: 以問題形式提問獲得更準確的答案
  - "如何優化咖啡店訂單處理流程？"
  - "Django WebSocket 的最佳實踐是什麼？"

### 2. 參數選擇建議
- **日常使用**: 使用 `search_tavily` 基本工具
- **深度研究**: 使用 `search_tavily_with_options` 並啟用 `include_raw_content`
- **快速查詢**: 設置 `max_results: 3` 和 `search_depth: "basic"`
- **全面分析**: 設置 `max_results: 10` 和 `search_depth: "advanced"`

### 3. 錯誤處理
```javascript
// 錯誤處理示例
try {
  const result = await search_tavily({
    query: "查詢內容",
    max_results: 5
  });
  // 處理成功結果
} catch (error) {
  console.error("搜索失敗:", error.message);
  // 提供備用方案或重新嘗試
}
```

## 性能優化

### 1. 緩存策略
- 對於重複查詢，考慮實現本地緩存
- 設置合理的緩存過期時間（例如 1 小時）

### 2. 並發控制
- 避免同時發送大量搜索請求
- 實現請求隊列和速率限制

### 3. 結果過濾
- 根據相關度分數過濾低質量結果
- 使用自定義過濾器排除不相關網站

## 安全考慮

### 1. API Key 保護
- 永遠不要將 API Key 提交到版本控制系統
- 使用環境變數或密鑰管理服務
- 定期輪換 API Key

### 2. 輸入驗證
- 驗證查詢參數的類型和範圍
- 防止惡意查詢或注入攻擊
- 限制查詢長度和複雜度

### 3. 輸出過濾
- 過濾潛在的惡意內容
- 驗證返回的 URL 安全性
- 限制圖片和文件下載

## 故障排除

### 常見問題及解決方案

#### 1. API Key 無效
**症狀**: 搜索返回認證錯誤
**解決方案**:
- 檢查環境變數是否正確設置
- 驗證 API Key 是否有效
- 確認帳戶是否有足夠的額度

#### 2. 網絡連接問題
**症狀**: 請求超時或連接失敗
**解決方案**:
- 檢查網絡連接
- 增加請求超時時間
- 實現重試機制

#### 3. 結果質量不佳
**症狀**: 搜索結果不相關
**解決方案**:
- 優化查詢關鍵詞
- 調整搜索深度
- 增加結果數量

#### 4. 速率限制
**症狀**: 收到速率限制錯誤
**解決方案**:
- 降低請求頻率
- 實現指數退避重試
- 升級 API 計劃

## 監控與日誌

### 1. 日誌記錄
```javascript
// 在 MCP 伺服器中添加日誌
console.error('搜索請求:', {
  query: args.query,
  timestamp: new Date().toISOString(),
  duration: responseTime
});
```

### 2. 性能指標
- 平均響應時間
- 成功率
- 結果數量分布
- 錯誤率

### 3. 健康檢查
```bash
# 測試 MCP 伺服器健康狀態
node simple-tavily-mcp.js --health-check
```

## 擴展與自定義

### 1. 添加自定義工具
```javascript
// 在 simple-tavily-mcp.js 中添加新工具
{
  name: 'search_coffee_industry',
  description: '專門搜索咖啡行業相關資訊',
  inputSchema: {
    type: 'object',
    properties: {
      topic: {
        type: 'string',
        description: '搜索主題（如：技術、市場、趨勢等）'
      },
      region: {
        type: 'string',
        description: '地區限制'
      }
    },
    required: ['topic']
  }
}
```

### 2. 集成其他數據源
- 結合本地數據庫查詢
- 集成社交媒體數據
- 連接行業報告數據庫

### 3. 自定義結果處理
```javascript
// 添加結果後處理邏輯
function processSearchResults(data) {
  // 過濾、排序、格式化結果
  return enhancedResults;
}
```

## 更新與維護

### 1. 版本更新
```bash
# 更新依賴包
npm update @modelcontextprotocol/sdk axios

# 檢查新版本
npm outdated
```

### 2. 備份配置
```bash
# 備份 MCP 設定文件
cp ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json ~/backup/
```

### 3. 定期檢查
- 每月檢查 API Key 額度
- 每季度更新搜索策略
- 每年審查安全設置

## 附錄

### A. Tavily API 文檔鏈接
- [官方文檔](https://docs.tavily.com)
- [API 參考](https://docs.tavily.com/docs/api-reference)
- [最佳實踐](https://docs.tavily.com/docs/best-practices)

### B. MCP 相關資源
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP SDK GitHub](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP 規範](https://spec.modelcontextprotocol.io)

### C. 聯繫支持
- Tavily 支持: support@tavily.com
- MCP 社區: [Discord](https://discord.gg/modelcontextprotocol)
- 問題反饋: GitHub Issues

---

## 版本歷史

| 版本 | 日期 | 描述 |
|------|------|------|
| 1.0.0 | 2026-04-05 | 初始版本，包含基本和進階搜索工具 |
| 1.0.1 | 2026-04-05 | 修復 CommonJS 導入問題 |
| 1.0.2 | 2026-04-05 | 添加錯誤處理和日誌記錄 |

## 版權聲明

本文件是 Between Coffee 系統的一部分，版權所有 © 2026 Between Coffee。保留所有權利。

本指南僅供內部使用，未經許可不得分發或複製。

---

**最後更新**: 2026年4月5日  
**維護者**: Between Coffee 技術團隊  
**聯繫方式**: tech@betweencoffee.com