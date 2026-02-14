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
    }
    
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        console.log('啟動訂單狀態更新器，訂單ID:', this.orderId);
        
        // 立即更新一次
        this.updateOrderStatus();
        
        // 每30秒更新一次
        this.updateInterval = setInterval(() => {
            this.updateOrderStatus();
        }, 30000);
    }
    
    stop() {
        this.isRunning = false;
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            console.log('訂單狀態更新器已停止');
        }
    }
    
    async updateOrderStatus() {
        try {
            const response = await fetch(`/eshop/api/order-status/${this.orderId}/`);
            
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態碼: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                console.error('獲取訂單狀態失敗:', data.error);
                return;
            }
            
            this.updateDisplay(data);
            
            // 如果訂單已完成，停止更新
            if (data.is_ready || data.status === 'completed') {
                this.stop();
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
    
    // 獲取模板變量
    const pickupCode = document.getElementById('pickup-code-display')?.textContent || 
                      document.querySelector('.display-4.text-primary')?.textContent;
    const orderId = document.querySelector('h5:contains("訂單編號")')?.textContent?.match(/#(\d+)/)?.[1];
    
    console.log("提取到的提取碼:", pickupCode);
    console.log("提取到的訂單ID:", orderId);
    
    // 綁定按鈕事件
    const copyBtn = document.getElementById('copy-pickup-code-btn');
    const saveBtn = document.getElementById('save-image-btn');
    
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            copyPickupCode(pickupCode);
        });
        console.log("複製按鈕事件綁定成功");
    }
    
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveAsImage(orderId);
        });
        console.log("保存按鈕事件綁定成功");
    }
    
    // 啟動訂單狀態更新器
    const paymentStatus = document.body.dataset.paymentStatus;
    const orderType = document.body.dataset.orderType;
    
    if (orderId && paymentStatus === 'paid' && orderType && orderType.includes('coffee') && !orderType.includes('beans_only')) {
        console.log("啟動訂單狀態更新器");
        window.orderUpdater = new UnifiedOrderUpdater(orderId);
        window.orderUpdater.start();
    }
}

// ========== 全局導出 ==========
// 確保函數在全局可用
window.copyPickupCode = copyPickupCode;
window.saveAsImage = saveAsImage;
window.showMessage = showMessage;
window.UnifiedOrderUpdater = UnifiedOrderUpdater;

// 頁面加載完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOrderConfirmationPage);
} else {
    initOrderConfirmationPage();
}