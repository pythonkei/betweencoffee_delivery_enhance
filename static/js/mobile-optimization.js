/*
 * mobile-optimization.js
 * 移動端優化腳本
 * 為移動設備提供更好的交互體驗
 */

(function() {
    'use strict';
    
    console.log('📱 移動端優化腳本加載完成');
    
    // ========== 移動端檢測 ==========
    const isMobile = {
        Android: function() {
            return navigator.userAgent.match(/Android/i);
        },
        BlackBerry: function() {
            return navigator.userAgent.match(/BlackBerry/i);
        },
        iOS: function() {
            return navigator.userAgent.match(/iPhone|iPad|iPod/i);
        },
        Opera: function() {
            return navigator.userAgent.match(/Opera Mini/i);
        },
        Windows: function() {
            return navigator.userAgent.match(/IEMobile/i) || navigator.userAgent.match(/WPDesktop/i);
        },
        any: function() {
            return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
        },
        isTouchDevice: function() {
            return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        }
    };
    
    // ========== 移動端優化函數 ==========
    
    /**
     * 優化觸摸交互
     */
    function optimizeTouchInteractions() {
        if (!isMobile.isTouchDevice()) return;
        
        console.log('🖐️ 優化觸摸設備交互');
        
        // 防止雙擊縮放
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // 優化按鈕觸摸反饋
        const buttons = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
        buttons.forEach(button => {
            // 添加觸摸反饋類
            button.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });
            
            button.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            });
            
            // 防止觸摸時出現藍色高亮
            button.style.webkitTapHighlightColor = 'transparent';
        });
        
        // 優化輸入框
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // 防止iOS自動縮放
            input.addEventListener('focus', function() {
                if (isMobile.iOS()) {
                    setTimeout(() => {
                        this.style.fontSize = '16px';
                    }, 100);
                }
            });
        });
    }
    
    /**
     * 優化滾動體驗
     */
    function optimizeScrolling() {
        if (!isMobile.any()) return;
        
        console.log('🔄 優化移動端滾動');
        
        // 添加平滑滾動
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // 優化滾動容器
        const scrollContainers = document.querySelectorAll('.scrollable, .modal-body, .table-responsive');
        scrollContainers.forEach(container => {
            container.style.webkitOverflowScrolling = 'touch';
            container.style.overflowY = 'auto';
            
            // 防止滾動穿透
            container.addEventListener('touchmove', function(e) {
                e.stopPropagation();
            }, { passive: false });
        });
        
        // 修復iOS橡皮筋效果
        document.addEventListener('touchmove', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    /**
     * 優化表單輸入
     */
    function optimizeFormInputs() {
        console.log('📝 優化移動端表單輸入');
        
        // 自動聚焦第一個輸入框（移動端優化）
        const firstInput = document.querySelector('input[type="text"], input[type="email"], input[type="tel"], input[type="number"]');
        if (firstInput && isMobile.any()) {
            setTimeout(() => {
                firstInput.focus();
            }, 300);
        }
        
        // 優化數字輸入
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(input => {
            input.setAttribute('pattern', '[0-9]*');
            input.setAttribute('inputmode', 'numeric');
        });
        
        // 優化電話輸入
        const telInputs = document.querySelectorAll('input[type="tel"]');
        telInputs.forEach(input => {
            input.setAttribute('inputmode', 'tel');
        });
        
        // 優化郵件輸入
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.setAttribute('inputmode', 'email');
        });
    }
    
    /**
     * 優化圖片加載
     */
    function optimizeImages() {
        console.log('🖼️ 優化移動端圖片加載');
        
        // 懶加載圖片
        const images = document.querySelectorAll('img[data-src]');
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        } else {
            // 降級方案：直接加載所有圖片
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
        
        // 響應式圖片支持
        const pictureElements = document.querySelectorAll('picture');
        pictureElements.forEach(picture => {
            const sources = picture.querySelectorAll('source');
            sources.forEach(source => {
                // 確保移動端使用正確的圖片
                if (isMobile.any() && source.media && source.media.includes('max-width')) {
                    const img = picture.querySelector('img');
                    if (img && source.srcset) {
                        img.src = source.srcset.split(' ')[0];
                    }
                }
            });
        });
    }
    
    /**
     * 優化導航和菜單
     */
    function optimizeNavigation() {
        console.log('🧭 優化移動端導航');
        
        // 移動端漢堡菜單優化
        const navbarToggles = document.querySelectorAll('.navbar-toggler');
        navbarToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const navbarCollapse = document.querySelector(this.getAttribute('data-target') || '.navbar-collapse');
                if (navbarCollapse) {
                    navbarCollapse.classList.toggle('show');
                    
                    // 添加動畫效果
                    if (navbarCollapse.classList.contains('show')) {
                        navbarCollapse.style.maxHeight = navbarCollapse.scrollHeight + 'px';
                    } else {
                        navbarCollapse.style.maxHeight = '0';
                    }
                }
            });
        });
        
        // 下拉菜單優化（移動端）
        const dropdowns = document.querySelectorAll('.dropdown');
        dropdowns.forEach(dropdown => {
            if (isMobile.any()) {
                // 移動端：點擊切換
                dropdown.addEventListener('click', function(e) {
                    if (!this.classList.contains('show')) {
                        e.preventDefault();
                        this.classList.add('show');
                        
                        // 點擊外部關閉
                        document.addEventListener('click', function closeDropdown(event) {
                            if (!dropdown.contains(event.target)) {
                                dropdown.classList.remove('show');
                                document.removeEventListener('click', closeDropdown);
                            }
                        });
                    }
                });
            }
        });
    }
    
    /**
     * 優化性能
     */
    function optimizePerformance() {
        console.log('⚡ 優化移動端性能');
        
        // 減少重繪和重排
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                document.body.classList.add('resize-active');
                setTimeout(() => {
                    document.body.classList.remove('resize-active');
                }, 100);
            }, 250);
        });
        
        // 優化動畫性能
        const animatedElements = document.querySelectorAll('.animated, .fade-in, .slide-in');
        animatedElements.forEach(element => {
            element.style.willChange = 'transform, opacity';
        });
        
        // 禁用不必要的動畫（如果用戶偏好減少動畫）
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.scrollBehavior = 'auto';
            
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                el.style.animationDuration = '0.01ms';
                el.style.transitionDuration = '0.01ms';
            });
        }
    }
    
    /**
     * 優化通知和反饋
     */
    function optimizeNotifications() {
        console.log('🔔 優化移動端通知');
        
        // 移動端友好的提示
        window.showMobileToast = function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `mobile-toast toast-${type}`;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                z-index: 9999;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                max-width: 90%;
                text-align: center;
                animation: slideUp 0.3s ease;
            `;
            
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // 3秒後自動消失
            setTimeout(() => {
                toast.style.animation = 'slideDown 0.3s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, 3000);
            
            // 添加動畫樣式
            if (!document.querySelector('#mobile-toast-styles')) {
                const style = document.createElement('style');
                style.id = 'mobile-toast-styles';
                style.textContent = `
                    @keyframes slideUp {
                        from { transform: translateX(-50%) translateY(100px); opacity: 0; }
                        to { transform: translateX(-50%) translateY(0); opacity: 1; }
                    }
                    @keyframes slideDown {
                        from { transform: translateX(-50%) translateY(0); opacity: 1; }
                        to { transform: translateX(-50%) translateY(100px); opacity: 0; }
                    }
                `;
                document.head.appendChild(style);
            }
        };
        
        // 振動反饋（如果支持）
        if ('vibrate' in navigator && isMobile.any()) {
            window.vibrateFeedback = function(pattern = [50]) {
                try {
                    navigator.vibrate(pattern);
                } catch (e) {
                    console.log('振動功能不可用');
                }
            };
        }
    }
    
    /**
     * 優化深色模式
     */
    function optimizeDarkMode() {
        console.log('🌙 優化深色模式');
        
        // 檢測系統深色模式
        const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        function updateDarkMode(isDark) {
            if (isDark) {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.body.classList.add('dark-mode');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                document.body.classList.remove('dark-mode');
            }
        }
        
        // 初始設置
        updateDarkMode(darkModeMediaQuery.matches);
        
        // 監聽變化
        darkModeMediaQuery.addEventListener('change', (e) => {
            updateDarkMode(e.matches);
        });
        
        // 添加深色模式樣式
        if (!document.querySelector('#dark-mode-styles')) {
            const style = document.createElement('style');
            style.id = 'dark-mode-styles';
            style.textContent = `
                [data-theme="dark"] {
                    --bg-color: #121212;
                    --text-color: #e0e0e0;
                    --card-bg: #1e1e1e;
                    --border-color: #333;
                }
                
                .dark-mode {
                    background-color: var(--bg-color);
                    color: var(--text-color);
                }
                
                .dark-mode .card {
                    background-color: var(--card-bg);
                    border-color: var(--border-color);
                }
                
                .dark-mode .modal-content {
                    background-color: var(--card-bg);
                }
                
                .dark-mode .table {
                    color: var(--text-color);
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    /**
     * 優化網絡狀態
     */
    function optimizeNetworkStatus() {
        console.log('📶 優化網絡狀態檢測');
        
        // 檢測網絡狀態
        if ('onLine' in navigator) {
            function updateOnlineStatus() {
                const isOnline = navigator.onLine;
                
                if (!isOnline) {
                    showMobileToast('⚠️ 網絡連接已斷開', 'error');
                    
                    // 顯示離線提示
                    const offlineBanner = document.createElement('div');
                    offlineBanner.id = 'offline-banner';
                    offlineBanner.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        background: #dc3545;
                        color: white;
                        text-align: center;
                        padding: 10px;
                        z-index: 9998;
                        font-size: 14px;
                    `;
                    offlineBanner.textContent = '⚠️ 您目前處於離線狀態，部分功能可能受限';
                    document.body.appendChild(offlineBanner);
                } else {
                    const offlineBanner = document.getElementById('offline-banner');
                    if (offlineBanner) {
                        offlineBanner.remove();
                    }
                    showMobileToast('✅ 網絡連接已恢復', 'success');
                }
            }
            
            // 初始檢測
            updateOnlineStatus();
            
            // 監聽網絡狀態變化
            window.addEventListener('online', updateOnlineStatus);
            window.addEventListener('offline', updateOnlineStatus);
        }
    }
    
    /**
     * 優化頁面加載
     */
    function optimizePageLoad() {
        console.log('🚀 優化頁面加載');
        
        // 添加加載動畫
        if (!document.querySelector('#page-loader')) {
            const loader = document.createElement('div');
            loader.id = 'page-loader';
            loader.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                transition: opacity 0.3s ease;
            `;
            loader.innerHTML = `
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">加載中...</span>
                </div>
            `;
            document.body.appendChild(loader);
            
            // 頁面加載完成後隱藏加載動畫
            window.addEventListener('load', function() {
                setTimeout(() => {
                    loader.style.opacity = '0';
                    setTimeout(() => {
                        if (loader.parentNode) {
                            loader.parentNode.removeChild(loader);
                        }
                    }, 300);
                }, 500);
            });
        }
        
        // 優化字體加載
        if (isMobile.any()) {
            // 移動端使用系統字體以提高性能
            document.body.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        }
    }
    
    // ========== 初始化所有優化 ==========
    function initMobileOptimizations() {
        console.log('🚀 初始化移動端優化');
        
        // 執行所有優化函數
        optimizeTouchInteractions();
        optimizeScrolling();
        optimizeFormInputs();
        optimizeImages();
        optimizeNavigation();
        optimizePerformance();
        optimizeNotifications();
        optimizeDarkMode();
        optimizeNetworkStatus();
        optimizePageLoad();
        
        // 添加移動端標識類
        if (isMobile.any()) {
            document.documentElement.classList.add('is-mobile');
        }
        
        if (isMobile.iOS()) {
            document.documentElement.classList.add('is-ios');
        }
        
        if (isMobile.Android()) {
            document.documentElement.classList.add('is-android');
        }
        
        console.log('✅ 移動端優化完成');
    }
    
    // 頁面加載完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileOptimizations);
    } else {
        setTimeout(initMobileOptim