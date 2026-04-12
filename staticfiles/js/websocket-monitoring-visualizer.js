// static/js/websocket-monitoring-visualizer.js
// WebSocket監控數據可視化組件

/**
 * WebSocket監控數據可視化組件
 * 提供實時監控數據的可視化顯示
 */
class WebSocketMonitoringVisualizer {
    /**
     * 創建監控數據可視化組件
     * @param {Object} options 配置選項
     */
    constructor(options = {}) {
        this.options = this._mergeOptions(options);
        
        // 可視化容器
        this.container = null;
        
        // 圖表實例
        this.charts = {
            healthScore: null,
            messageThroughput: null,
            latencyDistribution: null,
            errorDistribution: null
        };
        
        // 數據緩存
        this.dataCache = {
            healthScores: [],
            messageCounts: [],
            latencies: [],
            errors: []
        };
        
        // 最大數據點數
        this.maxDataPoints = 50;
        
        // 初始化
        this._initialize();
        
        console.log("📊 WebSocket監控數據可視化組件初始化完成");
    }
    
    /**
     * 合併配置選項
     * @private
     */
    _mergeOptions(userOptions) {
        const defaultOptions = {
            // 容器配置
            containerId: 'websocket-monitoring-visualizer',
            autoCreateContainer: true,
            
            // 圖表配置
            enableHealthScoreChart: true,
            enableMessageThroughputChart: true,
            enableLatencyChart: true,
            enableErrorChart: true,
            
            // 更新配置
            updateInterval: 5000, // 5秒更新一次
            maxDataPoints: 50,
            
            // 樣式配置
            theme: 'light', // 'light' 或 'dark'
            chartHeight: 200,
            
            // 調試配置
            debugMode: false
        };
        
        return { ...defaultOptions, ...userOptions };
    }
    
    /**
     * 初始化可視化組件
     * @private
     */
    _initialize() {
        // 設置最大數據點數
        this.maxDataPoints = this.options.maxDataPoints;
        
        // 創建或獲取容器
        this._setupContainer();
        
        // 創建圖表
        this._createCharts();
        
        // 設置事件監聽
        this._setupEventListeners();
        
        // 啟動定期更新
        this._startPeriodicUpdate();
    }
    
    /**
     * 設置容器
     * @private
     */
    _setupContainer() {
        if (this.options.autoCreateContainer) {
            // 檢查是否已存在容器
            let container = document.getElementById(this.options.containerId);
            
            if (!container) {
                // 創建新容器
                container = document.createElement('div');
                container.id = this.options.containerId;
                container.className = 'websocket-monitoring-visualizer';
                
                // 添加到文檔
                document.body.appendChild(container);
            }
            
            this.container = container;
        } else {
            // 使用現有容器
            this.container = document.getElementById(this.options.containerId);
            
            if (!this.container) {
                throw new Error(`找不到容器元素: #${this.options.containerId}`);
            }
        }
        
        // 設置容器樣式
        this._applyContainerStyles();
    }
    
    /**
     * 應用容器樣式
     * @private
     */
    _applyContainerStyles() {
        const styles = {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '400px',
            maxHeight: '500px',
            backgroundColor: this.options.theme === 'dark' ? '#2d3748' : '#ffffff',
            border: `1px solid ${this.options.theme === 'dark' ? '#4a5568' : '#e2e8f0'}`,
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: '1000',
            overflow: 'hidden',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        };
        
        Object.assign(this.container.style, styles);
        
        // 創建標題欄
        this._createHeader();
        
        // 創建內容區域
        this._createContentArea();
    }
    
