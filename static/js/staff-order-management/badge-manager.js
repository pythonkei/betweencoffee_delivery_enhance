// static/js/staff-order-management/badge-manager.js
// ==================== 徽章管理器 - 統一數據流版本（修正徽章顯示） ====================

class BadgeManager {
    constructor() {
        console.log('🔄 初始化徽章管理器（靜態顯示版）...');
        
        // 徽章ID映射表（根據staff_order_management.html的ID）
        this.badgeIdMap = {
            'waiting': 'queue-badge',
            'preparing': 'preparing-orders-badge',
            'ready': 'ready-orders-badge',
            'completed': 'completed-orders-badge'
        };
        
        // 徽章樣式映射（靜態，不變）
        this.badgeStyleMap = {
            'waiting': 'badge-warning',
            'preparing': 'badge-primary',
            'ready': 'badge-success',
            'completed': 'badge-info'
        };
        
        // 徽章標籤映射
        this.badgeLabelMap = {
            'waiting': '等待中',
            'preparing': '製作中',
            'ready': '已就緒',
            'completed': '已提取'
        };
        
        // 初始化
        this.init();
    }
    
    init() {
        console.log('✅ 初始化徽章管理器...');
        
        // 註冊到統一數據管理器
        if (window.unifiedDataManager) {
            // 監聽徽章數據更新
            window.unifiedDataManager.registerListener('badge_summary', (badgeData) => {
                this.updateBadgesFromData(badgeData);
            });
            
            // 監聽所有數據更新（備用）
            window.unifiedDataManager.registerListener('all_data', (allData) => {
                if (allData.badge_summary) {
                    this.updateBadgesFromData(allData.badge_summary);
                }
            });
            
            console.log('✅ 徽章管理器已註冊到統一數據管理器');
        } else {
            console.error('❌ 未找到統一數據管理器，徽章更新將失敗');
        }
        
        // 綁定事件
        this.bindEvents();
        
        // 初始顯示所有徽章為0
        this.initializeAllBadges();
    }
    
    // ==================== 核心方法：從統一數據更新徽章 ====================
    
    /**
     * 從統一數據更新徽章（修正：即使為0也顯示）
     */
    updateBadgesFromData(badgeData) {
        if (!badgeData) {
            console.warn('⚠️ 徽章數據為空，使用默認值');
            this.updateAllBadgesToZero();
            return;
        }
        
        console.log('🔄 從統一數據更新徽章（靜態）:', badgeData);
        
        // 更新等待徽章（始終顯示）
        this.updateBadgeElement('waiting', badgeData.waiting);
        
        // 更新製作中徽章（始終顯示）
        this.updateBadgeElement('preparing', badgeData.preparing);
        
        // 更新已就緒徽章（始終顯示）
        this.updateBadgeElement('ready', badgeData.ready);
        
        // 更新已提取徽章（始終顯示）
        this.updateBadgeElement('completed', badgeData.completed);
        
        // 更新最後更新時間（靜態，無動畫）
        this.updateLastUpdateTime();
        
        // 觸發徽章更新完成事件（無動畫）
        this.dispatchBadgeUpdatedEvent(badgeData);
    }
    
    /**
     * 更新單個徽章元素（修正：始終顯示，不隱藏）
     */
    updateBadgeElement(badgeType, count) {
        const badgeId = this.badgeIdMap[badgeType];
        if (!badgeId) {
            console.error(`❌ 未知的徽章類型: ${badgeType}`);
            return;
        }
        
        const element = document.getElementById(badgeId);
        if (!element) {
            console.warn(`⚠️ 徽章元素 #${badgeId} 未找到`);
            return;
        }
        
        // 確保徽章始終顯示
        element.style.display = 'inline-block';
        element.style.visibility = 'visible';
        element.style.opacity = '1';
        
        // 更新數字（即使為0也顯示）
        const formattedCount = count || 0;
        element.textContent = formattedCount;
        
        // 移除所有動畫類
        element.classList.remove('badge-updated', 'badge-pulse', 'badge-blink');
        
        // 添加或更新靜態樣式類
        const styleClass = this.badgeStyleMap[badgeType];
        if (styleClass) {
            // 移除所有樣式類
            ['badge-warning', 'badge-primary', 'badge-success', 'badge-info', 
             'badge-secondary', 'badge-light', 'badge-dark'].forEach(cls => {
                element.classList.remove(cls);
            });
            
            // 根據數量決定最終樣式
            if (formattedCount > 0) {
                // 有訂單：使用原始樣式
                element.classList.add(styleClass);
                element.classList.add('has-items');
                element.style.backgroundColor = ''; // 重置內聯樣式
                element.style.color = ''; // 重置內聯樣式
            } else {
                // 無訂單：使用淡色樣式，但仍然可見
                const lightStyleClass = this.getLightStyleClass(badgeType);
                element.classList.add(lightStyleClass);
                element.classList.remove('has-items');
                element.classList.add('no-items');
                
                // 添加淡色內聯樣式（無邊框，保持與有訂單狀態一致）
                element.style.backgroundColor = this.getLightBackground(badgeType);
                element.style.color = this.getLightTextColor(badgeType);
                element.style.border = 'none';
            }
        }
        
        // 添加懸浮提示（始終顯示）
        element.title = `${this.badgeLabelMap[badgeType]}: ${formattedCount}個`;
        
        // 確保沒有過渡動畫
        element.style.transition = 'none';
        element.style.animation = 'none';
    }
    
