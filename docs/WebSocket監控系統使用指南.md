# WebSocket監控系統使用指南

## 概述

WebSocket監控系統是一個完整的解決方案，用於監控和優化Between Coffee系統中的WebSocket連接穩定性。系統提供實時健康度評分、詳細性能指標、錯誤分析和可視化儀表板。

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket監控系統                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 健康度監控器 │  │ 監控適配器   │  │ 可視化組件       │  │
│  │ (增強版)     │◄─┤ (Adapter)    │◄─┤ (Visualizer)     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                  │                    │          │
│         ▼                  ▼                    ▼          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 數據收集     │  │ 事件攔截     │  │ 圖表渲染         │  │
│  │ 健康度計算   │  │ 適配整合     │  │ 實時更新         │  │
│  │ 警報生成     │  │ 狀態同步     │  │ 交互控制         │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. WebSocketHealthMonitorEnhanced (健康度監控器增強版)

**功能特性：**
- 實時健康度評分系統（0-100分）
- 多維度健康度評估（穩定性、可靠性、網絡質量、資源使用）
- 詳細監控數據收集和統計
- 智能警報系統（警告、嚴重警報）
- 連接事件時間線記錄
- 性能指標計算（延遲、吞吐量、錯誤率）

**基本用法：**
```javascript
// 創建健康度監控器
const healthMonitor = new WebSocketHealthMonitorEnhanced({
    enableDetailedMonitoring: true,
    enableHealthScoring: true,
    enableAlerts: true,
    debugMode: false,
    logLevel: 'info'
});

// 記錄連接開始
healthMonitor.recordConnectionStart();

// 記錄消息發送/接收
healthMonitor.recordMessageSent('訂單數據', 200);
healthMonitor.recordMessageReceived('確認響應', 180, 50);

// 記錄錯誤
healthMonitor.recordError('timeout', '請求超時', { timeout: 5000 });

// 計算健康度
const healthScore = healthMonitor.calculateHealthScore();

// 獲取監控摘要
const summary = healthMonitor.getMonitoringSummary();

// 結束監控
healthMonitor.recordConnectionEnd('normal');
healthMonitor.generateFinalReport();

// 清理資源
healthMonitor.cleanup();
```

### 2. WebSocketMonitoringAdapter (監控適配器)

**功能特性：**
- 無縫整合現有WebSocket連接器
- 自動事件監聽和數據收集
- 支持多種WebSocket實現（原生、第三方庫）
- 事件攔截和轉發
- 自動化監控啟動/停止

**基本用法：**
```javascript
// 假設已有WebSocket連接器
const existingWebSocketConnector = {
    ws: new WebSocket('ws://localhost:8000/ws/orders/'),
    send: function(data) { this.ws.send(data); },
    close: function() { this.ws.close(); }
};

// 創建監控適配器
const monitoringAdapter = new WebSocketMonitoringAdapter(
    existingWebSocketConnector,
    {
        debugMode: false,
        logLevel: 'info',
        monitorConnectionEvents: true,
        monitorMessageEvents: true,
        monitorErrorEvents: true
    }
);

// 獲取健康度監控器
const healthMonitor = monitoringAdapter.getHealthMonitor();

// 手動檢查健康度
const healthScore = monitoringAdapter.checkHealth();

// 手動上報數據
monitoringAdapter.reportData();

// 獲取監控摘要
const summary = monitoringAdapter.getMonitoringSummary();

// 清理適配器
monitoringAdapter.cleanup();
```

### 3. WebSocketMonitoringVisualizer (可視化組件)

**功能特性：**
- 實時監控儀表板
- 多種圖表類型（折線圖、柱狀圖、雷達圖、餅圖）
- 響應式設計，支持移動設備
- 可配置的主題和樣式
- 警報通知顯示
- 數據導出功能

**基本用法：**
```javascript
// 創建可視化組件
const visualizer = new WebSocketMonitoringVisualizer({
    containerId: 'websocket-monitoring-dashboard',
    autoCreateContainer: true,
    enableHealthScoreChart: true,
    enableMessageThroughputChart: true,
    enableLatencyChart: true,
    enableErrorChart: true,
    updateInterval: 5000, // 5秒更新一次
    theme: 'light', // 'light' 或 'dark'
    chartHeight: 200,
    debugMode: false
});

// 顯示/隱藏組件
visualizer.show();
visualizer.hide();

// 獲取當前數據
const currentData = visualizer.getCurrentData();

// 重置數據
visualizer.resetData();

// 清理組件
visualizer.cleanup();
```

## 整合到Between Coffee系統

### 方案A：最小化整合（推薦）

