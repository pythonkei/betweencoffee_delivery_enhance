// static/js/staff-order-management/subtab-manager.js
// ==================== 自定義 Tab 管理器 - 解決 Bootstrap 嵌套 tab 只能切換一次的問題 ====================
// 最後更新: 2026-07-11
// 
// 問題背景：
// Bootstrap 4.6 的 tab 組件在處理嵌套 tab 時，_activate() 方法中的 _findActive()
// 會因為 DOM 嵌套結構導致狀態查找混亂，造成 tab 只能切換一次。
// 
// 根本原因：
// 主 tab 的 .tab-content 內部包含了子 tab 的 .tab-content，Bootstrap 的 _findActive()
// 在遍歷 .tab-pane 時會找到嵌套的子 .tab-pane，導致 active 狀態判斷錯誤。
// 
// 解決方案：
// 所有 tab（主 tab + 子 tab）都不使用 Bootstrap 的 data-toggle="tab"，
// 改用自定義點擊事件手動切換，直接操作 CSS class 來控制 tab-pane 的顯示/隱藏。

class SubtabManager {
    constructor() {
        console.log('🔄 初始化自定義 Tab 管理器...');
        this.initialized = false;
    }

    init() {
        if (this.initialized) {
            console.log('⚠️ 自定義 Tab 管理器已初始化，跳過');
            return;
        }

        console.log('🔄 初始化自定義 Tab 管理器...');
        
        // 掛載到 window 方便其他組件存取（如 BadgeManager）
        window.subtabManagerInstance = this;
        
        // 1. 初始化主 tab 組（使用自定義切換，繞過 Bootstrap bug）
        this.initMainTabs();
        
        // 2. 初始化子 tab 組
        this.initSubtabGroup('queueSubTabs', 'queueSubTabsContent');
        this.initSubtabGroup('preparingSubTabs', 'preparingSubTabsContent');
        
        this.initialized = true;
        console.log('✅ 自定義 Tab 管理器初始化完成');
    }

