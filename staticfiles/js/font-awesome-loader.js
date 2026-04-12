/**
 * Font Awesome 字體加載優化器
 * 解決 FOUT (Flash of Unstyled Text) 問題
 * 當 Font Awesome 字體加載完成後才顯示圖示，避免視覺抖動
 */

(function() {
    'use strict';
    
    // 檢查 Font Awesome 是否已加載
    function isFontAwesomeLoaded() {
        // 創建一個測試元素來檢查 Font Awesome 字體
        const testElement = document.createElement('span');
        testElement.style.cssText = 'font-family: "Font Awesome 6 Pro", "Font Awesome 6 Brands"; font-size: 16px; position: absolute; left: -9999px;';
        testElement.innerHTML = ''; // Font Awesome 心形圖示的 Unicode
        
        document.body.appendChild(testElement);
        
        // 獲取測試元素的寬度
        const initialWidth = testElement.offsetWidth;
        
        // 設置一個已知寬度的備用字體
        testElement.style.fontFamily = 'Arial, sans-serif';
        const fallbackWidth = testElement.offsetWidth;
        
        // 恢復 Font Awesome 字體
        testElement.style.fontFamily = '"Font Awesome 6 Pro", "Font Awesome 6 Brands"';
        const finalWidth = testElement.offsetWidth;
        
        document.body.removeChild(testElement);
        
        // 如果 Font Awesome 字體已加載，寬度應該與備用字體不同
        return initialWidth !== fallbackWidth || finalWidth !== fallbackWidth;
    }
    
    // 處理活動圖示的顯示
    function handleActivityIcons() {
        const activityIcons = document.querySelectorAll('.activity-icon');
        
        if (activityIcons.length === 0) {
            return;
        }
        
        // 檢查字體是否已加載
        if (isFontAwesomeLoaded()) {
            // 字體已加載，顯示所有圖示
            activityIcons.forEach(icon => {
                icon.style.opacity = '1';
                icon.style.visibility = 'visible';
            });
        } else {
            // 字體未加載，設置定時器重試
            setTimeout(handleActivityIcons, 100);
        }
    }
    
    // 初始化函數
    function initFontAwesomeLoader() {
        // 等待 DOM 完全加載
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', handleActivityIcons);
        } else {
            handleActivityIcons();
        }
        
        // 監聽字體加載事件
        document.fonts.ready.then(() => {
            // 字體加載完成後，確保所有圖示都顯示
            const activityIcons = document.querySelectorAll('.activity-icon');
            activityIcons.forEach(icon => {
                icon.style.opacity = '1';
            });
        });
    }
    
    // 啟動優化器
    initFontAwesomeLoader();
    
    // 導出函數供其他腳本使用
    window.FontAwesomeLoader = {
        isFontAwesomeLoaded: isFontAwesomeLoaded,
        handleActivityIcons: handleActivityIcons
    };
    
})();