```javascript
// 在現有WebSocket管理器中添加監控
class EnhancedWebSocketManager {
    constructor() {
        // 現有WebSocket連接器
        this.websocketConnector = this._createWebSocketConnector();
        
        // 添加監控適配器
        this.monitoringAdapter = new WebSocketMonitoringAdapter(
            this.websocketConnector,
            {
                debugMode: false,
                logLevel: 'info'
            }
        );
        
        // 可選：添加可視化組件（僅在開發環境）
        if (process.env.NODE_ENV === 'development') {
            this.visualizer = new WebSocketMonitoringVisualizer({
                containerId: 'dev-websocket-monitor',
                autoCreateContainer: true,
                theme: 'dark'
            });
        }
    }
    
    // 現有方法保持不變
    connect() {
        // 原有連接邏輯
        this.websocketConnector.connect();
        
        // 記錄監控開始
        this.monitoringAdapter.getHealthMonitor().recordConnectionStart();
    }
    
    send(data) {
        // 原有發送邏輯
        this.websocketConnector.send(data);
    }
    
    disconnect() {
        // 原有斷開邏輯
        this.websocketConnector.disconnect();
        
        // 記錄監控結束
        this.monitoringAdapter.getHealthMonitor().recordConnectionEnd('user_disconnect');
    }
    
    // 新增監控相關方法
    getHealthScore() {
        return this.monitoringAdapter.getHealthScore();
    }
    
    getMonitoringSummary() {
        return this.monitoringAdapter.getMonitoringSummary();
    }
    
    checkHealth() {
        return this.monitoringAdapter.checkHealth();
    }
}
```

### 方案B：完整整合（包含儀表板）

```html
<!-- 在管理員頁面添加監控儀表板 -->
<!DOCTYPE html>
<html>
<head>
    <title>Between Coffee - WebSocket監控</title>
    <!-- 引入監控系統依賴 -->
    <script src="/static/js/websocket-health-monitor-enhanced.js"></script>
    <script src="/static/js/websocket-monitoring-adapter.js"></script>
    <script src="/static/js/websocket-monitoring-visualizer.js"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>WebSocket連接監控</h1>
        
        <!-- 監控控制面板 -->
        <div class="control-panel">
            <button id="btnStartMonitor" class="btn btn-success">開始監控</button>
            <button id="btnStopMonitor" class="btn btn-danger">停止監控</button>
            <button id="btnExportReport" class="btn btn-info">導出報告</button>
            <span id="healthStatus" class="badge bg-success">健康度: --</span>
        </div>
        
        <!-- 監控儀表板容器 -->
        <div id="monitoringDashboard"></div>
    </div>
    
    <script>
        // 初始化監控系統
        class BetweenCoffeeWebSocketMonitor {
            constructor() {
                this.monitoringAdapter = null;
                this.visualizer = null;
                this.isMonitoring = false;
                
                this._initialize();
            }
            
            _initialize() {
                // 獲取現有WebSocket連接器
                const existingConnector = window.WebSocketManager || 
                                         window.orderWebSocketManager ||
                                         this._findWebSocketConnector();
                
                if (!existingConnector) {
                    console.warn('未找到WebSocket連接器，創建模擬連接器');
                    existingConnector = this._createMockConnector();
                }
                
                // 創建監控適配器
                this.monitoringAdapter = new WebSocketMonitoringAdapter(
                    existingConnector,
                    {
                        debugMode: true,
                        logLevel: 'debug'
                    }
                );
                
                // 創建可視化組件
                this.visualizer = new WebSocketMonitoringVisualizer({
                    containerId: 'monitoringDashboard',
                    autoCreateContainer: false,
                    enableHealthScoreChart: true,
                    enableMessageThroughputChart: true,
                    enableLatencyChart: true,
                    enableErrorChart: true,
                    updateInterval: 10000,
                    theme: 'light'
                });
                
                // 設置事件監聽
                this._setupEventListeners();
                
                // 自動開始監控
                this.startMonitoring();
            }
            
            startMonitoring() {
                if (this.isMonitoring) return;
                
                this.isMonitoring = true;
                this.monitoringAdapter.getHealthMonitor().recordConnectionStart();
                console.log('✅ WebSocket監控已啟動');
            }
            
            stopMonitoring() {
                if (!this.isMonitoring) return;
                
                this.isMonitoring = false;
                this.monitoringAdapter.getHealthMonitor().recordConnectionEnd('manual_stop');
                console.log('🛑 WebSocket監控已停止');
            }
            
            exportReport() {
                const report = this.monitoringAdapter.getHealthMonitor().generateFinalReport();
                const reportStr = JSON.stringify(report, null, 2);
                
                // 創建下載鏈接
                const blob = new Blob([reportStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `websocket-monitor-report-${Date.now()}.json`;
                a.click();
                
                console.log('📥 報告已導出');
            }
            
            _setupEventListeners() {
                document.getElementById('btnStartMonitor').addEventListener('click', () => {
                    this.startMonitoring();
                });
                
                document.getElementById('btnStopMonitor').addEventListener('click', () => {
                    this.stopMonitoring();
                });
                
                document.getElementById('btnExportReport').addEventListener('click', () => {
                    this.exportReport();
                });
                
                // 監聽健康度更新
                document.addEventListener('websocket:monitoring_data', (event) => {
                    const data = event.detail;
                    document.getElementById('healthStatus').textContent = 
                        `健康度: ${data.healthScore}`;
                    
                    // 根據健康度更新顏色
                    const badge = document.getElementById('healthStatus');
                    badge.className = 'badge ';
                    if (data.healthScore >= 80) {
                        badge.classList.add('bg-success');
                    } else if (data.healthScore >= 60) {
                        badge.classList.add('bg-warning');
                    } else {
                        badge.classList.add('bg-danger');
                    }
                });
            }
            
            _findWebSocketConnector() {
                // 嘗試查找系統中的WebSocket連接器
                const possibleNames = [
                    'webSocketManager',
                    'socketManager',
                    'connectionManager',
                    'wsManager'
                ];
                
                for (const name of possibleNames) {
                    if (window[name]) {
                        return window[name];
                    }
                }
                
                return null;
            }
            
            _createMockConnector() {
                return {
                    ws: {
                        url: 'ws://localhost:8000/ws/orders/',
                        addEventListener: () => {},
                        removeEventListener: () => {}
                    },
                    send: (data) => console.log('模擬發送:', data),
                    close: () => console.log('模擬關閉'),
                    reconnect: () => console.log('模擬重連')
                };
            }
        }
        
        // 啟動監控系統
        window.addEventListener('DOMContentLoaded', () => {
            window.betweenCoffeeMonitor = new BetweenCoffeeWebSocketMonitor();
        });
    </script>
</body>
</html>
```