    /**
     * 創建標題欄
     * @private
     */
    _createHeader() {
        const header = document.createElement('div');
        header.className = 'visualizer-header';
        
        const headerStyles = {
            padding: '12px 16px',
            backgroundColor: this.options.theme === 'dark' ? '#1a202c' : '#f7fafc',
            borderBottom: `1px solid ${this.options.theme === 'dark' ? '#4a5568' : '#e2e8f0'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        };
        
        Object.assign(header.style, headerStyles);
        
        // 標題
        const title = document.createElement('h3');
        title.textContent = 'WebSocket 監控儀表板';
        title.style.margin = '0';
        title.style.fontSize = '14px';
        title.style.fontWeight = '600';
        title.style.color = this.options.theme === 'dark' ? '#e2e8f0' : '#2d3748';
        
        // 控制按鈕
        const controls = document.createElement('div');
        controls.style.display = 'flex';
        controls.style.gap = '8px';
        
        // 最小化按鈕
        const minimizeBtn = document.createElement('button');
        minimizeBtn.textContent = '−';
        minimizeBtn.title = '最小化';
        minimizeBtn.className = 'control-btn minimize';
        
        // 關閉按鈕
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.title = '關閉';
        closeBtn.className = 'control-btn close';
        
        // 應用按鈕樣式
        [minimizeBtn, closeBtn].forEach(btn => {
            Object.assign(btn.style, {
                width: '24px',
                height: '24px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: this.options.theme === 'dark' ? '#4a5568' : '#e2e8f0',
                color: this.options.theme === 'dark' ? '#e2e8f0' : '#4a5568',
                cursor: 'pointer',
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            });
            
            btn.addEventListener('mouseenter', () => {
                btn.style.backgroundColor = this.options.theme === 'dark' ? '#718096' : '#cbd5e0';
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.backgroundColor = this.options.theme === 'dark' ? '#4a5568' : '#e2e8f0';
            });
        });
        
        // 添加事件監聽
        minimizeBtn.addEventListener('click', () => this._toggleMinimize());
        closeBtn.addEventListener('click', () => this._closeVisualizer());
        
        controls.appendChild(minimizeBtn);
        controls.appendChild(closeBtn);
        
        header.appendChild(title);
        header.appendChild(controls);
        
        this.container.appendChild(header);
        this.header = header;
    }
    
    /**
     * 創建內容區域
     * @private
     */
    _createContentArea() {
        const content = document.createElement('div');
        content.className = 'visualizer-content';
        
        const contentStyles = {
            padding: '16px',
            maxHeight: '400px',
            overflowY: 'auto'
        };
        
        Object.assign(content.style, contentStyles);
        
        // 創建圖表容器
        this._createChartContainers(content);
        
        this.container.appendChild(content);
        this.content = content;
    }
    
    /**
     * 創建圖表容器
     * @private
     */
    _createChartContainers(parent) {
        // 健康度評分圖表
        if (this.options.enableHealthScoreChart) {
            const healthScoreContainer = this._createChartContainer('健康度評分', 'health-score-chart');
            parent.appendChild(healthScoreContainer);
        }
        
        // 消息吞吐量圖表
        if (this.options.enableMessageThroughputChart) {
            const throughputContainer = this._createChartContainer('消息吞吐量', 'message-throughput-chart');
            parent.appendChild(throughputContainer);
        }
        
        // 延遲分布圖表
        if (this.options.enableLatencyChart) {
            const latencyContainer = this._createChartContainer('延遲分布', 'latency-distribution-chart');
            parent.appendChild(latencyContainer);
        }
        
        // 錯誤分布圖表
        if (this.options.enableErrorChart) {
            const errorContainer = this._createChartContainer('錯誤分布', 'error-distribution-chart');
            parent.appendChild(errorContainer);
        }
    }
    
    /**
     * 創建圖表容器
     * @private
     */
    _createChartContainer(title, chartId) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        
        Object.assign(container.style, {
            marginBottom: '20px'
        });
        
        // 圖表標題
        const chartTitle = document.createElement('h4');
        chartTitle.textContent = title;
        chartTitle.style.margin = '0 0 8px 0';
        chartTitle.style.fontSize = '12px';
        chartTitle.style.fontWeight = '600';
        chartTitle.style.color = this.options.theme === 'dark' ? '#a0aec0' : '#718096';
        
        // 圖表畫布容器
        const canvasContainer = document.createElement('div');
        canvasContainer.className = 'canvas-container';
        
        Object.assign(canvasContainer.style, {
            position: 'relative',
            height: `${this.options.chartHeight}px`
        });
        
        // 圖表畫布
        const canvas = document.createElement('canvas');
        canvas.id = chartId;
        
        container.appendChild(chartTitle);
        container.appendChild(canvasContainer);
        canvasContainer.appendChild(canvas);
        
        return container;
    }
    
    /**
     * 創建圖表
     * @private
     */
    _createCharts() {
        // 檢查Chart.js是否可用
        if (typeof Chart === 'undefined') {
            console.warn('⚠️ Chart.js 未加載，圖表功能將不可用');
            return;
        }
        
        // 健康度評分圖表
        if (this.options.enableHealthScoreChart) {
            this.charts.healthScore = this._createHealthScoreChart();
        }
        
        // 消息吞吐量圖表
        if (this.options.enableMessageThroughputChart) {
            this.charts.messageThroughput = this._createMessageThroughputChart();
        }
        
        // 延遲分布圖表
        if (this.options.enableLatencyChart) {
            this.charts.latencyDistribution = this._createLatencyDistributionChart();
        }
        
        // 錯誤分布圖表
        if (this.options.enableErrorChart) {
            this.charts.errorDistribution = this._createErrorDistributionChart();
        }
    }
    
    /**
     * 創建健康度評分圖表
     * @private
     */
    _createHealthScoreChart() {
        const ctx = document.getElementById('health-score-chart').getContext('2d');
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '健康度評分',
                    data: [],
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '時間'
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '評分'
                        },
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 創建消息吞吐量圖表
     * @private
     */
    _createMessageThroughputChart() {
        const ctx = document.getElementById('message-throughput-chart').getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '發送',
                        data: [],
                        backgroundColor: '#4299e1',
                        borderColor: '#4299e1',
                        borderWidth: 1
                    },
                    {
                        label: '接收',
                        data: [],
                        backgroundColor: '#ed8936',
                        borderColor: '#ed8936',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '時間'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '消息數量'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * 創建延遲分布圖表
     * @private
     */
    _createLatencyDistributionChart() {
        const ctx = document.getElementById('latency-distribution-chart').getContext('2d');
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '平均延遲',
                    data: [],
                    borderColor: '#9f7aea',
                    backgroundColor: 'rgba(159, 122, 234, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '時間'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '延遲 (ms)'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * 創建錯誤分布圖表
     * @private
     */
    _createErrorDistributionChart() {
        const ctx = document.getElementById('error-distribution-chart').getContext('2d');
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#f56565',
                        '#ed8936',
                        '#ecc94b',
                        '#48bb78',
                        '#38b2ac',
                        '#4299e1',
                        '#667eea',
                        '#9f7aea'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
    
    /**
     * 設置事件監聽
     * @private
     */
    _setupEventListeners() {
        // 監聽監控數據事件
        document.addEventListener('websocket:monitoring_data', (event) => {
            this._handleMonitoringData(event.detail);
        });
        
        // 監聽警報事件
        document.addEventListener('websocket:alert', (event) => {
            this._handleAlert(event.detail);
        });
        
        // 監聽最終報告事件
        document.addEventListener('websocket:final_report', (event) => {
            this._handleFinalReport(event.detail);
        });
    }
    
    /**
     * 啟動定期更新
     * @private
     */
    _startPeriodicUpdate() {
        if (this.options.updateInterval > 0) {
            this.updateTimer = setInterval(() => {
                this._updateCharts();
            }, this.options.updateInterval);
        }
    }
    
    /**
     * 處理監控數據
     * @private
     */
    _handleMonitoringData(data) {
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        // 更新健康度數據
        if (data.healthScore !== undefined) {
            this._addDataPoint('healthScores', {
                timestamp: timestamp,
                value: data.healthScore
            });
        }
        
        // 更新消息統計
        if (data.connectionStats) {
            this._addDataPoint('messageCounts', {
                timestamp: timestamp,
                sent: data.connectionStats.messagesSent || 0,
                received: data.connectionStats.messagesReceived || 0
            });
        }
        
        // 更新延遲數據
        if (data.connectionStats && data.connectionStats.avgLatency !== undefined) {
            this._addDataPoint('latencies', {
                timestamp: timestamp,
                value: data.connectionStats.avgLatency
            });
        }
        
        // 更新錯誤數據
        if (data.connectionStats && data.connectionStats.errorRate !== undefined) {
            this._addDataPoint('errors', {
                timestamp: timestamp,
                value: data.connectionStats.errorRate
            });
        }
        
        // 立即更新圖表
        this._updateCharts();
        
        if (this.options.debugMode) {
            console.debug('📊 監控數據處理完成:', data);
        }
    }
    
    /**
     * 處理警報
     * @private
     */
    _handleAlert(alert) {
        // 可以在這裡添加警報可視化邏輯
        // 例如：顯示警報通知、改變圖表顏色等
        
        if (this.options.debugMode) {
            console.debug('🚨 警報處理:', alert);
        }
    }
    
    /**
     * 處理最終報告
     * @private
     */
    _handleFinalReport(report) {
        // 可以在這裡添加最終報告的可視化
        // 例如：顯示總結信息、生成報告圖表等
        
        console.log('📋 最終報告處理:', report.connectionId);
    }
    
    /**
     * 添加數據點
     * @private
     */
    _addDataPoint(dataType, dataPoint) {
        if (!this.dataCache[dataType]) {
            this.dataCache[dataType] = [];
        }
        
        this.dataCache[dataType].push(dataPoint);
        
        // 限制數據點數量
        if (this.dataCache[dataType].length > this.maxDataPoints) {
            this.dataCache[dataType].shift();
        }
    }
    
    /**
     * 更新圖表
     * @private
     */
    _updateCharts() {
        // 更新健康度評分圖表
        if (this.charts.healthScore && this.dataCache.healthScores.length > 0) {
            this._updateHealthScoreChart();
        }
        
        // 更新消息吞吐量圖表
        if (this.charts.messageThroughput && this.dataCache.messageCounts.length > 0) {
            this._updateMessageThroughputChart();
        }
        
        // 更新延遲分布圖表
        if (this.charts.latencyDistribution && this.dataCache.latencies.length > 0) {
            this._updateLatencyDistributionChart();
        }
        
        // 更新錯誤分布圖表
        if (this.charts.errorDistribution && this.dataCache.errors.length > 0) {
            this._updateErrorDistributionChart();
        }
    }
    
    /**
     * 更新健康度評分圖表
     * @private
     */
    _updateHealthScoreChart() {
        const labels = this.dataCache.healthScores.map(d => d.timestamp);
        const data = this.dataCache.healthScores.map(d => d.value);
        
        this.charts.healthScore.data.labels = labels;
        this.charts.healthScore.data.datasets[0].data = data;
        this.charts.healthScore.update();
    }
    
    /**
     * 更新消息吞吐量圖表
     * @private
     */
    _updateMessageThroughputChart() {
        const labels = this.dataCache.messageCounts.map(d => d.timestamp);
        const sentData = this.dataCache.messageCounts.map(d => d.sent);
        const receivedData = this.dataCache.messageCounts.map(d => d.received);
        
        this.charts.messageThroughput.data.labels = labels;
        this.charts.messageThroughput.data.datasets[0].data = sentData;
        this.charts.messageThroughput.data.datasets[1].data = receivedData;
        this.charts.messageThroughput.update();
    }
    
    /**
     * 更新延遲分布圖表
     * @private
     */
    _updateLatencyDistributionChart() {
        const labels = this.dataCache.latencies.map(d => d.timestamp);
        const data = this.dataCache.latencies.map(d => d.value);
        
        this.charts.latencyDistribution.data.labels = labels;
        this.charts.latencyDistribution.data.datasets[0].data = data;
        this.charts.latencyDistribution.update();
    }
    
    /**
     * 更新錯誤分布圖表
     * @private
     */
    _updateErrorDistributionChart() {
        // 這裡可以根據錯誤類型創建分布圖
        // 目前簡單顯示錯誤率
        const labels = ['錯誤率'];
        const data = [this.dataCache.errors.length > 0 ? 
            this.dataCache.errors[this.dataCache.errors.length - 1].value * 100 : 0];
        
        this.charts.errorDistribution.data.labels = labels;
        this.charts.errorDistribution.data.datasets[0].data = data;
        this.charts.errorDistribution.update();
    }
    
    /**
     * 切換最小化
     * @private
     */
    _toggleMinimize() {
        if (this.content.style.display === 'none') {
            this.content.style.display = 'block';
            this.container.style.maxHeight = '500px';
        } else {
            this.content.style.display = 'none';
            this.container.style.maxHeight = '60px';
        }
    }
    
    /**
     * 關閉可視化組件
     * @private
     */
    _closeVisualizer() {
        this.cleanup();
        this.container.remove();
    }
    
    /**
     * 清理可視化組件
     */
    cleanup() {
        // 停止定期更新
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
        
        // 銷毀圖表
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        
        // 移除事件監聽
        document.removeEventListener('websocket:monitoring_data', this._handleMonitoringData);
        document.removeEventListener('websocket:alert', this._handleAlert);
        document.removeEventListener('websocket:final_report', this._handleFinalReport);
        
        console.log('🧹 WebSocket監控數據可視化組件清理完成');
    }
    
    /**
     * 顯示可視化組件
     */
    show() {
        if (this.container) {
            this.container.style.display = 'block';
        }
    }
    
    /**
     * 隱藏可視化組件
     */
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }
    
    /**
     * 獲取當前數據
     */
    getCurrentData() {
        return {
            healthScores: [...this.dataCache.healthScores],
            messageCounts: [...this.dataCache.messageCounts],
            latencies: [...this.dataCache.latencies],
            errors: [...this.dataCache.errors]
        };
    }
    
    /**
     * 重置數據
     */
    resetData() {
        this.dataCache = {
            healthScores: [],
            messageCounts: [],
            latencies: [],
            errors: []
        };
        
        this._updateCharts();
        
        console.log('🔄 監控數據已重置');
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.WebSocketMonitoringVisualizer = WebSocketMonitoringVisualizer;
    console.log('✅ WebSocket監控數據可視化組件已註冊到全局');
}

// 導出工廠函數
if (typeof window !== 'undefined') {
    window.createWebSocketMonitoringVisualizer = (options) => {
        return new WebSocketMonitoringVisualizer(options);
    };
}
