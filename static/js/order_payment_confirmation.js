// static/js/order_payment_confirmation.js
// ✅ 極簡版 - 移除所有狀態更新功能，只保留基本功能

// ========== 基礎工具函數 ==========
function copyPickupCode(pickupCode) {
    console.log("複製提取碼:", pickupCode);
    
    if (!pickupCode || pickupCode === 'None' || pickupCode === '') {
        alert("提取碼不存在");
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
            alert(`提取碼 ${pickupCode} 已複製到剪貼簿`);
        } else {
            alert(`複製失敗，請手動複製提取碼: ${pickupCode}`);
        }
    } catch (err) {
        console.error('複製失敗:', err);
        alert(`複製失敗，請手動複製提取碼: ${pickupCode}`);
    }
    
    document.body.removeChild(textArea);
}

// 保存二維碼圖片功能
function saveQRCodeImage() {
    console.log("開始保存二維碼圖片");
    
    // 檢查html2canvas是否可用
    if (typeof html2canvas === 'undefined') {
        alert('圖片保存功能暫時不可用，請稍後重試');
        return;
    }
    
    const qrcodeSection = document.getElementById('qrcode-section');
    if (!qrcodeSection) {
        alert('找不到保存區域');
        return;
    }
    
    // 獲取提取碼
    const pickupCodeElement = document.getElementById('pickup-code-display');
    const pickupCode = pickupCodeElement ? pickupCodeElement.textContent.trim() : "";
    
    // 禁用按鈕並顯示加載狀態
    const saveBtn = document.getElementById('save-image-btn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>生成中...';
    saveBtn.disabled = true;
    
    try {
        // 使用html2canvas生成圖片
        html2canvas(qrcodeSection, {
            scale: 2, // 提高分辨率
            backgroundColor: '#ffffff',
            useCORS: true,
            logging: false
        }).then(function(canvas) {
            // 創建下載鏈接
            const image = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = pickupCode ? `提取碼_${pickupCode}.png` : '訂單二維碼.png';
            link.href = image;
            
            // 觸發下載
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 恢復按鈕狀態
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            
            alert('圖片保存成功！');
            console.log("圖片保存成功");
        }).catch(function(error) {
            console.error('生成圖片失敗:', error);
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            alert('生成圖片失敗，請稍後重試');
        });
        
    } catch (error) {
        console.error('保存圖片失敗:', error);
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
        alert('保存圖片失敗，請稍後重試');
    }
}

// ========== 頁面初始化 ==========
function initOrderConfirmationPage() {
    console.log("初始化訂單確認頁面");
    
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
    
    // 綁定保存圖片按鈕事件
    const saveBtn = document.getElementById('save-image-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveQRCodeImage();
        });
        console.log("圖片保存按鈕事件綁定成功");
    }
    
    console.log("訂單確認頁面初始化完成");
}

// ========== 全局錯誤處理 ==========
// 過濾第三方庫錯誤
window.addEventListener('error', function(event) {
    const errorMessage = event.error ? event.error.toString() : '';
    
    // 檢查是否為第三方庫錯誤
    const isThirdPartyError = 
        errorMessage.includes('Explain is not defined') ||
        errorMessage.includes('bootstrap.bundle.min.js');
    
    if (isThirdPartyError) {
        // 第三方庫錯誤，只記錄警告
        console.warn('⚠️ 第三方庫錯誤（已過濾）:', errorMessage);
        event.stopPropagation();
        return false;
    } else {
        // 我們的代碼錯誤，記錄錯誤
        console.error('❌ JavaScript錯誤被捕獲:', event.error);
        event.stopPropagation();
        return false;
    }
});

// ========== 全局導出 ==========
window.copyPickupCode = copyPickupCode;
window.initOrderConfirmationPage = initOrderConfirmationPage;

// 頁面加載完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        try {
            initOrderConfirmationPage();
        } catch (error) {
            console.error('頁面初始化失敗:', error);
        }
    });
} else {
    // 如果DOM已經加載完成，直接初始化
    setTimeout(function() {
        try {
            initOrderConfirmationPage();
        } catch (error) {
            console.error('頁面初始化失敗:', error);
        }
    }, 100);
}