## 配置選項

### WebSocketHealthMonitorEnhanced 配置

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `enableDetailedMonitoring` | boolean | `true` | 啟用詳細監控數據收集 |
| `enableHealthScoring` | boolean | `true` | 啟用健康度評分系統 |
| `enableAlerts` | boolean | `true` | 啟用警報系統 |
| `dataReportInterval` | number | `60000` | 數據上報間隔（毫秒） |
| `healthCheckInterval` | number | `30000` | 健康度檢查間隔（毫秒） |
| `maxLatencyRecords` | number | `100` | 最大延遲記錄數 |
| `maxErrorRecords` | number | `50` | 最大錯誤記錄數 |
| `maxEventRecords` | number | `200` | 最大事件記錄數 |
| `debugMode` | boolean | `false` | 調試模式 |
| `logLevel` | string | `'info'` | 日誌級別（debug/info/warn/error） |

### WebSocketMonitoringAdapter 配置

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `monitorConnectionEvents` | boolean | `true` | 監聽連接事件 |
| `monitorMessageEvents` | boolean | `true` | 監聽消息事件 |
| `monitorErrorEvents` | boolean | `true` | 監聽錯誤事件 |
| `monitorReconnectEvents` | boolean | `true` | 監聽重連事件 |
| `autoStartMonitoring` | boolean | `true` | 自動開始監控 |
| `autoStopMonitoring` | boolean | `true` | 自動停止監控 |
| `interceptOriginalEvents` | boolean | `true` | 攔截原始事件 |
| `debugMode` | boolean | `false` | 調試模式 |
| `logLevel` | string | `'info'` | 日誌級別 |

### WebSocketMonitoringVisualizer 配置

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `containerId` | string | `'websocket-monitoring-visualizer'` | 容器元素ID |
| `autoCreateContainer` | boolean | `true` | 自動創建容器 |
| `enableHealthScoreChart` | boolean | `true` | 啟用健康度評分圖表 |
| `enableMessageThroughputChart` | boolean | `true` | 啟用消息吞吐量圖表 |
| `enableLatencyChart` | boolean | `true` | 啟用延遲圖表 |
| `enableErrorChart` | boolean | `true` | 啟用錯誤圖表 |
| `updateInterval` | number | `5000` | 更新間隔（毫秒） |
| `maxDataPoints` | number | `50` | 最大數據點數 |
| `theme` | string | `'light'` | 主題（light/dark） |
| `chartHeight` | number | `200` | 圖表高度（像素） |
| `debugMode` | boolean | `false` | 調試模式 |

## 健康度評分系統

### 評分維度

1. **穩定性 (40%)**
   - 連接持續時間
   - 錯誤數量
   - 重連次數
   - 連接中斷頻率

2. **可靠性 (30%)**
   - 消息丟失率
   - 消息確認率
   - 數據一致性
   - 超時處理

3. **網絡質量 (20%)**
   - 平均延遲
   - 延遲抖動
   - 帶寬使用率
   - 網絡穩定性

4. **資源使用 (10%)**
   - 內存使用
   - CPU使用率
   - 連接數
   - 消息隊列長度

### 評分等級

| 分數範圍 | 等級 | 顏色 | 建議行動 |
|----------|------|------|----------|
| 90-100 | 優秀 | 綠色 | 連接狀態極佳，無需操作 |
| 70-89 | 良好 | 藍色 | 連接狀態良好，持續監控 |
| 50-69 | 一般 | 黃色 | 連接狀態一般，建議優化 |
| 30-49 | 較差 | 