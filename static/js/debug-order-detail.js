// static/js/debug-order-detail.js
// ==================== 訂單詳情頁面調試工具 ====================

/**
 * 訂單詳情頁面調試工具
 * 用於診斷訂單詳情頁面的 DOM 元素和 WebSocket 問題
 */

class OrderDetailDebugger {
    constructor() {
        this.debugMode = true;
        this.init();
    }
    
    init() {
        console.log('🔧 訂單詳情頁面調試工具已加載');
        this.checkPageElements();
        this.setupDebugControls();
    }
    
    // 檢查頁面中的關鍵 DOM 元素
    checkPageElements() {
        const elements = [
            'status-text', 'status-icon-symbol', 'status-icon',
            'progress-fill', 'queue-info', 'step-pending',
            'step-preparing', 'step-ready', 'step-completed',
            'queue-position', 'estimated-time', 'ws-connection-status',
            'order-detail-app'
        ];
        
        console.log('🔍 檢查頁面元素:');
        const results = [];
        
        elements.forEach(id => {
            const el = document.getElementById(id);
            const exists = !!el;
            const tagName = el ? el.tagName : 'N/A';
            const className = el ? el.className : 'N/A';
            
            results.push({
                id,
                exists,
                tagName,
                className: className.substring(0, 50) + (className.length > 50 ? '...' : '')
            });
            
            console.log(`  ${id}: ${exists ? '✅ 存在' : '❌ 不存在'} (${tagName})`);
        });
        
        // 保存結果供後續使用
        this.elementCheckResults = results;
        
        // 如果有缺失的元素，顯示警告
        const missingElements = results.filter(r => !r.exists);
        if (missingElements.length > 0) {
            console.warn(`⚠️ 發現 ${missingElements.length} 個缺失的元素:`, 
                missingElements.map(e => e.id));
        }
        
        return results;
    }
    
    // 檢查 WebSocket 狀態
    checkWebSocketStatus() {
        const tracker = window.orderTracker;
        if (!tracker) {
            console.warn('⚠️ orderTracker 未定義');
            return {
                exists: false,
                status: '未定義',
                isConnected: false
            };
        }
        
        const status = {
            exists: true,
            isConnected: tracker.isConnected,
            reconnectAttempts: tracker.reconnectAttempts,
            maxReconnectAttempts: tracker.maxReconnectAttempts,
            shouldReconnect: tracker.shouldReconnect,
            socketReadyState: tracker.socket ? tracker.socket.readyState : '無 socket'
        };
        
        console.log('🔌 WebSocket 狀態檢查:', status);
        return status;
    }
    
    // 模擬訂單狀態更新（用於測試）
    simulateStatusUpdate(status) {
        console.log(`🎯 模擬訂單狀態更新: ${status}`);
        
        const testData = {
            status: status,
            status_display: this.getStatusDisplay(status),
            updated_at: new Date().toISOString(),
            progress_percentage: this.getProgressPercentage(status),
            progress_display: `${this.getProgressPercentage(status)}% 完成`
        };
        
        // 如果 orderTracker 存在，使用它的方法
        if (window.orderTracker && window.orderTracker.updateOrderStatus) {
            window.orderTracker.updateOrderStatus(testData);
            console.log('✅ 使用 orderTracker 更新狀態');
        } else {
            // 否則直接調用 updateOrderStatus 方法
            this.directUpdateOrderStatus(testData);
            console.log('✅ 直接更新狀態');
        }
        
        return testData;
    }
    
    // 直接更新訂單狀態（用於測試）
    directUpdateOrderStatus(data) {
        const status = data.status;
        const statusDisplay = data.status_display || this.getStatusDisplay(status);
        
        // 更新狀態文字
        const statusTextEl = document.getElementById('status-text');
        if (statusTextEl) {
            statusTextEl.textContent = `訂單 ${statusDisplay}`;
        }
        
        // 更新狀態圖示
        this.updateStatusIconDirectly(status);
        
        // 更新進度條
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            const width = this.getProgressPercentage(status);
            progressFill.style.width = width + '%';
        }
        
        // 更新時間軸
        this.updateTimelineDirectly(status, data.updated_at);
        
