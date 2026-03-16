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

// ========== 訂單狀態更新器 ==========
class UnifiedOrderUpdater {
    constructor(orderId) {
        this.orderId = orderId;
        this.updateInterval = null;
        this.isRunning = false;
        this.updateCount = 0;
        this.maxUpdates = 120; // 最多更新120次（60分鐘）
    }
    
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        console.log('啟動訂單狀態更新器，訂單ID:', this.orderId);
        
        // 立即更新一次
        this.updateOrderStatus();
        
        // 每30秒更新一次（更頻繁的更新）
        this.updateInterval = setInterval(() => {
            this.updateOrderStatus();
        }, 10000); // 改為10秒更新一次
    }
    
    stop() {
        this.isRunning = false;
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            console.log('訂單狀態更新器已停止');
        }
    }
    
    async updateOrderStatus() {
        // 檢查是否達到最大更新次數
        if (this.updateCount >= this.maxUpdates) {
            console.log('達到最大更新次數，停止更新器');
            this.stop();
            return;
        }
        
        this.updateCount++;
        
        try {
            // ✅ 修復：使用正確的 API 路徑
            // 原路徑：/eshop/api/order-status/${this.orderId}/
            // 正確路徑：/eshop/order/api/order-status/${this.orderId}/
            const apiUrl = `/eshop/order/api/order-status/${this.orderId}/`;
            console.log('調用 API:', apiUrl);
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態碼: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                console.error('獲取訂單狀態失敗:', data.error);
                return;
            }
            
            console.log('訂單狀態更新:', data);
            this.updateDisplay(data);
            
            // 如果訂單已完成，停止更新
            if (data.is_ready || data.status === 'completed' || data.status === 'ready') {
                console.log('訂單已完成，停止更新器');
                this.stop();
                
                // 顯示完成消息
                setTimeout(() => {
                    if (document.getElementById('ready-section')) {
                        document.getElementById('ready-section').style.display = 'block';
                    }
                }, 1000);
            }
            
        } catch (error) {
            console.error('訂單狀態更新失敗:', error);
        }
    }
    
    updateDisplay(data) {
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
        const queueMessage = document.getElementById('queue-message');
        
        if (queueStatusText) queueStatusText.textContent = data.queue_display || '等待系統處理...';
        if (countdownText) countdownText.textContent = data.remaining_display || '';
        if (queueMessage) queueMessage.textContent = data.queue_message || '';
        
        // 更新預計時間
        const estimatedTimeElement = document.querySelector('#estimated-time-display .font-weight-bold');
        if (estimatedTimeElement && data.estimated_time) {
            estimatedTimeElement.textContent = data.estimated_time;
        }
        
        // 更新完成狀態
        if (data.is_ready) {
            const queueInfoSection = document.getElementById('queue-info-section');
            const readySection = document.getElementById('ready-section');
            
            if (queueInfoSection) queueInfoSection.style.display = 'none';
            if (readySection) readySection.style.display = 'block';
        }
    }
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
        
        // 啟動訂單狀態更新器（放寬條件：允許 paid 或 pending 狀態）
        const shouldStartUpdater = orderId && 
            (paymentStatus === 'paid' || paymentStatus === 'pending') &&
            isCoffeeOrder && !isBeansOnly;
        
        if (shouldStartUpdater) {
            console.log("啟動訂單狀態更新器，訂單ID:", orderId);
            window.orderUpdater = new UnifiedOrderUpdater(orderId);
            window.orderUpdater.start();
            
            // 添加調試信息
            console.log('訂單狀態更新器已啟動，將每10秒更新一次');
            console.log('啟動條件:', {
                orderId,
                paymentStatus,
                isCoffeeOrder,
                isBeansOnly,
                shouldStartUpdater
            });
        } else {
            console.log('不啟動訂單狀態更新器，原因:', {
                hasOrderId: !!orderId,
                paymentStatus,
                isCoffeeOrder,
                isBeansOnly,
                shouldStartUpdater
            });
        }
        
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
    console.error('JavaScript錯誤被捕獲:', event.error);
    event.preventDefault();
    return true;
});

// 防止未處理的Promise拒絕
window.addEventListener('unhandledrejection', function(event) {
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// ========== 全局導出 ==========
// 確保函數在全局可用
window.copyPickupCode = copyPickupCode;
window.saveAsImage = saveAsImage;
window.showMessage = showMessage;
window.UnifiedOrderUpdater = UnifiedOrderUpdater;
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
