/**
 * Between Coffee 圖片懶加載模塊
 * 版本: 1.0.0
 * 創建日期: 2026年2月23日
 * 功能: 圖片懶加載、WebP支持檢測、骨架屏效果
 */

(function() {
    'use strict';
    
    // 配置
    const CONFIG = {
        // 懶加載配置
        lazyLoad: {
            rootMargin: '50px 0px',
            threshold: 0.01,
            maxRetries: 3,
            retryDelay: 1000
        },
        
        // WebP檢測配置
        webp: {
            testImage: 'data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==',
            timeout: 3000
        },
        
        // 骨架屏配置
        skeleton: {
            backgroundColor: '#f0f0f0',
            animationDuration: '1.5s',
            animationTiming: 'ease-in-out'
        }
    };
    
    // 全局狀態
    const STATE = {
        webpSupported: null,
        observer: null,
        lazyImages: [],
        initialized: false
    };
    
    /**
     * 檢測瀏覽器是否支持WebP格式
     * @returns {Promise<boolean>} 是否支持WebP
     */
    function detectWebPSupport() {
        return new Promise((resolve) => {
            // 如果已經檢測過，直接返回結果
            if (STATE.webpSupported !== null) {
                resolve(STATE.webpSupported);
                return;
            }
            
            const img = new Image();
            let timeoutId;
            
            img.onload = img.onerror = function() {
                clearTimeout(timeoutId);
                STATE.webpSupported = (img.width === 1 && img.height === 1);
                resolve(STATE.webpSupported);
            };
            
            timeoutId = setTimeout(() => {
                STATE.webpSupported = false;
                resolve(false);
            }, CONFIG.webp.timeout);
            
            img.src = CONFIG.webp.testImage;
        });
    }
    
    /**
     * 創建骨架屏元素
     * @param {HTMLElement} imgElement - 圖片元素
     * @returns {HTMLElement} 骨架屏容器
     */
    function createSkeleton(imgElement) {
        const container = document.createElement('div');
        container.className = 'lazy-skeleton';
        
        // 複製原始圖片的尺寸和位置
        const rect = imgElement.getBoundingClientRect();
        container.style.width = rect.width > 0 ? `${rect.width}px` : '100%';
        container.style.height = rect.height > 0 ? `${rect.height}px` : '200px';
        container.style.backgroundColor = CONFIG.skeleton.backgroundColor;
        container.style.position = 'relative';
        container.style.overflow = 'hidden';
        container.style.borderRadius = '4px';
        
        // 添加動畫效果
        const shimmer = document.createElement('div');
        shimmer.style.position = 'absolute';
        shimmer.style.top = '0';
        shimmer.style.left = '-100%';
        shimmer.style.width = '100%';
        shimmer.style.height = '100%';
        shimmer.style.background = 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)';
        shimmer.style.animation = `shimmer ${CONFIG.skeleton.animationDuration} ${CONFIG.skeleton.animationTiming} infinite`;
        
        container.appendChild(shimmer);
        
        // 添加CSS動畫
        if (!document.querySelector('#lazy-load-styles')) {
            const style = document.createElement('style');
            style.id = 'lazy-load-styles';
            style.textContent = `
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(200%); }
                }
                
                .lazy-skeleton {
                    display: inline-block;
                    vertical-align: middle;
                }
                
                .lazy-loaded {
                    animation: fadeIn 0.5s ease-in-out;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                picture.lazy-loading img,
                img.lazy-loading {
                    opacity: 0;
                    transition: opacity 0.3s ease-in-out;
                }
                
                picture.lazy-loaded img,
                img.lazy-loaded {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }
        
        return container;
    }
    
    /**
     * 加載圖片
     * @param {HTMLElement} imgElement - 圖片元素
     * @param {number} retryCount - 重試次數
     * @returns {Promise<void>}
     */
    function loadImage(imgElement, retryCount = 0) {
        return new Promise((resolve, reject) => {
            // 如果圖片已經加載，直接返回
            if (imgElement.complete && imgElement.naturalWidth > 0) {
                resolve();
                return;
            }
            
            // 設置加載狀態
            imgElement.classList.add('lazy-loading');
            
            const onLoad = () => {
                cleanup();
                imgElement.classList.remove('lazy-loading');
                imgElement.classList.add('lazy-loaded');
                resolve();
            };
            
            const onError = () => {
                cleanup();
                
                // 重試邏輯
                if (retryCount < CONFIG.lazyLoad.maxRetries) {
                    setTimeout(() => {
                        loadImage(imgElement, retryCount + 1)
                            .then(resolve)
                            .catch(reject);
                    }, CONFIG.lazyLoad.retryDelay);
                } else {
                    imgElement.classList.remove('lazy-loading');
                    reject(new Error(`Failed to load image after ${CONFIG.lazyLoad.maxRetries} retries`));
                }
            };
            
            const cleanup = () => {
                imgElement.removeEventListener('load', onLoad);
                imgElement.removeEventListener('error', onError);
            };
            
            imgElement.addEventListener('load', onLoad);
            imgElement.addEventListener('error', onError);
            
            // 如果圖片已經有src，觸發加載
            if (imgElement.src && imgElement.src !== window.location.href) {
                imgElement.src = imgElement.src; // 觸發加載
            }
        });
    }
    
    /**
     * 處理單個懶加載圖片
     * @param {HTMLElement} element - 圖片或picture元素
     */
    function processLazyElement(element) {
        // 檢查是否已經處理過
        if (element.dataset.lazyProcessed === 'true') {
            return;
        }
        
        element.dataset.lazyProcessed = 'true';
        
        // 保存原始數據
        const originalSrc = element.getAttribute('src');
        const dataSrc = element.getAttribute('data-src');
        const dataSrcset = element.getAttribute('data-srcset');
        const dataWebp = element.getAttribute('data-webp');
        
        if (!dataSrc && !dataSrcset && !dataWebp) {
            return; // 沒有懶加載數據
        }
        
        // 創建骨架屏
        const skeleton = createSkeleton(element);
        element.parentNode.insertBefore(skeleton, element);
        element.style.display = 'none';
        
        // 觀察元素進入視口
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    observer.unobserve(element);
                    loadLazyElement(element, skeleton);
                }
            });
        }, CONFIG.lazyLoad);
        
        observer.observe(element);
    }
    
    /**
     * 加載懶加載元素
     * @param {HTMLElement} element - 圖片或picture元素
     * @param {HTMLElement} skeleton - 骨架屏元素
     */
    async function loadLazyElement(element, skeleton) {
        try {
            // 檢測WebP支持
            const webpSupported = await detectWebPSupport();
            
            // 處理圖片源
            if (element.tagName === 'PICTURE') {
                // 處理picture元素
                await processPictureElement(element, webpSupported);
            } else {
                // 處理普通img元素
                await processImgElement(element, webpSupported);
            }
            
            // 加載圖片
            await loadImage(element.tagName === 'PICTURE' ? element.querySelector('img') : element);
            
            // 移除骨架屏，顯示圖片
            if (skeleton && skeleton.parentNode) {
                skeleton.parentNode.removeChild(skeleton);
            }
            
            element.style.display = '';
            
            // 觸發加載完成事件
            element.dispatchEvent(new CustomEvent('lazyloaded', {
                bubbles: true,
                detail: { element }
            }));
            
        } catch (error) {
            console.error('Failed to load lazy element:', error);
            
            // 加載失敗時顯示錯誤圖標
            element.style.display = '';
            element.classList.add('lazy-error');
            
            if (skeleton && skeleton.parentNode) {
                skeleton.parentNode.removeChild(skeleton);
            }
        }
    }
    
    /**
     * 處理picture元素
     * @param {HTMLPictureElement} pictureElement - picture元素
     * @param {boolean} webpSupported - 是否支持WebP
     */
    async function processPictureElement(pictureElement, webpSupported) {
        const sources = pictureElement.querySelectorAll('source');
        const img = pictureElement.querySelector('img');
        
        if (!img) return;
        
        // 處理source元素
        sources.forEach(source => {
            const dataSrcset = source.getAttribute('data-srcset');
            if (dataSrcset) {
                source.srcset = dataSrcset;
                source.removeAttribute('data-srcset');
            }
            
            // 如果是WebP source且瀏覽器不支持WebP，移除它
            if (source.type === 'image/webp' && !webpSupported) {
                source.parentNode.removeChild(source);
            }
        });
        
        // 處理img元素
        const dataSrc = img.getAttribute('data-src');
        const dataSrcset = img.getAttribute('data-srcset');
        
        if (dataSrc) {
            img.src = dataSrc;
            img.removeAttribute('data-src');
        }
        
        if (dataSrcset) {
            img.srcset = dataSrcset;
            img.removeAttribute('data-srcset');
        }
    }
    
    /**
     * 處理img元素
     * @param {HTMLImageElement} imgElement - img元素
     * @param {boolean} webpSupported - 是否支持WebP
     */
    async function processImgElement(imgElement, webpSupported) {
        const dataSrc = imgElement.getAttribute('data-src');
        const dataSrcset = imgElement.getAttribute('data-srcset');
        const dataWebp = imgElement.getAttribute('data-webp');
        
        // 優先使用WebP（如果支持）
        if (webpSupported && dataWebp) {
            imgElement.src = dataWebp;
            imgElement.removeAttribute('data-webp');
        } else if (dataSrc) {
            imgElement.src = dataSrc;
            imgElement.removeAttribute('data-src');
        }
        
        if (dataSrcset) {
            imgElement.srcset = dataSrcset;
            imgElement.removeAttribute('data-srcset');
        }
    }
    
    /**
     * 初始化懶加載
     */
    function init() {
        if (STATE.initialized) {
            return;
        }
        
        STATE.initialized = true;
        
        // 查找所有需要懶加載的元素
        const lazyElements = document.querySelectorAll(
            'img[data-src], img[data-srcset], img[data-webp], ' +
            'picture source[data-srcset], picture img[data-src]'
        );
        
        // 將picture元素的img子元素添加到列表
        const pictureImgs = document.querySelectorAll('picture img[data-src]');
        const pictures = document.querySelectorAll('picture source[data-srcset]');
        
        // 合併所有元素
        const allElements = new Set([...lazyElements]);
        pictureImgs.forEach(img => allElements.add(img.closest('picture') || img));
        pictures.forEach(source => allElements.add(source.closest('picture') || source));
        
        // 處理每個元素
        allElements.forEach(element => {
            if (element) {
                processLazyElement(element);
            }
        });
        
        // 監聽DOM變化，處理動態添加的元素
        if (window.MutationObserver) {
            const mutationObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // 檢查新增的元素
                            const lazyImgs = node.querySelectorAll?.(
                                'img[data-src], img[data-srcset], img[data-webp], ' +
                                'picture source[data-srcset], picture img[data-src]'
                            ) || [];
                            
                            lazyImgs.forEach(img => {
                                const picture = img.closest('picture');
                                processLazyElement(picture || img);
                            });
                            
                            // 檢查元素本身
                            if (node.matches?.('img[data-src], img[data-srcset], img[data-webp]') ||
                                node.matches?.('picture source[data-srcset]') ||
                                (node.matches?.('picture') && node.querySelector('img[data-src]'))) {
                                processLazyElement(node);
                            }
                        }
                    });
                });
            });
            
            mutationObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        console.log(`LazyLoad initialized: ${allElements.size} elements found`);
    }
    
    /**
     * 手動觸發圖片加載
     * @param {HTMLElement} element - 要加載的元素
     */
    function load(element) {
        if (!element) {
            console.error('No element provided to load');
            return;
        }
        
        const skeleton = element.previousElementSibling?.classList?.contains('lazy-skeleton') 
            ? element.previousElementSibling 
            : null;
        
        loadLazyElement(element, skeleton);
    }
    
    /**
     * 加載所有可見圖片
     */
    function loadAllVisible() {
        const lazyElements = document.querySelectorAll(
            'img[data-src], img[data-srcset], img[data-webp], ' +
            'picture source[data-srcset], picture img[data-src]'
        );
        
        lazyElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const isVisible = (
                rect.top <= window.innerHeight &&
                rect.bottom >= 0 &&
                rect.left <= window.innerWidth &&
                rect.right >= 0
            );
            
            if (isVisible && element.dataset.lazyProcessed !== 'true') {
                processLazyElement(element);
            }
        });
    }
    
    /**
     * 檢查WebP支持
     * @returns {Promise<boolean>} 是否支持WebP
     */
    function checkWebPSupport() {
        return detectWebPSupport();
    }
    
    // 導出API
    window.LazyLoad = {
        init,
        load,
        loadAllVisible,
        checkWebPSupport,
        config: CONFIG
    };
    
    // 自動初始化（當DOM加載完成時）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 100); // 延遲初始化，確保所有元素都已渲染
    }
    
})();