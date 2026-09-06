# mcp-server-github 安裝與使用指南

## 📋 目錄
1. [安裝概述](#安裝概述)
2. [系統要求](#系統要求)
3. [安裝步驟](#安裝步驟)
4. [配置說明](#配置說明)
5. [可用工具](#可用工具)
6. [使用示例](#使用示例)
7. [安全建議](#安全建議)
8. [故障排除](#故障排除)
9. [進階使用](#進階使用)

---

## 安裝概述

**mcp-server-github** 是一個 Model Context Protocol (MCP) 伺服器，提供 GitHub API 相關的工具，讓 Cline AI Agent 能夠直接與 GitHub 進行交互。

### 主要功能
- ✅ 讀取 GitHub 倉庫文件
- ✅ 搜索倉庫和代碼
- ✅ 管理 issues 和 pull requests
- ✅ 創建倉庫和分支
- ✅ 訪問 GitHub 用戶和組織信息

### 安裝狀態
- **安裝時間**: 2026年4月5日
- **安裝版本**: @iflow-mcp/server-github@0.6.2
- **測試狀態**: ✅ 所有測試通過

---

## 系統要求

### 必要條件
1. **Node.js**: v14.0.0 或更高版本
2. **npm**: v6.0.0 或更高版本
3. **GitHub 帳戶**: 需要 GitHub Personal Access Token
4. **Cline AI Agent**: 已安裝並配置 MCP 支持

### 已驗證環境
```
✅ Node.js: v18.19.1
✅ npm: 9.2.0
✅ npx: 9.2.0
✅ GitHub Token: 已配置
✅ MCP 設定: 已正確配置
```

---

## 安裝步驟

### 步驟 1: 檢查 Node.js 和 npm
```bash
node --version
npm --version
npx --version
```

### 步驟 2: 安裝 mcp-server-github
```bash
# 測試安裝（npx 會自動下載）
npx @iflow-mcp/server-github --help
```

### 步驟 3: 配置 MCP 設定文件
MCP 設定文件位於:
```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

### 步驟 4: 添加 GitHub 配置
在 `mcpServers` 部分添加以下配置:
```json
"mcp-server-github": {
    "command": "npx",
    "args": ["@iflow-mcp/server-github"],
    "env": {
        "GITHUB_TOKEN": "您的_GitHub_Personal_Access_Token"
    }
}
```

### 步驟 5: 測試安裝
```bash
# 運行測試腳本
cd /home/kei/Desktop/betweencoffee_delivery_enhance
node test_mcp_github.js
```

---

## 配置說明

### MCP 設定文件結構
```json
{
    "mcpServers": {
        "mcp-installer": { ... },
        "mcp-server-fetch": { ... },
        "simple-postgres": { ... },
        "mcp-server-filesystem": { ... },
        "mcp-server-github": {
            "command": "npx",
            "args": ["@iflow-mcp/server-github"],
            "env": {
                "GITHUB_TOKEN": "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"
            }
        }
    }
}
```

### GitHub Token 權限
建議的 GitHub Personal Access Token 權限:
- **repo**: 訪問私有倉庫和進行寫操作
- **read:org**: 讀取組織信息
- **user**: 讀取用戶信息
- **workflow**: 訪問 GitHub Actions

### 環境變數
| 變數名稱 | 說明 | 必需 |
|---------|------|------|
| GITHUB_TOKEN | GitHub Personal Access Token | ✅ |
| GITHUB_API_URL | GitHub API 端點（可選） | ❌ |

---

## 可用工具

mcp-server-github 提供以下 MCP 工具:

### 1. 倉庫操作
- **get_file_contents**: 獲取 GitHub 倉庫文件內容
- **search_repositories**: 搜索 GitHub 倉庫
- **create_repository**: 創建新的 GitHub 倉庫
- **fork_repository**: Fork 倉庫

### 2. 代碼管理
- **search_code**: 在 GitHub 上搜索代碼
- **list_commits**: 列出倉庫的 commits
- **get_pull_request_files**: 獲取 pull request 的文件列表

### 3. Issue 管理
- **create_issue**: 在倉庫中創建 issue
- **list_issues**: 列出倉庫的 issues
- **search_issues**: 搜索 issues
- **update_issue**: 更新 issue
- **add_issue_comment**: 添加 issue 評論

### 4. Pull Request 管理
- **create_pull_request**: 創建 pull request
- **list_pull_requests**: 列出 pull requests
- **get_pull_request**: 獲取 pull request 詳情
- **create_pull_request_review**: 創建 PR 審查
- **merge_pull_request**: 合併 PR

### 5. 用戶和組織
- **search_users**: 搜索 GitHub 用戶
- **get_issue**: 獲取 issue 詳情
- **get_pull_request_status**: 獲取 PR 狀態

---

## 使用示例

### 示例 1: 讀取倉庫文件
```javascript
// 讀取 README.md 文件
get_file_contents('pythonkei', 'betweencoffee_delivery_enhance', 'README.md')
```

### 示例 2: 搜索倉庫
```javascript
// 搜索包含 "betweencoffee" 的倉庫
search_repositories('betweencoffee delivery')
```

### 示例 3: 創建 issue
```javascript
// 在倉庫中創建 issue
create_issue('pythonkei', 'betweencoffee_delivery_enhance', 'Bug 報告', '發現一個問題...')
```

### 示例 4: 獲取 commits
```javascript
// 列出倉庫的 commits
list_commits('pythonkei', 'betweencoffee_delivery_enhance')
```

### 示例 5: 搜索代碼
```javascript
// 搜索包含 "WebSocket" 的代碼
search_code('WebSocket language:JavaScript')
```

### 示例 6: 創建 pull request
```javascript
// 創建 pull request
create_pull_request('pythonkei', 'betweencoffee_delivery_enhance', 
    '功能增強: 添加新功能', 
    '這個 PR 添加了以下功能...',
    'feature-branch',
    'main')
```

---

## 安全建議

### 1. GitHub Token 安全
- 🔒 **不要將 Token 提交到版本控制**
- 🔒 **定期更新 Token**（建議每90天）
- 🔒 **使用最小必要權限原則**
- 🔒 **考慮使用環境變數或密碼管理器**

### 2. Token 權限管理
```bash
# 創建具有最小權限的 Token
# 訪問: https://github.com/settings/tokens
# 選擇權限:
#   - repo (如果需要寫操作)
#   - read:org (如果需要讀取組織信息)
#   - user (讀取用戶信息)
```

### 3. 環境變數配置
```bash
# 使用環境變數而不是硬編碼
export GITHUB_TOKEN="your_token_here"
```

### 4. 監控和審計
- 📊 定期檢查 GitHub Token 的使用記錄
- 📊 監控 API 調用頻率
- 📊 設置使用限制和告警

---

## 故障排除

### 常見問題

#### 問題 1: "GitHub MCP Server running on stdio" 但無法使用工具
**解決方案**:
1. 檢查 MCP 設定文件格式
2. 驗證 GitHub Token 是否有效
3. 重啟 Cline AI Agent

#### 問題 2: GitHub API 速率限制
**解決方案**:
1. 使用認證的 Token 提高限制
2. 實現請求緩存
3. 減少不必要的 API 調用

#### 問題 3: Token 權限不足
**解決方案**:
1. 檢查 Token 權限設置
2. 重新生成具有適當權限的 Token
3. 更新 MCP 設定文件中的 Token

#### 問題 4: npx 安裝失敗
**解決方案**:
```bash
# 清理 npm 緩存
npm cache clean --force

# 重新安裝
npx @iflow-mcp/server-github --help
```

### 診斷命令
```bash
# 測試 GitHub Token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# 測試 npx 命令
npx @iflow-mcp/server-github --help

# 檢查 MCP 設定文件
cat ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json | python -m json.tool
```

---

## 進階使用

### 1. 批量操作
```javascript
// 批量讀取多個文件
const files = ['README.md', 'package.json', 'LICENSE'];
for (const file of files) {
    const content = get_file_contents('pythonkei', 'betweencoffee_delivery_enhance', file);
    console.log(`File: ${file}, Size: ${content.length} bytes`);
}
```

### 2. 自動化工作流
```javascript
// 自動創建 issue 模板
function createBugReport(title, description, labels = ['bug']) {
    return create_issue('pythonkei', 'betweencoffee_delivery_enhance', 
        `[Bug] ${title}`, 
        `## 問題描述\n${description}\n\n## 重現步驟\n1. ...\n2. ...\n3. ...`,
        labels);
}
```

### 3. 數據分析
```javascript
// 分析倉庫活動
const commits = list_commits('pythonkei', 'betweencoffee_delivery_enhance');
const issues = list_issues('pythonkei', 'betweencoffee_delivery_enhance', 'all');

console.log(`總 commits: ${commits.length}`);
console.log(`總 issues: ${issues.length}`);
console.log(`開啟的 issues: ${issues.filter(i => i.state === 'open').length}`);
```

### 4. 集成其他 MCP 工具
```javascript
// 結合文件系統和 GitHub 工具
const localFile = read_file('/path/to/local/file.js');
const githubFile = get_file_contents('owner', 'repo', 'path/to/file.js');

// 比較文件內容
if (localFile !== githubFile) {
    console.log('文件不同，需要更新');
    // 創建 pull request 或 issue
}
```

### 5. 監控和報告
```javascript
// 生成倉庫健康報告
function generateRepoHealthReport(owner, repo) {
    const commits = list_commits(owner, repo);
    const issues = list_issues(owner, repo, 'all');
    const prs = list_pull_requests(owner, repo, 'all');
    
    return {
        repository: `${owner}/${repo}`,
        totalCommits: commits.length,
        openIssues: issues.filter(i => i.state === 'open').length,
        openPRs: prs.filter(pr => pr.state === 'open').length,
        lastCommit: commits[0]?.commit?.author?.date,
        activityScore: calculateActivityScore(commits, issues, prs)
    };
}
```

---

## 最佳實踐

### 1. 錯誤處理
```javascript
try {
    const content = get_file_contents('owner', 'repo', 'file.txt');
    console.log('文件內容:', content);
} catch (error) {
    console.error('讀取文件失敗:', error.message);
    // 記錄錯誤或重試
}
```

### 2. 緩存策略
```javascript
// 實現簡單的緩存
const cache = new Map();

function getCachedFile(owner, repo, path) {
    const cacheKey = `${owner}/${repo}/${path}`;
    
    if (cache.has(cacheKey)) {
        return cache.get(cacheKey);
    }
    
    const content = get_file_contents(owner, repo, path);
    cache.set(cacheKey, content);
    
    // 設置緩存過期時間
    setTimeout(() => cache.delete(cacheKey), 5 * 60 * 1000); // 5分鐘
    
    return content;
}
```

### 3. 速率限制處理
```javascript
// 處理 GitHub API 速率限制
let requestCount = 0;
const RATE_LIMIT = 30; // 每分鐘請求數

function makeGitHubRequest(operation, ...args) {
    if (requestCount >= RATE_LIMIT) {
        console.warn('達到速率限制，等待1分鐘...');
        await new Promise(resolve => setTimeout(resolve, 60 * 1000));
        requestCount = 0;
    }
    
    requestCount++;
    return operation(...args);
}
```

### 4. 日誌記錄
```javascript
// 記錄所有 GitHub 操作
function logGitHubOperation(operation, params, result, error = null) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        operation,
        params,
        result: error ? null : result,
        error: error ? error.message : null,
        success: !error
    };
    
    // 保存到文件或發送到監控系統
    console.log('GitHub 操作日誌:', logEntry);
}
```

---

## 更新和維護

### 檢查更新
```bash
# 檢查可用更新
npm view @iflow-mcp/server-github version

# 更新到最新版本
npx @iflow-mcp/server-github@latest --help
```

### 備份配置
```bash
# 備份 MCP 設定文件
cp ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json \
   ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json.backup
```

### 遷移到新版本
1. 備份當前配置
2. 測試新版本
3. 更新 MCP 設定文件
4. 運行測試腳本驗證

---

## 聯繫和支持

### 資源鏈接
- **GitHub 倉庫**: https://github.com/iflow/mcp-server-github
- **npm 包**: https://www.npmjs.com/package/@iflow-mcp/server-github
- **MCP 文檔**: https://modelcontextprotocol.io
- **GitHub API 文檔**: https://docs.github.com/en/rest

### 問題報告
1. 檢查現有 issues
2. 提供詳細的錯誤信息
3. 包括環境信息和配置
4. 提供重現步驟

### 社區支持
- GitHub Discussions
- MCP 社區論壇
- 開發者 Discord 頻道

---

## 附錄

### A. 測試腳本
測試腳本位於: `/home/kei/Desktop/betweencoffee_delivery_enhance/test_mcp_github.js`

### B. 配置示例
完整的 MCP 設定文件示例已包含在本文檔中。

### C. 快速參考
```bash
# 快速測試命令
node test_mcp_github.js

# 檢查配置
cat ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json | jq '.mcpServers["mcp-server-github"]'

# 測試 GitHub 連接
npx @iflow-mcp/server-github --help
```

### D. 版本歷史
- **v0.6.2** (2025-08-11): 當前安裝版本
- **未來更新**: 定期檢查 npm 包更新

---

## 總結

mcp-server-github 已成功安裝並配置完成。您現在可以:

1. ✅ 使用 GitHub 相關的 MCP 工具
2. ✅ 訪問和管理 GitHub 倉庫
3. ✅ 處理 issues 和 pull requests
4. ✅ 搜索代碼和用戶
5. ✅ 自動化 GitHub 工作流

**下一步行動**:
1. 測試基本功能（讀取文件、搜索倉庫）
2. 探索進階功能（創建 issue、管理 PR）
3. 集成到現有工作流中
4. 監控使用情況和性能

**重要提醒**: 定期更新 GitHub Token 並監控 API 使用情況以確保安全和效率。

---

**文檔版本**: 1.0.0  
**最後更新**: 2026年4月5日  
**適用於**: Between Coffee 系統開發團隊  
**維護者**: Cline AI Agent