    /**
     * 獲取淡色樣式類
     */
    getLightStyleClass(badgeType) {
        const lightStyleMap = {
            'waiting': 'badge-light',
            'preparing': 'badge-light',
            'ready': 'badge-light',
            'completed': 'badge-light'
        };
        return lightStyleMap[badgeType] || 'badge-light';
    }
    
    /**
     * 獲取淡色背景
     */
    getLightBackground(badgeType) {
        const colorMap = {
            'waiting': '#fff3cd', // 淡黃色
            'preparing': '#d1ecf1', // 淡藍色
            'ready': '#d4edda', // 淡綠色
            'completed': '#e2e3e5' // 淡灰色
        };
        return colorMap[badgeType] || '#f8f9fa';
    }
    
    /**
     * 獲取淡色文字顏色
     */
    getLightTextColor(badgeType) {
        const colorMap = {
            'waiting': '#856404', // 深黃色
            'preparing': '#0c5460', // 深藍色
            'ready': '#155724', // 深綠色
            'completed': '#383d41' // 深灰色
        };
        return colorMap[badgeType] || '#6c757d';
    }
    
    /**
     * 初始化所有徽章為0（始終顯示）
     */
    initializeAllBadges() {
        console.log('🔄 初始化所有徽章為0（始終顯示）');
        
        Object.keys(this.badgeIdMap).forEach(badgeType => {
            this.updateBadgeElement(badgeType, 0);
        });
        
        this.updateLastUpdateTime();
    }
    
    /**
     * 更新所有徽章為0（靜態）
     */
    updateAllBadgesToZero() {
        console.log('🔄 更新所有徽章為0（靜態）');
        
        Object.keys(this.badgeIdMap).forEach(badgeType => {
            this.updateBadgeElement(badgeType, 0);
        });
        
        this.updateLastUpdateTime();
    }
    