        console.log(`✅ 直接更新完成: ${status} (${statusDisplay})`);
    }
    
    // 直接更新狀態圖示
    updateStatusIconDirectly(status) {
        const icon = document.getElementById('status-icon-symbol');
        const iconContainer = document.getElementById('status-icon');
        
        if (!icon || !iconContainer) {
            console.warn('⚠️ 找不到狀態圖示元素');
            return;
        }
        
        // 移除所有狀態 class
        iconContainer.className = 'rounded-circle text-white d-flex align-items-center justify-content-center';
        
        switch (status) {
            case 'pending':
                icon.setAttribute('class', 'fas fa-clock fa-lg');
                iconContainer.classList.add('bg-warning');
                break;
            case 'preparing':
                icon.setAttribute('class', 'fas fa-mug-hot fa-lg');
                iconContainer.classList.add('bg-primary');
                break;
            case 'ready':
                icon.setAttribute('class', 'fas fa-bell fa-lg');
                iconContainer.classList.add('bg-success');
                break;
            case 'completed':
                icon.setAttribute('class', 'fas fa-check-double fa-lg');
                iconContainer.classList.add('bg-secondary');
                break;
            default:
                icon.setAttribute('class', 'fas fa-check fa-lg');
                iconContainer.classList.add('bg-success');
        }
    }
    
    // 直接更新時間軸
    updateTimelineDirectly(status, timestamp) {
        const steps = ['pending', 'preparing', 'ready', 'completed'];
        let currentReached = false;
        
        steps.forEach(step => {
            const stepEl = document.getElementById(`step-${step}`);
            const timeEl = document.getElementById(`time-${step}`);
            
            if (!stepEl) return;
            
            if (step === status) {
                // 當前狀態：active
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
                currentReached = true;
                if (timeEl && timestamp) {
                    timeEl.textContent = this.formatTime(timestamp);
                }
            } else if (!currentReached) {
                // 已完成的狀態
                stepEl.classList.add('completed');
                stepEl.classList.remove('active');
            } else {
                // 未到達的狀態
                stepEl.classList.remove('completed', 'active');
                if (timeEl) timeEl.textContent = '--:--';
            }
        });
    }
    
    // 輔助方法
    getStatusDisplay(status) {
        const map = {
            'pending': '處理中',
            'preparing': '製作中',
            'ready': '待取餐',
            'completed': '已完成'
        };
        return map[status] || status;
    }
    
    getProgressPercentage(status) {
        switch (status) {
            case 'pending': return 25;
            case 'preparing': return 60;
            case 'ready': return 90;
            case 'completed': return 100;
            default: return 0;
        }
    }
    
    formatTime(isoString) {
        if (!isoString) return '--:--';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('zh-HK', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return isoString;
        }
    }
    
    // 設置調試控制界面
    setupDebugControls() {
        // 只在調試模式下創建控制界面
        if (!this.debugMode) return;
        
        // 檢查是否已經存在調試控制界面
        if (document.getElementById('debug-controls')) {
            return;
        }
        
        // 創建調試控制界面
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-controls';
        debugDiv.style.cssText = `
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            z-index: 9999;
            font-family: monospace;
            font-size: 12px;
            max-width: 300px;
        `;
        
        debugDiv.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>🔧 訂單詳情調試工具</strong>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;">
                <button onclick="window.debugger.checkPageElements()" style="padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">檢查元素</button>
                <button onclick="window.debugger.checkWebSocketStatus()" style="padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">檢查WS</button>
                <button onclick="window.debugger.simulateStatusUpdate('pending')" style="padding: 4px 8px; background: #ffc107; color: black; border: none; border-radius: 3px; cursor: pointer;">模擬待處理</button>
                <button onclick="window.debugger.simulateStatusUpdate('preparing')" style="padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">模擬製作中</button>
                <button onclick="window.debugger.simulateStatusUpdate('ready')" style="padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">模擬待取餐</button>
                <button onclick="window.debugger.simulateStatusUpdate('completed')" style="padding: 4px 8px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">模擬已完成</button>
            </div>
            <div id="debug-output" style="max-height: 100px; overflow-y: auto; font-size: 10px; background: rgba(255,255,255,0.1); padding: 5px; border-radius: 3px;"></div>
        `;
        
        document.body.appendChild(debugDiv);
        
        // 重寫 console.log 以捕獲輸出到調試界面
        this.originalConsoleLog = console.log;
        console.log = (...args) => {
            this.originalConsoleLog.apply(console, args);
            this.appendToDebugOutput(args.join(' '));
        };
        
        console.log('✅ 調試控制界面已加載');
    }
    
    // 添加輸出到調試界面
    appendToDebugOutput(message) {
        const outputDiv = document.getElementById('debug-output');
        if (outputDiv) {
            const entry = document.createElement('div');
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            outputDiv.appendChild(entry);
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    }
    
    // 生成調試報告
    generateDebugReport() {
        const elementResults = this.checkPageElements();
        const wsStatus = this.checkWebSocketStatus();
        
        const report = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            pageTitle: document.title,
            elementCheck: elementResults,
            webSocketStatus: wsStatus,
            orderTrackerExists: !!window.orderTracker,
            orderId: document.getElementById('order-detail-app')?.dataset?.orderId || '未知'
        };
        
        console.log('📊 調試報告:', report);
        return report;
    }
}

// 全局導出
window.OrderDetailDebugger = OrderDetailDebugger;

// 自動初始化（僅在訂單詳情頁面）
document.addEventListener('DOMContentLoaded', function() {
    const appContainer = document.getElementById('order-detail-app');
    if (appContainer) {
        // 等待頁面完全加載
        setTimeout(() => {
            window.debugger = new OrderDetailDebugger();
            console.log('✅ 訂單詳情調試工具已初始化');
            
            // 生成初始調試報告
            window.debugger.generateDebugReport();
        }, 1000);
    }
});

// 提供全局調試函數
window.debugOrderDetail = {
    checkElements: function() {
        if (window.debugger) {
            return window.debugger.checkPageElements();
        } else {
            console.warn('調試工具未初始化');
            return null;
        }
    },
    
    checkWebSocket: function() {
        if (window.debugger) {
            return window.debugger.checkWebSocketStatus();
        } else {
            console.warn('調試工具未初始化');
            return null;
        }
    },
    
    simulateUpdate: function(status) {
        if (window.debugger) {
            return window.debugger.simulateStatusUpdate(status);
        } else {
            console.warn('調試工具未初始化');
            return null;
        }
    },
    
    generateReport: function() {
        if (window.debugger) {
            return window.debugger.generateDebugReport();
        } else {
            console.warn('調試工具未初始化');
            return null;
        }
    }
};