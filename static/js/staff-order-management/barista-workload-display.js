/**
 * 員工工作負載顯示模塊
 * 
 * 這個模塊負責：
 * 1. 顯示員工當前工作負載
 * 2. 顯示智能分配建議
 * 3. 提供操作建議
 * 4. 實時更新工作狀態
 */

class BaristaWorkloadDisplay {
    constructor(options = {}) {
        this.options = {
            updateInterval: 10000, // 10秒更新一次
            containerSelector: '#barista-workload-container',
            ...options
        };
        
        this.container = null;
        this.workloadData = null;
        this.updateTimer = null;
        
        this.initialize();
    }
    
    /**
     * 初始化模塊
     */
    initialize() {
        console.log('🔄 初始化員工工作負載顯示模塊');
        
        // 查找容器
        this.container = document.querySelector(this.options.containerSelector);
        
        if (!this.container) {
            console.warn(`找不到容器: ${this.options.containerSelector}`);
            return;
        }
        
        // 創建基本結構
        this.createContainerStructure();
        
        // 加載初始數據
        this.loadWorkloadData();
        
        // 開始定時更新
        this.startAutoUpdate();
        
        console.log('✅ 員工工作負載顯示模塊初始化完成');
    }
    
    /**
     * 創建容器結構
     */
    createContainerStructure() {
        this.container.innerHTML = `
            <div class="barista-workload-header">
                <h3 class="workload-title">
                    <i class="fas fa-users"></i> 員工工作負載
                    <span class="badge bg-info" id="workload-update-badge">實時</span>
                </h3>
                <div class="workload-controls">
                    <button class="btn btn-sm btn-outline-primary" id="refresh-workload-btn">
                        <i class="fas fa-sync-alt"></i> 刷新
                    </button>
                    <button class="btn btn-sm btn-outline-success" id="optimize-btn">
                        <i class="fas fa-magic"></i> 智能優化
                    </button>
                </div>
            </div>
            
            <div class="workload-loading" id="workload-loading">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">加載中...</span>
                </div>
                <span class="loading-text">加載工作負載數據...</span>
            </div>
            
            <div class="workload-content" id="workload-content" style="display: none;">
                <!-- 系統概覽 -->
                <div class="system-overview card mb-3">
                    <div class="card-header">
                        <i class="fas fa-chart-line"></i> 系統概覽
                    </div>
                    <div class="card-body" id="system-overview-content">
                        <!-- 動態加載 -->
                    </div>
                </div>
                
                <!-- 員工列表 -->
                <div class="barista-list" id="barista-list">
                    <!-- 動態加載 -->
                </div>
                
                <!-- 智能建議 -->
                <div class="smart-suggestions card mt-3" id="smart-suggestions" style="display: none;">
                    <div class="card-header bg-info text-white">
                        <i class="fas fa-lightbulb"></i> 智能建議
                    </div>
                    <div class="card-body" id="suggestions-content">
                        <!-- 動態加載 -->
                    </div>
                </div>
            </div>
            
            <div class="workload-error" id="workload-error" style="display: none;">
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span id="error-message">加載失敗</span>
                </div>
            </div>
        `;
        
        // 綁定事件
        this.bindEvents();
    }
    
    /**
     * 綁定事件
     */
    bindEvents() {
        // 刷新按鈕
        const refreshBtn = document.getElementById('refresh-workload-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadWorkloadData());
        }
        
        // 優化按鈕
        const optimizeBtn = document.getElementById('optimize-btn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizeQueue());
        }
    }
    
