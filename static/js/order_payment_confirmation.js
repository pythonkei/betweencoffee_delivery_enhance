// static/js/order_payment_confirmation.js
// ✅ 簡化版 - 移除過度複雜的錯誤處理和圖片保存功能

// ========== 基礎工具函數（簡化版） ==========
function showMessage(message, type = "info") {
    console.log(`📢 ${type}: ${message}`);
    
    // 使用簡單的 alert 或 console 輸出
    if (type === 'error') {
        console.error(message);
    } else if (type === 'success') {
        console.log(message);
    }
    
    // 可以選擇性地顯示簡單的提示
    if (window.toastr) {
        // 如果有 toastr 庫，使用它
        toastr[type === 'error' ? 'error' : type === 'success' ? 'success' : 'info'](message);
    }
}

function copyPickupCode(pickupCode) {
    console.log("複製提取碼:", pickupCode);
    
    if (!pickupCode || pickupCode === 'None' || pickupCode === '') {
        showMessage("提取碼不存在", "error");
        return;
    }
    
    // 使用簡單的複製方法
    const textArea = document.createElement("textarea");
    textArea.value = pickupCode;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage("提取碼已複製到剪貼簿", "success");
        } else {
            showMessage("複製失敗，請手動複製提取碼: " + pickupCode, "error");
        }
    } catch (err) {
        console.error('複製失敗:', err);
        showMessage("複製失敗，請手動複製提取碼: " + pickupCode, "error");
    }
    
    document.body.removeChild(textArea);
}

// ========== 訂單狀態更新器（簡化版） ==========
// 注意：完整的更新器邏輯已移至 unified-order-updater.js
// 此處只保留基本的更新顯示功能

function updatePaymentConfirmationDisplay(data) {
    // 根據狀態顯示不同的消息
    const queueMessage = document.getElementById('queue-message');
    if (queueMessage) {
        switch(data.status) {
            case 'preparing':
                queueMessage.textContent = '您的訂單正在製作中，請耐心等候...';
                break;
            case 'ready':
                queueMessage.textContent = '您的訂單已準備就緒，請前往取餐！';
                break;
            default:
                queueMessage.textContent = data.queue_message || '';
        }
    }
    
    // 更新進度條
    const progressBar = document.getElementById('order-progress');
    const progressText = document.getElementById('progress-text');
    
    if (progressBar && progressText && data.progress_percentage !== undefined) {
        const progress = Math.max(0, Math.min(100, data.progress_percentage));
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressText.textContent = data.progress_display || `${progress}% 完成`;
        
        // 添加動畫效果
        progressBar.classList.add('progress-bar-animated');
    }
    
    // 更新隊列信息
    const queueStatusText = document.getElementById('queue-status-text');
    const countdownText = document.getElementById('countdown-text');
    
    if (queueStatusText) queueStatusText.textContent = data.queue_display || '等待系統處理...';
    if (countdownText) countdownText.textContent = data.remaining_display || '';
    
    // 更新預計時間
    const estimatedTimeElement = document.querySelector('#estimated-time-display .font-weight-bold');
    if (estimatedTimeElement && data.estimated_time) {
        estimatedTimeElement.textContent = data.estimated_time;
    }
    
    // 更新完成狀態
    if (data.is_ready || data.status === 'ready') {
        const queueInfoSection = document.getElementById('queue-info-section');
        const readySection = document.getElementById('ready-section');
        
        if (queueInfoSection) queueInfoSection.style.display = 'none';
        if (readySection) readySection.style.display = 'block';
    }
    
    // 添加調試日誌
    console.log(`✅ 支付確認頁面更新: status=${data.status}, progress=${data.progress_percentage}%`);
}

