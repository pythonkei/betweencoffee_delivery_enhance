// static/js/order_payment_confirmation.js

// ========== 基礎工具函數 ==========
function showMessage(message, type = "info") {
    console.log("顯示消息:", message, type);
    
    // 移除現有消息
    const existingAlert = document.querySelector('.custom-alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 確定 Bootstrap 類名
    const alertClass = type === 'success' ? 'alert-success' : 
                       type === 'error' ? 'alert-danger' : 'alert-info';
    
    // 創建消息元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert ${alertClass} alert-dismissible fade show`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="close" onclick="this.parentElement.remove()">
            <span>&times;</span>
        </button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3秒後自動消失
    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

function fallbackCopyText(text) {
    console.log("使用降級複製方案");
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage("✅ 提取碼已複製到剪貼簿", "success");
        } else {
            showMessage("❌ 複製失敗，請手動複製提取碼: " + text, "error");
        }
    } catch (err) {
        console.error('降級複製失敗:', err);
        showMessage("❌ 複製失敗，請手動複製提取碼: " + text, "error");
    }
    
    document.body.removeChild(textArea);
}

// ========== 核心功能函數 ==========
function copyPickupCode(pickupCode) {
    console.log("copyPickupCode 被調用，提取碼:", pickupCode);
    
    if (!pickupCode || pickupCode === 'None' || pickupCode === '') {
        showMessage("❌ 提取碼不存在", "error");
        return;
    }
    
    // 方法1: 使用現代的 Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(pickupCode).then(function() {
            showMessage("✅ 提取碼已複製到剪貼簿", "success");
        }).catch(function(err) {
            console.error('Clipboard API 失敗:', err);
            fallbackCopyText(pickupCode);
        });
    } else {
        // 方法2: 降級方案
        fallbackCopyText(pickupCode);
    }
}

function saveAsImage(orderId) {
    console.log("saveAsImage 被調用，訂單ID:", orderId);
    
    // 檢查 html2canvas 是否可用
    if (typeof html2canvas === 'undefined') {
        console.error("html2canvas 未定義");
        showMessage("❌ 圖片保存功能暫時不可用", "error");
        return;
    }
    
    const qrcodeSection = document.getElementById('qrcode-section');
    if (!qrcodeSection) {
        console.error("找不到保存區域: qrcode-section");
        showMessage("❌ 找不到保存區域", "error");
        return;
    }
    
    // 顯示保存中提示
    const saveBtn = document.getElementById('save-image-btn');
    if (saveBtn) {
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>保存中...';
        saveBtn.disabled = true;
        
        // 配置 html2canvas
        const options = {
            scale: 2,
            useCORS: true,
            backgroundColor: '#ffffff',
            logging: false
        };
        
        html2canvas(qrcodeSection, options).then(function(canvas) {
            console.log("截圖完成");
            
            // 創建下載鏈接
            const link = document.createElement('a');
            link.download = `between_coffee_order_${orderId}.png`;
            link.href = canvas.toDataURL("image/png");
            
            // 觸發下載
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 恢復按鈕狀態
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            
            showMessage("✅ 圖片保存成功", "success");
            
        }).catch(function(error) {
            console.error("截圖失敗:", error);
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            showMessage("❌ 圖片保存失敗，請稍後重試", "error");
        });
    }
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
        
        // 綁定按鈕事件
        const copyBtn = document.getElementById('copy-pickup-code-btn');
        const saveBtn = document.getElementById('save-image-btn');
        
        if (copyBtn && pickupCode) {
            copyBtn.addEventListener('click', function() {
                copyPickupCode(pickupCode);
            });
            console.log("複製按鈕事件綁定成功");
        }
        
        if (saveBtn && orderId) {
            saveBtn.addEventListener('click', function() {
                saveAsImage(orderId);
            });
            console.log("保存按鈕事件綁定成功");
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

// ========== 全局錯誤處理 ==========
// 防止JavaScript錯誤導致頁面重定向
window.addEventListener('error', function(event) {
    // 檢查是否是第三方庫的錯誤（如 Bootstrap 的 Explain 錯誤）
    if (event.error && event.error.message && event.error.message.includes('Explain')) {
        console.warn('第三方庫錯誤被捕獲（已安全處理）:', event.error.message);
        event.preventDefault();
        event.stopPropagation();
        return true; // 阻止錯誤繼續傳播
    }
    
    console.error('JavaScript錯誤被捕獲:', event.error);
    // 防止錯誤傳播，但不阻止默認行為
    event.stopPropagation();
    return false; // 返回false讓瀏覽器處理錯誤
});

// 防止未處理的Promise拒絕
window.addEventListener('unhandledrejection', function(event) {
    // 檢查是否是第三方庫的錯誤
    if (event.reason && event.reason.message && event.reason.message.includes('Explain')) {
        console.warn('第三方庫Promise錯誤被捕獲（已安全處理）:', event.reason.message);
        event.preventDefault();
        return;
    }
    
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// 添加更安全的錯誤處理
(function() {
    // 保存原始的 console.error
    const originalConsoleError = console.error;
    
    // 重寫 console.error 以過濾第三方庫錯誤
    console.error = function(...args) {
        // 檢查是否是第三方庫的錯誤
        const errorString = args.map(arg => String(arg)).join(' ');
        if (errorString.includes('Explain') || errorString.includes('bootstrap.bundle.min.js')) {
            console.warn('第三方庫錯誤（已過濾）:', args);
            return;
        }
        
        // 調用原始的 console.error
        originalConsoleError.apply(console, args);
    };
})();

// ========== 全局導出 ==========
// 確保函數在全局可用
window.copyPickupCode = copyPickupCode;
window.saveAsImage = saveAsImage;
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
