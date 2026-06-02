/*
 * mobile-optimization-enhanced.js
 * 移動端優化增強腳本
 * 採用漸進式增強策略，只添加移動端特定功能
 * 避免與現有JavaScript衝突
 */

(function() {
    'use strict';
    
    console.log('📱 移動端優化增強腳本加載完成');
    
    // ========== 配置 ==========
    const CONFIG = {
        enableMobileOptimization: true,
        enableTouchOptimization: true,
        enablePerformanceOptimization: true,
        enableAccessibilityOptimization: true,
        debugMode: false
    };
    
    // ========== 移動端檢測 ==========
    const MobileDetector = {
        isMobile: function() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        },
        
        isTouchDevice: function() {
            return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        },
        
        isIOS: function() {
            return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        },
        
        isAndroid: function() {
            return /Android/.test(navigator.userAgent);
        },
        
        getDeviceType: function() {
            if (this.isIOS()) return 'ios';
            if (this.isAndroid()) return 'android';
            if (this.isMobile()) return 'mobile';
            return 'desktop';
        }
    };
    
    // ========== 移動端優化管理器 ==========
    class MobileOptimizationManager {
        constructor() {
            this.deviceType = MobileDetector.getDeviceType();
            this.isMobile = MobileDetector.isMobile();
            this.isTouch = MobileDetector.isTouchDevice();
            this.optimizations = [];
            this.initialized = false;
        }
        
        // 初始化移動端優化
        init() {
            if (this.initialized) return;
            
            console.log(`🚀 初始化移動端優化 (設備類型: ${this.deviceType})`);
            
            // 添加移動端標識類
            this.addDeviceClasses();
            
            // 根據配置啟用優化
            if (CONFIG.enableMobileOptimization) {
                this.enableMobileOptimizations();
            }
            
            if (CONFIG.enableTouchOptimization && this.isTouch) {
                this.enableTouchOptimizations();
            }
            
            if (CONFIG.enablePerformanceOptimization) {
                this.enablePerformanceOptimizations();
            }
            
            if (CONFIG.enableAccessibilityOptimization) {
                this.enableAccessibilityOptimizations();
            }
            
            this.initialized = true;
            console.log('✅ 移動端優化初始化完成');
        }
        
        // 添加設備類
        addDeviceClasses() {
            document.documentElement.classList.add(`device-${this.deviceType}`);
            
            if (this.isMobile) {
                document.documentElement.classList.add('is-mobile');
                document.body.classList.add('mobile-optimized');
            }
            
            if (this.isTouch) {
                document.documentElement.classList.add('is-touch');
            }
            
            if (this.isIOS) {
                document.documentElement.classList.add('is-ios');
            }
            
            if (this.isAndroid) {
                document.documentElement.classList.add('is-android');
            }
        }
        
        // 啟用移動端優化
        enableMobileOptimizations() {
            console.log('📱 啟用移動端優化');
            
            // 優化視口
            this.optimizeViewport();
            
            // 優化字體大小
            this.optimizeFontSizes();
            
            // 優化圖片
            this.optimizeImages();
            
            // 優化表單
            this.optimizeForms();
            
            // 優化導航
            this.optimizeNavigation();
        }
        
        // 啟用觸摸優化
        enableTouchOptimizations() {
            console.log('🖐️ 啟用觸摸優化');
            
            // 防止雙擊縮放
            this.preventDoubleTapZoom();
            
            // 優化觸摸反饋
            this.optimizeTouchFeedback();
            
            // 優化滾動
            this.optimizeScrolling();
            
            // 優化長按
            this.optimizeLongPress();
        }
        
        // 啟用性能優化
        enablePerformanceOptimizations() {
            console.log('⚡ 啟用性能優化');
            
            // 懶加載資源
            this.lazyLoadResources();
            
            // 優化動畫性能
            this.optimizeAnimationPerformance();
            
            // 減少重繪
            this.reduceRepaints();
            
            // 優化網絡請求
            this.optimizeNetworkRequests();
        }
        
        // 啟用可訪問性優化
        enableAccessibilityOptimizations() {
            console.log('♿ 啟用可訪問性優化');
            
            // 增加觸摸目標尺寸
            this.increaseTouchTargets();
            
            // 優化焦點管理
            this.optimizeFocusManagement();
            
            // 支持減少動畫
            this.supportReducedMotion();
            
            // 支持高對比度
            this.supportHighContrast();
        }
        
        // ========== 具體優化方法 ==========
        
        // 優化視口
        optimizeViewport() {
            // 確保視口設置正確
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (viewportMeta) {
                let content = viewportMeta.getAttribute('content');
                if (!content.includes('maximum-scale')) {
                    content += ', maximum-scale=5';
                    viewportMeta.setAttribute('content', content);
                }
            }
        }
        
        // 優化字體大小
        optimizeFontSizes() {
            if (this.isMobile) {
                // 移動端使用系統字體以提高性能
                document.body.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                
                // 優化基礎字體大小
                const baseFontSize = window.innerWidth < 768 ? '14px' : '16px';
                document.documentElement.style.fontSize = baseFontSize;
            }
        }
        
        // 優化圖片
        optimizeImages() {
            // 懶加載圖片
            const lazyImages = document.querySelectorAll('img[data-src]');
            if (lazyImages.length > 0 && 'IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            imageObserver.unobserve(img);
                        }
                    });
                });
                
                lazyImages.forEach(img => imageObserver.observe(img));
            }
            
            // 響應式圖片支持
            const pictures = document.querySelectorAll('picture');
            pictures.forEach(picture => {
                const sources = picture.querySelectorAll('source');
                sources.forEach(source => {
                    if (this.isMobile && source.media && source.media.includes('max-width')) {
                        const img = picture.querySelector('img');
                        if (img && source.srcset) {
                            // 移動端使用合適的圖片
                            const src = source.srcset.split(' ')[0];
                            if (src) img.src = src;
                        }
                    }
                });
            });
        }
        
        // 優化表單
        optimizeForms() {
            // 優化輸入類型
            const numberInputs = document.querySelectorAll('input[type="number"]');
            numberInputs.forEach(input => {
                input.setAttribute('pattern', '[0-9]*');
                input.setAttribute('inputmode', 'numeric');
            });
            
            const telInputs = document.querySelectorAll('input[type="tel"]');
            telInputs.forEach(input => {
                input.setAttribute('inputmode', 'tel');
            });
            
            const emailInputs = document.querySelectorAll('input[type="email"]');
            emailInputs.forEach(input => {
                input.setAttribute('inputmode', 'email');
            });
            
            // 防止iOS自動縮放
            if (this.isIOS) {
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    input.addEventListener('focus', function() {
                        setTimeout(() => {
                            this.style.fontSize = '16px';
                        }, 100);
                    });
                });
            }
        }
        
        // 優化導航
        optimizeNavigation() {
            // 移動端漢堡菜單優化
            const navbarToggles = document.querySelectorAll('.navbar-toggler');
            navbarToggles.forEach(toggle => {
                toggle.addEventListener('click', function() {
                    const targetId = this.getAttribute('data-target') || this.getAttribute('aria-controls');
                    if (targetId) {
                        const target = document.querySelector(targetId);
                        if (target) {
                            target.classList.toggle('show');
                            
                            // 添加動畫效果
                            if (target.classList.contains('show')) {
                                target.style.maxHeight = target.scrollHeight + 'px';
                            } else {
                                target.style.maxHeight = '0';
                            }
                        }
                    }
                });
            });
            
            // 移動端下拉菜單優化
            if (this.isTouch) {
                const dropdowns = document.querySelectorAll('.dropdown');
                dropdowns.forEach(dropdown => {
                    dropdown.addEventListener('click', function(e) {
                        if (!this.classList.contains('show')) {
                            e.preventDefault();
                            e.stopPropagation();
                            this.classList.add('show');
                            
                            // 點擊外部關閉
                            const closeHandler = (event) => {
                                if (!dropdown.contains(event.target)) {
                                    dropdown.classList.remove('show');
                                    document.removeEventListener('click', closeHandler);
                                }
                            };
                            
                            setTimeout(() => {
                                document.addEventListener('click', closeHandler);
                            }, 0);
                        }
                    });
                });
            }
        }
        
        // 防止雙擊縮放
        preventDoubleTapZoom() {
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(event) {
                const now = Date.now();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, { passive: false });
        }
        
        // 優化觸摸反饋
        optimizeTouchFeedback() {
            const touchElements = document.querySelectorAll('.btn, .nav-link, .dropdown-item, .list-group-item');
            touchElements.forEach(element => {
                // 添加觸摸反饋
                element.addEventListener('touchstart', function() {
                    this.classList.add('touch-active');
                });
                
                element.addEventListener('touchend', function() {
                    this.classList.remove('touch-active');
                });
                
                // 防止觸摸高亮
                element.style.webkitTapHighlightColor = 'transparent';
            });
        }
        
        // 優化滾動
        optimizeScrolling() {
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
        }
        
        // 優化長按
        optimizeLongPress() {
            let pressTimer;
            
            document.addEventListener('touchstart', function(e) {
                const target = e.target;
                if (target.classList.contains('long-press')) {
                    pressTimer = setTimeout(() => {
                        target.dispatchEvent(new Event('longpress'));
                    }, 500);
                }
            });
            
            document.addEventListener('touchend', function(e) {
                clearTimeout(pressTimer);
            });
            
            document.addEventListener('touchmove', function(e) {
                clearTimeout(pressTimer);
            });
        }
        
        // 懶加載資源
        lazyLoadResources() {
            // 懶加載iframe
            const lazyIframes = document.querySelectorAll('iframe[data-src]');
            if (lazyIframes.length > 0 && 'IntersectionObserver' in window) {
                const iframeObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const iframe = entry.target;
                            iframe.src = iframe.dataset.src;
                            iframe.removeAttribute('data-src');
                            iframeObserver.unobserve(iframe);
                        }
                    });
                });
                
                lazyIframes.forEach(iframe => iframeObserver.observe(iframe));
            }
        }
        
        // 優化動畫性能
        optimizeAnimationPerformance() {
            // 添加will-change屬性
            const animatedElements = document.querySelectorAll('.animated, .fade-in, .slide-in');
            animatedElements.forEach(element => {
                element.style.willChange = 'transform, opacity';
            });
            
            // 支持減少動畫
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.scrollBehavior = 'auto';
                
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    el.style.animationDuration = '0.01ms';
                    el.style.animationIterationCount = '1';
                    el.style.transitionDuration = '0.01ms';
                });
            }
        }
        
        // 減少重繪
        reduceRepaints() {
            let resizeTimeout;
            window.addEventListener('resize', () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    document.body.classList.add('resize-active');
                    setTimeout(() => {
                        document.body.classList.remove('resize-active');
                    }, 100);
                }, 250);
            });
        }
        
        // 優化網絡請求
        optimizeNetworkRequests() {
            // 預加載關鍵資源
            if ('connection' in navigator && navigator.connection.saveData === false) {
                const criticalResources = [
                    // 添加關鍵資源URL
                ];
                
                criticalResources.forEach(url => {
                    const link = document.createElement('link');
                    link.rel = 'preload';
                    link.href = url;
                    link.as = 'script';
                    document.head.appendChild(link);
                });
            }
        }
        
        // 增加觸摸目標尺寸
        increaseTouchTargets() {
            const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, label');
            interactiveElements.forEach(element => {
                const rect = element.getBoundingClientRect();
                if (rect.width < 44 || rect.height < 44) {
                    element.classList.add('touch-target-small');
                    
                    // 增加最小尺寸
                    element.style.minHeight = '44px';
                    element.style.minWidth = '44px';
                }
            });
        }
        
        // 優化焦點管理
        optimizeFocusManagement() {
            // 確保焦點可見
            document.addEventListener('focusin', function(e) {
                e.target.classList.add('focused');
            });
            
            document.addEventListener('focusout', function(e) {
                e.target.classList.remove('focused');
            });
            
            // 移動端虛擬鍵盤處理
            if (this.isMobile) {
                const inputs = document.querySelectorAll('input, textarea');
                inputs.forEach(input => {
                    input.addEventListener('focus', function() {
                        setTimeout(() => {
                            this.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }, 300);
                    });
                });
            }
        }
        
        // 支持減少動畫
        supportReducedMotion() {
            const motionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            
            const updateMotionPreference = (prefersReduced) => {
                if (prefersReduced) {
                    document.documentElement.classList.add('reduced-motion');
                } else {
                    document.documentElement.classList.remove('reduced-motion');
                }
            };
            
            // 初始設置
            updateMotionPreference(motionMediaQuery.matches);
            
            // 監聽變化
            motionMediaQuery.addEventListener('change', (e) => {
                updateMotionPreference(e.matches);
            });
        }
        
        // 支持高對比度
        supportHighContrast() {
            const contrastMediaQuery = window.matchMedia('(prefers-contrast: high)');
            
            const updateContrastPreference = (prefersHighContrast) => {
                if (prefersHighContrast) {
                    document.documentElement.classList.add('high-contrast');
                } else {
                    document.documentElement.classList.remove('high-contrast');
                }
            };
            
            // 初始設置
            updateContrastPreference(contrastMediaQuery.matches);
            
            // 監聽變化
            contrastMediaQuery.addEventListener('change', (e) => {
                updateContrastPreference(e.matches);
            });
        }
        
        // ========== 工具方法 ==========
        
        // 顯示移動端提示
        showMobileToast(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `mobile-toast toast-${type}`;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: ${this.getToastColor(type)};
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                z-index: 9999;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                max-width: 90%;
                text-align: center;
                animation: mobileToastSlideUp 0.3s ease;
            `;
            
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // 添加動畫樣式
            this.addToastStyles();
            
            // 定時消失
            setTimeout(() => {
                toast.style.animation = 'mobileToastSlideDown 0.3s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, duration);
            
            return toast;
        }
        
        // 獲取提示顏色
        getToastColor(type) {
            const colors = {
                info: '#007bff',
                success: '#28a745',
                warning: '#ffc107',
                error: '#dc3545'
            };
            return colors[type] || colors.info;
        }
        
        // 添加提示樣式
        addToastStyles() {
            if (!document.querySelector('#mobile-toast-styles')) {
                const style = document.createElement('style');
                style.id = 'mobile-toast-styles';
                style.textContent = `
                    @keyframes mobileToastSlideUp {
                        from { transform: translateX(-50%) translateY(100px); opacity: 0; }
                        to { transform: translateX(-50%) translateY(0); opacity: 1; }
                    }
                    @keyframes mobileToastSlideDown {
                        from { transform: translateX(-50%) translateY(0); opacity: 1; }
                        to { transform: translateX(-50%) translateY(100px); opacity: 0; }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // 振動反饋
        vibrate(pattern = [50]) {
            if ('vibrate' in navigator && this.isMobile) {
                try {
                    navigator.vibrate(pattern);
                } catch (e) {
                    if (CONFIG.debugMode) console.log('振動功能不可用:', e.message);
                }
            }
        }
        
        // 網絡狀態檢測
        initNetworkStatus() {
            if ('onLine' in navigator) {
                const updateStatus = () => {
                    if (!navigator.onLine) {
                        this.showMobileToast('⚠️ 網絡連接已斷開', 'error');
                    } else {
                        this.showMobileToast('✅ 網絡連接已恢復', 'success');
                    }
                };
                
                // 初始檢測
                updateStatus();
                
                // 監聽變化
                window.addEventListener('online', updateStatus);
                window.addEventListener('offline', updateStatus);
            }
        }
        
        // 深色模式支持
        initDarkMode() {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            const updateDarkMode = (isDark) => {
                if (isDark) {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    document.body.classList.add('dark-mode');
                } else {
                    document.documentElement.setAttribute('data-theme', 'light');
                    document.body.classList.remove('dark-mode');
                }
            };
            
            // 初始設置
            updateDarkMode(darkModeQuery.matches);
            
            // 監聽變化
            darkModeQuery.addEventListener('change', (e) => {
                updateDarkMode(e.matches);
            });
        }
        
        // 頁面加載優化
        optimizePageLoad() {
            // 添加加載動畫
            if (!document.querySelector('#mobile-page-loader')) {
                const loader = document.createElement('div');
                loader.id = 'mobile-page-loader';
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
                
                // 頁面加載完成後隱藏
                window.addEventListener('load', () => {
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
        }
        
        // 調試模式
        enableDebugMode() {
            if (CONFIG.debugMode) {
                console.log('🔧 啟用調試模式');
                console.log('設備信息:', {
                    type: this.deviceType,
                    isMobile: this.isMobile,
                    isTouch: this.isTouch,
                    userAgent: navigator.userAgent,
                    screen: `${window.innerWidth}x${window.innerHeight}`,
                    pixelRatio: window.devicePixelRatio
                });
            }
        }
    }
    
    // ========== 初始化 ==========
    
    // 創建優化管理器實例
    const mobileManager = new MobileOptimizationManager();
    
    // 頁面加載完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            mobileManager.init();
        });
    } else {
        // 如果文檔已經加載完成，直接初始化
        setTimeout(() => {
            mobileManager.init();
        }, 100);
    }
    
    // 導出管理器（可選）
    window.MobileOptimizationManager = mobileManager;
    
    console.log('📱 移動端優化增強腳本準備完成');
})();