    /**
     * 更新最後更新時間顯示（靜態）
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById('badge-last-update');
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timeElement.style.transition = 'none';
            timeElement.style.animation = 'none';
        }
    }
    
    // ==================== 事件處理（靜態，無動畫） ====================
    
    /**
     * 綁定事件
     */
    bindEvents() {
        // 徽章點擊事件（導航到對應標籤頁）
        Object.values(this.badgeIdMap).forEach(badgeId => {
            const badge = document.getElementById(badgeId);
            if (badge) {
                badge.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleBadgeClick(badgeId);
                });
            }
        });
        
        // 調試按鈕事件（從HTML中）
        const debugBtn = document.getElementById('debug-badges');
        if (debugBtn) {
            debugBtn.addEventListener('click', () => {
                this.debugCurrentState();
            });
        }
        
        const refreshBtn = document.getElementById('refresh-badges');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.forceUpdateFromUnifiedManager();
            });
        }
        
        const refreshAllBtn = document.getElementById('refresh-all-badges');
        if (refreshAllBtn) {
            refreshAllBtn.addEventListener('click', () => {
                this.forceUpdateFromUnifiedManager();
            });
        }
        
        const checkBtn = document.getElementById('check-badge-status');
        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                this.checkStatus();
            });
        }
        
        // 監聽統一數據更新事件（靜態）
        document.addEventListener('unified_data_updated', (event) => {
            console.log('📢 徽章管理器收到統一數據更新（靜態）');
        });
        
        // 監聽統一數據錯誤事件
        document.addEventListener('unified_data_error', (event) => {
            console.error('❌ 徽章管理器收到統一數據錯誤:', event.detail.error);
        });
    }
    
    /**
     * 處理徽章點擊事件
     */
    handleBadgeClick(badgeId) {
        console.log(`🔄 徽章點擊: ${badgeId}`);
        
        // 徽章到標籤頁的映射
        const tabMap = {
            'queue-badge': 'queue-tab',
            'preparing-orders-badge': 'preparing-tab',
            'ready-orders-badge': 'ready-tab',
            'completed-orders-badge': 'completed-tab'
        };
        
        const tabId = tabMap[badgeId];
        if (tabId) {
            const tabElement = document.getElementById(tabId);
            if (tabElement) {
                console.log(`🔄 切換到標籤頁: ${tabId}`);
                // 使用Bootstrap方法切換
                $(tabElement).tab('show');
            }
        }
    }
    
    /**
     * 分發徽章更新完成事件（靜態）
     */
    dispatchBadgeUpdatedEvent(badgeData) {
        const event = new CustomEvent('badges_updated_static', {
            detail: {
                badges: badgeData,
                timestamp: new Date().toISOString(),
                static: true
            },
            bubbles: true
        });
        document.dispatchEvent(event);
        console.log('📢 徽章更新完成事件已分發（靜態）');
    }
    
    // ==================== 輔助方法 ====================
    
    /**
     * 從統一數據管理器強制更新（靜態）
     */
    forceUpdateFromUnifiedManager() {
        if (window.unifiedDataManager) {
            console.log('🔄 強制從統一數據管理器更新（靜態）');
            window.unifiedDataManager.loadUnifiedData(true);
        } else {
            console.error('❌ 統一數據管理器未找到');
        }
    }
    
    /**
     * 檢查當前狀態
     */
    checkStatus() {
        const status = {
            unifiedDataManager: !!window.unifiedDataManager,
            badgeElements: {},
            lastUpdateTime: this.getLastUpdateTime()
        };
        
        // 檢查所有徽章元素
        Object.entries(this.badgeIdMap).forEach(([type, id]) => {
            const element = document.getElementById(id);
            status.badgeElements[type] = {
                exists: !!element,
                text: element ? element.textContent : 'N/A',
                visible: element ? (element.style.display !== 'none' && element.style.visibility !== 'hidden') : false,
                hasItems: element ? element.classList.contains('has-items') : false,
                style: element ? element.className : 'N/A'
            };
        });
        
        console.log('🔍 徽章管理器狀態檢查:', status);
        return status;
    }
    
    /**
     * 調試當前狀態
     */
    debugCurrentState() {
        const state = this.checkStatus();
        
        // 顯示調試信息
        alert(`徽章管理器調試信息：
        
統一數據管理器: ${state.unifiedDataManager ? '✓ 已連接' : '✗ 未連接'}
最後更新時間: ${state.lastUpdateTime || '無'}
        
徽章狀態:
- 等待中 (#queue-badge): ${state.badgeElements.waiting.exists ? '存在' : '缺失'} (${state.badgeElements.waiting.text}) [可見: ${state.badgeElements.waiting.visible}]
- 製作中 (#preparing-orders-badge): ${state.badgeElements.preparing.exists ? '存在' : '缺失'} (${state.badgeElements.preparing.text}) [可見: ${state.badgeElements.preparing.visible}]
- 已就緒 (#ready-orders-badge): ${state.badgeElements.ready.exists ? '存在' : '缺失'} (${state.badgeElements.ready.text}) [可見: ${state.badgeElements.ready.visible}]
- 已提取 (#completed-orders-badge): ${state.badgeElements.completed.exists ? '存在' : '缺失'} (${state.badgeElements.completed.text}) [可見: ${state.badgeElements.completed.visible}]`);
    }
    
    /**
     * 獲取最後更新時間
     */
    getLastUpdateTime() {
        const timeElement = document.getElementById('badge-last-update');
        return timeElement ? timeElement.textContent : null;
    }
    
    /**
     * 獲取當前徽章值
     */
    getCurrentBadgeValues() {
        const values = {};
        
        Object.entries(this.badgeIdMap).forEach(([type, id]) => {
            const element = document.getElementById(id);
            if (element) {
                values[type] = parseInt(element.textContent) || 0;
            }
        });
        
        return values;
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理徽章管理器...');
        // 移除所有事件監聽器
        Object.values(this.badgeIdMap).forEach(badgeId => {
            const badge = document.getElementById(badgeId);
            if (badge) {
                badge.replaceWith(badge.cloneNode(true)); // 移除事件監聽器
            }
        });
        console.log('✅ 徽章管理器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.BadgeManager = BadgeManager;
}