    /**
     * 加載工作負載數據
     */
    async loadWorkloadData() {
        try {
            this.showLoading();
            
            const response = await fetch('/api/queue/barista-workload/');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.workloadData = data.data;
                this.renderWorkload();
                this.hideError();
            } else {
                throw new Error(data.message || '加載失敗');
            }
            
        } catch (error) {
            console.error('加載工作負載數據失敗:', error);
            this.showError(`加載失敗: ${error.message}`);
        }
    }
    
    /**
     * 渲染工作負載
     */
    renderWorkload() {
        if (!this.workloadData) return;
        
        // 渲染系統概覽
        this.renderSystemOverview();
        
        // 渲染員工列表
        this.renderBaristaList();
        
        // 渲染智能建議
        this.renderSmartSuggestions();
        
        // 顯示內容
        this.showContent();
        
        // 更新時間戳
        this.updateTimestamp();
    }
    
    /**
     * 渲染系統概覽
     */
    renderSystemOverview() {
        const overviewContent = document.getElementById('system-overview-content');
        if (!overviewContent) return;
        
        const { 
            total_baristas, 
            active_baristas, 
            total_capacity, 
            current_load, 
            available_capacity,
            utilization_rate 
        } = this.workloadData;
        
        // 計算進度條百分比
        const utilizationPercent = Math.min(100, utilization_rate);
        
        // 確定進度條顏色
        let progressColor = 'bg-success';
        if (utilization_rate > 80) {
            progressColor = 'bg-danger';
        } else if (utilization_rate > 60) {
            progressColor = 'bg-warning';
        }
        
        overviewContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="system-metric">
                        <div class="metric-label">在崗員工</div>
                        <div class="metric-value">
                            <span class="badge bg-primary">${active_baristas}/${total_baristas}</span>
                        </div>
                    </div>
                    
                    <div class="system-metric">
                        <div class="metric-label">總容量</div>
                        <div class="metric-value">
                            <span class="badge bg-info">${total_capacity} 杯</span>
                        </div>
                    </div>
                    
                    <div class="system-metric">
                        <div class="metric-label">當前負載</div>
                        <div class="metric-value">
                            <span class="badge ${current_load > total_capacity * 0.8 ? 'bg-danger' : 'bg-success'}">
                                ${current_load} 杯
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="system-metric">
                        <div class="metric-label">可用容量</div>
                        <div class="metric-value">
                            <span class="badge ${available_capacity > 0 ? 'bg-success' : 'bg-danger'}">
                                ${available_capacity} 杯
                            </span>
                        </div>
                    </div>
                    
                    <div class="system-metric">
                        <div class="metric-label">利用率</div>
                        <div class="metric-value">
                            <span class="badge ${utilization_rate > 80 ? 'bg-danger' : utilization_rate > 60 ? 'bg-warning' : 'bg-success'}">
                                ${utilization_rate}%
                            </span>
                        </div>
                    </div>
                    
                    <div class="progress mt-2" style="height: 10px;">
                        <div class="progress-bar ${progressColor}" 
                             role="progressbar" 
                             style="width: ${utilizationPercent}%"
                             aria-valuenow="${utilizationPercent}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染員工列表
     */
    renderBaristaList() {
        const baristaList = document.getElementById('barista-list');
        if (!baristaList) return;
        
        const baristaDetails = this.workloadData.barista_details || [];
        
        if (baristaDetails.length === 0) {
            baristaList.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> 沒有在崗員工
                </div>
            `;
            return;
        }
        
        let html = '<div class="row">';
        
        baristaDetails.forEach(barista => {
            const { 
                name, 
                current_load, 
                max_concurrent, 
                available_slots,
                efficiency_factor,
                is_available,
                current_orders 
            } = barista;
            
            // 計算進度
            const loadPercent = Math.min(100, (current_load / max_concurrent) * 100);
            
            // 確定狀態顏色
            let statusColor = 'success';
            let statusIcon = 'fa-check-circle';
            let statusText = '可用';
            
            if (!is_available) {
                statusColor = 'danger';
                statusIcon = 'fa-times-circle';
                statusText = '不可用';
            } else if (available_slots === 0) {
                statusColor = 'warning';
                statusIcon = 'fa-exclamation-circle';
                statusText = '已滿';
            }
            
            // 效率標籤
            let efficiencyBadge = '';
            if (efficiency_factor < 0.9) {
                efficiencyBadge = '<span class="badge bg-success ms-1">快速</span>';
            } else if (efficiency_factor > 1.1) {
                efficiencyBadge = '<span class="badge bg-warning ms-1">較慢</span>';
            }
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card barista-card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fas fa-user"></i> 
                                <strong>${name}</strong>
                                ${efficiencyBadge}
                            </div>
                            <span class="badge bg-${statusColor}">
                                <i class="fas ${statusIcon}"></i> ${statusText}
                            </span>
                        </div>
                        
                        <div class="card-body">
                            <!-- 負載進度條 -->
                            <div class="mb-2">
                                <div class="d-flex justify-content-between mb-1">
                                    <small>工作負載</small>
                                    <small>${current_load}/${max_concurrent} 杯</small>
                                </div>
                                <div class="progress" style="height: 8px;">
                                    <div class="progress-bar ${loadPercent > 80 ? 'bg-danger' : loadPercent > 60 ? 'bg-warning' : 'bg-success'}" 
                                         role="progressbar" 
                                         style="width: ${loadPercent}%"
                                         aria-valuenow="${loadPercent}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 容量信息 -->
                            <div class="row text-center mb-2">
                                <div class="col-6">
                                    <div class="capacity-box bg-light p-2 rounded">
                                        <div class="capacity-label">可用容量</div>
                                        <div class="capacity-value ${available_slots > 0 ? 'text-success' : 'text-danger'}">
                                            <strong>${available_slots}</strong> 杯
                                        </div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="capacity-box bg-light p-2 rounded">
                                        <div class="capacity-label">效率因子</div>
                                        <div class="capacity-value">
                                            <strong>${efficiency_factor.toFixed(2)}</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 當前訂單 -->
                            ${this.renderCurrentOrders(current_orders)}
                        </div>
                        
                        <div class="card-footer">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i> 
                                可同時製作最多 ${max_concurrent} 杯咖啡
                            </small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        baristaList.innerHTML = html;
    }
    
    /**
     * 渲染當前訂單
     */
    renderCurrentOrders(currentOrders) {
        if (!currentOrders || currentOrders.length === 0) {
            return `
                <div class="current-orders">
                    <div class="alert alert-light mb-0">
                        <i class="fas fa-coffee"></i> 暫無製作中的訂單
                    </div>
                </div>
            `;
        }
        
        let html = `
            <div class="current-orders">
                <div class="orders-header">
                    <small><i class="fas fa-list"></i> 製作中的訂單</small>
                </div>
                <div class="orders-list">
        `;
        
        currentOrders.forEach(order => {
            const startTime = new Date(order.start_time);
            const timeAgo = this.formatTimeAgo(startTime);
            
            html += `
                <div class="order-item">
                    <div class="order-info">
                        <span class="order-id">#${order.order_id}</span>
                        <span class="order-cups">${order.coffee_count} 杯</span>
                    </div>
                    <div class="order-time">
                        <small class="text-muted">${timeAgo}前開始</small>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * 渲染智能建議
     */
    renderSmartSuggestions() {
        const suggestionsContainer = document.getElementById('smart-suggestions');
        const suggestionsContent = document.getElementById('suggestions-content');
        
        if (!suggestionsContainer || !suggestionsContent) return;
        
        // 檢查是否有建議數據
        const hasSuggestions = this.workloadData.recommendations && 
                              this.workloadData.recommendations.length > 0;
        
        if (!hasSuggestions) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        suggestionsContainer.style.display = 'block';
        
        let html = '';
        
        this.workloadData.recommendations.forEach(rec => {
            let priorityClass = '';
            let priorityIcon = '';
            
            switch (rec.priority) {
                case 'high':
                    priorityClass = 'suggestion-high';
                    priorityIcon = 'fa-exclamation-circle text-danger';
                    break;
                case 'medium':
                    priorityClass = 'suggestion-medium';
                    priorityIcon = 'fa-info-circle text-warning';
                    break;
                case 'low':
                    priorityClass = 'suggestion-low';
                    priorityIcon = 'fa-lightbulb text-info';
                    break;
            }
            
            html += `
                <div class="suggestion-item ${priorityClass} mb-2 p-2 rounded">
                    <div class="d-flex align-items-start">
                        <div class="suggestion-icon me-2">
                            <i class="fas ${priorityIcon}"></i>
                        </div>
                        <div class="suggestion-content flex-grow-1">
                            <div class="suggestion-title">
                                <strong>${rec.title}</strong>
                            </div>
                            <div class="suggestion-message">
                                ${rec.message}
                            </div>
                            ${rec.barista_name ? `
                                <div class="suggestion-details mt-1">
                                    <small class="text-muted">
                                        <i class="fas fa-user"></i> 推薦員工: ${rec.barista_name}
                                    </small>
                                </div>
                            ` : ''}
                            ${rec.estimated_time ? `
                                <div class="suggestion-details mt-1">
                                    <small class="text-muted">
                                        <i class="fas fa-clock"></i> 預計時間: ${rec.estimated_time}分鐘
                                    </small>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        suggestionsContent.innerHTML = html;
    }
    
    /**
     * 優化隊列
     */
    async optimizeQueue() {
        try {
            // 顯示優化中狀態
            const optimizeBtn = document.getElementById('optimize-btn');
            if (optimizeBtn) {
                const originalText = optimizeBtn.innerHTML;
                optimizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 優化中...';
                optimizeBtn.disabled = true;
                
                setTimeout(() => {
                    optimizeBtn.innerHTML = originalText;
                    optimizeBtn.disabled = false;
                }, 3000);
            }
            
            const response = await fetch('/api/queue/optimize/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // 顯示成功消息
                this.showToast('優化成功', '隊列已成功優化', 'success');
                
                // 重新加載數據
                setTimeout(() => {
                    this.loadWorkloadData();
                }, 1000);
            } else {
                throw new Error(data.message || '優化失敗');
            }
            
        } catch (error) {
            console.error('優化隊列失敗:', error);
            this.showToast('優化失敗', error.message, 'error');
        }
    }
    
    /**
     * 開始自動更新
     */
    startAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        this.updateTimer = setInterval(() => {
            this.loadWorkloadData();
        }, this.options.updateInterval);
        
        console.log(`🔄 開始自動更新，間隔: ${this.options.updateInterval}ms`);
    }
    
    /**
     * 停止自動更新
     */
    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
            console.log('⏹️ 停止自動更新');
        }
    }
    
    /**
     * 顯示加載狀態
     */
    showLoading() {
        const loadingEl = document.getElementById('workload-loading');
        const contentEl = document.getElementById('workload-content');
        const errorEl = document.getElementById('workload-error');
        
        if (loadingEl) loadingEl.style.display = 'block';
        if (contentEl) contentEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';
    }
    
    /**
     * 顯示內容
     */
    showContent() {
        const loadingEl = document.getElementById('workload-loading');
        const contentEl = document.getElementById('workload-content');
        const errorEl = document.getElementById('workload-error');
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'block';
        if (errorEl) errorEl.style.display = 'none';
    }
    
    /**
     * 顯示錯誤
     */
    showError(message) {
        const loadingEl = document.getElementById('workload-loading');
        const contentEl = document.getElementById('workload-content');
        const errorEl = document.getElementById('workload-error');
        const errorMessage = document.getElementById('error-message');
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'block';
        if (errorMessage) errorMessage.textContent = message;
    }
    
    /**
     * 隱藏錯誤
     */
    hideError() {
        const errorEl = document.getElementById('workload-error');
        if (errorEl) errorEl.style.display = 'none';
    }
    
    /**
     * 更新時間戳
     */
    updateTimestamp() {
        const badge = document.getElementById('workload-update-badge');
        if (badge) {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('zh-TW', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            badge.textContent = `更新於 ${timeStr}`;
        }
    }
    
    /**
     * 格式化時間差
     */
    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) {
            return '剛剛';
        } else if (diffMins < 60) {
            return `${diffMins}分鐘`;
        } else {
            const diffHours = Math.floor(diffMins / 60);
            return `${diffHours}小時`;
        }
    }
    
    /**
     * 獲取CSRF Token
     */
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        return cookieValue || '';
    }
    
    /**
     * 顯示Toast通知
     */
    showToast(title, message, type = 'info') {
        // 使用現有的toast系統或創建簡單的alert
        const toastContainer = document.getElementById('toast-container');
        
        if (toastContainer && typeof window.showToast === 'function') {
            window.showToast(title, message, type);
        } else {
            // 簡單的alert替代
            alert(`${title}: ${message}`);
        }
    }
    
    /**
     * 銷毀實例
     */
    destroy() {
        this.stopAutoUpdate();
        if (this.container) {
            this.container.innerHTML = '';
        }
        console.log('🗑️ 員工工作負載顯示模塊已銷毀');
    }
}

// 導出模塊
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BaristaWorkloadDisplay;
} else {
    window.BaristaWorkloadDisplay = BaristaWorkloadDisplay;
}

// 自動初始化
document.addEventListener('DOMContentLoaded', function() {
    // 檢查是否有容器
    const container = document.querySelector('#barista-workload-container');
    if (container) {
        window.baristaWorkloadDisplay = new BaristaWorkloadDisplay();
    }
});