    /**
     * 初始化主 tab 組（製作隊列、製作中、已就緒、已提取）
     * 不使用 Bootstrap data-toggle，改用自定義切換
     */
    initMainTabs() {
        const tabsContainer = document.getElementById('orderTabs');
        const contentContainer = document.getElementById('orderTabsContent');
        
        if (!tabsContainer || !contentContainer) {
            console.warn('⚠️ 主 tab 組未找到');
            return;
        }

        const tabLinks = tabsContainer.querySelectorAll('.nav-link');
        
        tabLinks.forEach(tabLink => {
            // 移除 Bootstrap 的 data-toggle 屬性
            tabLink.removeAttribute('data-toggle');
            
            // 移除舊的事件監聽器（克隆替換方式）
            const newTabLink = tabLink.cloneNode(true);
            tabLink.parentNode.replaceChild(newTabLink, tabLink);
            
            // 綁定自定義點擊事件
            newTabLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchMainTab(newTabLink, tabsContainer, contentContainer);
            });
        });

        console.log(`✅ 主 tab 組初始化完成 (${tabLinks.length} 個標籤頁)`);
    }

    /**
     * 切換主 tab
     */
    switchMainTab(targetTab, tabsContainer, contentContainer) {
        // 如果目標 tab 已經是 active，不做任何事
        if (targetTab.classList.contains('active')) {
            return;
        }

        // 獲取目標 pane ID
        const targetId = targetTab.getAttribute('href').replace('#', '');
        const targetPane = document.getElementById(targetId);
        
        if (!targetPane) {
            console.error(`❌ 未找到主 pane: #${targetId}`);
            return;
        }

        // 1. 切換 tab 導航的 active 狀態
        const currentActiveTab = tabsContainer.querySelector('.nav-link.active');
        if (currentActiveTab) {
            currentActiveTab.classList.remove('active');
            currentActiveTab.setAttribute('aria-selected', 'false');
        }
        
        targetTab.classList.add('active');
        targetTab.setAttribute('aria-selected', 'true');

        // 2. 切換 tab 內容的 active 狀態
        // 注意：只切換直接子層級的 .tab-pane，不影響嵌套的子 tab
        const currentActivePane = contentContainer.querySelector(':scope > .tab-pane.active');
        if (currentActivePane) {
            currentActivePane.classList.remove('active', 'show');
        }
        
        targetPane.classList.add('active', 'show');

        console.log(`✅ 主 tab 切換: ${targetId}`);
        
        // 3. 觸發自定義事件
        const event = new CustomEvent('maintab_changed', {
            detail: {
                tabId: targetId,
                tabElement: targetTab,
                paneElement: targetPane
            },
            bubbles: true
        });
        tabsContainer.dispatchEvent(event);
    }

    /**
     * 初始化一組子標籤頁
     * @param {string} tabsId - 子 tab 導航欄的 ID
     * @param {string} contentId - 子 tab 內容容器的 ID
     */
    initSubtabGroup(tabsId, contentId) {
        const tabsContainer = document.getElementById(tabsId);
        const contentContainer = document.getElementById(contentId);
        
        if (!tabsContainer || !contentContainer) {
            console.warn(`⚠️ 子標籤頁組未找到: ${tabsId} / ${contentId}`);
            return;
        }

        const tabLinks = tabsContainer.querySelectorAll('.nav-link');
        
        tabLinks.forEach(tabLink => {
            // 移除 Bootstrap 的 data-toggle 屬性
            tabLink.removeAttribute('data-toggle');
            
            // 移除舊的事件監聽器
            const newTabLink = tabLink.cloneNode(true);
            tabLink.parentNode.replaceChild(newTabLink, tabLink);
            
            // 綁定自定義點擊事件
            newTabLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(newTabLink, tabsContainer, contentContainer);
            });
        });

        console.log(`✅ 子標籤頁組初始化: ${tabsId} (${tabLinks.length} 個標籤頁)`);
    }

    /**
     * 切換子標籤頁
     * @param {HTMLElement} targetTab - 目標 tab 元素
     * @param {HTMLElement} tabsContainer - tab 導航容器
     * @param {HTMLElement} contentContainer - tab 內容容器
     */
    switchTab(targetTab, tabsContainer, contentContainer) {
        // 如果目標 tab 已經是 active，不做任何事
        if (targetTab.classList.contains('active')) {
            return;
        }

        // 獲取目標 pane ID
        const targetId = targetTab.getAttribute('href').replace('#', '');
        const targetPane = document.getElementById(targetId);
        
        if (!targetPane) {
            console.error(`❌ 未找到目標 pane: #${targetId}`);
            return;
        }

        // 1. 切換 tab 導航的 active 狀態
        const currentActiveTab = tabsContainer.querySelector('.nav-link.active');
        if (currentActiveTab) {
            currentActiveTab.classList.remove('active');
            currentActiveTab.setAttribute('aria-selected', 'false');
        }
        
        targetTab.classList.add('active');
        targetTab.setAttribute('aria-selected', 'true');

        // 2. 切換 tab 內容的 active 狀態
        const currentActivePane = contentContainer.querySelector('.tab-pane.active');
        if (currentActivePane) {
            currentActivePane.classList.remove('active', 'show');
        }
        
        targetPane.classList.add('active', 'show');

        console.log(`✅ 子標籤頁切換: ${targetId}`);
        
        // 3. 觸發自定義事件
        const event = new CustomEvent('subtab_changed', {
            detail: {
                tabId: targetId,
                tabElement: targetTab,
                paneElement: targetPane,
                tabsContainer: tabsContainer,
                contentContainer: contentContainer
            },
            bubbles: true
        });
        tabsContainer.dispatchEvent(event);
    }

    /**
     * 通過 ID 切換到指定子標籤頁
     * @param {string} tabId - 目標 tab 的 ID（如 'waiting-tab'）
     */
    switchToTabById(tabId) {
        const tab = document.getElementById(tabId);
        if (!tab) {
            console.warn(`⚠️ 未找到子標籤頁: #${tabId}`);
            return false;
        }

        // 找到所屬的 tab 組
        const tabsContainer = tab.closest('.staff-subnav-tabs');
        if (!tabsContainer) {
            console.warn(`⚠️ 未找到子標籤頁容器`);
            return false;
        }

        // 找到對應的內容容器（下一個兄弟元素）
        const contentContainer = tabsContainer.nextElementSibling;
        if (!contentContainer || !contentContainer.classList.contains('tab-content')) {
            console.warn(`⚠️ 未找到子標籤頁內容容器`);
            return false;
        }

        this.switchTab(tab, tabsContainer, contentContainer);
        return true;
    }

    /**
     * 通過 ID 切換到指定主 tab
     * @param {string} tabId - 目標主 tab 的 ID（如 'queue-tab'）
     */
    switchToMainTabById(tabId) {
        const tab = document.getElementById(tabId);
        if (!tab) {
            console.warn(`⚠️ 未找到主 tab: #${tabId}`);
            return false;
        }

        const tabsContainer = document.getElementById('orderTabs');
        const contentContainer = document.getElementById('orderTabsContent');
        
        if (!tabsContainer || !contentContainer) {
            console.warn('⚠️ 主 tab 容器未找到');
            return false;
        }

        this.switchMainTab(tab, tabsContainer, contentContainer);
        return true;
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.SubtabManager = SubtabManager;
    console.log('🌍 SubtabManager 已註冊到 window 對象');
}