// ========== 頁面初始化 ==========
function initOrderConfirmationPage() {
    console.log("初始化訂單確認頁面");
    
    // 等待數據屬性設置的函數
    function waitForDataAttributes() {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                const orderId = document.body.dataset.orderId;
                if (orderId !== undefined) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 50);
            
            // 5秒後超時
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve();
            }, 5000);
        });
    }
    
    // 使用 Promise 等待數據屬性設置
    waitForDataAttributes().then(() => {
        // 從數據屬性獲取訂單信息
        const orderId = document.body.dataset.orderId;
        const paymentStatus = document.body.dataset.paymentStatus;
        const isCoffeeOrder = document.body.dataset.isCoffeeOrder === 'true';
        const isBeansOnly = document.body.dataset.isBeansOnly === 'true';
        
        console.log("訂單信息:", {
            orderId,
            paymentStatus,
            isCoffeeOrder,
            isBeansOnly
        });
        
        // 獲取提取碼
        const pickupCode = document.getElementById('pickup-code-display')?.textContent?.trim() || '';
        
        // 綁定複製按鈕事件
        const copyBtn = document.getElementById('copy-pickup-code-btn');
        
        if (copyBtn && pickupCode) {
            copyBtn.addEventListener('click', function() {
                copyPickupCode(pickupCode);
            });
            console.log("複製按鈕事件綁定成功");
        }
        
        // 移除圖片保存功能，因為它過於複雜且容易出錯
        const saveBtn = document.getElementById('save-image-btn');
        if (saveBtn) {
            saveBtn.style.display = 'none'; // 隱藏保存按鈕
            console.log("圖片保存按鈕已隱藏");
        }
        
        // 注意：訂單狀態更新器現在由 unified-order-updater.js 自動處理
        // 該文件會在頁面加載時自動初始化，無需在此手動啟動
        
        console.log('訂單狀態更新器將由 unified-order-updater.js 自動處理');
        console.log('啟動條件檢查:', {
            orderId,
            paymentStatus,
            isCoffeeOrder,
            isBeansOnly,
            shouldStartUpdater: orderId && 
                (paymentStatus === 'paid' || paymentStatus === 'pending') &&
                isCoffeeOrder && !isBeansOnly
        });
        
        // 添加支付超時倒計時（如果支付狀態為pending）
        if (paymentStatus === 'pending') {
            startPaymentTimeoutCountdown();
        }
    }).catch(error => {
        console.error('等待數據屬性時發生錯誤:', error);
    });
}

// ========== 支付超時倒計時 ==========
function startPaymentTimeoutCountdown() {
    const countdownElement = document.getElementById('payment-timeout-countdown');
    if (!countdownElement) return;
    
    let minutes = 5;
    let seconds = 0;
    
    const updateCountdown = () => {
        countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        if (minutes === 0 && seconds === 0) {
            clearInterval(countdownInterval);
            countdownElement.textContent = '00:00';
            // 可以添加超時處理邏輯
        } else {
            if (seconds === 0) {
                minutes--;
                seconds = 59;
            } else {
                seconds--;
            }
        }
    };
    
    // 立即更新一次
    updateCountdown();
    
    // 每秒更新一次
    const countdownInterval = setInterval(updateCountdown, 1000);
}

// ========== 全局錯誤處理（簡化版） ==========
// 只處理關鍵錯誤，避免過度防護
window.addEventListener('error', function(event) {
    // 只記錄錯誤，不阻止默認行為
    console.error('JavaScript錯誤被捕獲:', event.error);
    event.stopPropagation();
    return false; // 返回false讓瀏覽器處理錯誤
});

// 防止未處理的Promise拒絕
window.addEventListener('unhandledrejection', function(event) {
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// ========== 全局導出 ==========
// 確保函數在全局可用
window.copyPickupCode = copyPickupCode;
window.showMessage = showMessage;
window.updatePaymentConfirmationDisplay = updatePaymentConfirmationDisplay;
window.initOrderConfirmationPage = initOrderConfirmationPage;

// 頁面加載完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        try {
            initOrderConfirmationPage();
        } catch (error) {
            console.error('頁面初始化失敗:', error);
            // 不拋出錯誤，防止頁面重定向
        }
    });
} else {
    // 如果DOM已經加載完成，直接初始化
    setTimeout(function() {
        try {
            initOrderConfirmationPage();
        } catch (error) {
            console.error('頁面初始化失敗:', error);
            // 不拋出錯誤，防止頁面重定向
        }
    }, 100);
}
