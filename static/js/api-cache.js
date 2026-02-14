// static/js/api-cache.js
class ApiCache {
    constructor(options = {}) {
        this.cache = new Map();
        this.defaultMaxAge = options.maxAge || 15000; // 15秒
        this.maxCacheSize = options.maxSize || 100; // 最大緩存條目
    }
    
    async fetchWithCache(url, options = {}) {
        const cacheKey = this.generateCacheKey(url, options);
        const now = Date.now();
        
        // 檢查緩存
        const cached = this.cache.get(cacheKey);
        if (cached && (now - cached.timestamp) < cached.maxAge) {
            console.log('[API Cache] 使用緩存:', url);
            return cached.data;
        }
        
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態碼: ${response.status}`);
            }
            
            const data = await response.json();
            
            // 存入緩存
            this.set(cacheKey, data, options.maxAge);
            
            console.log('[API Cache] 從API獲取並緩存:', url);
            return data;
            
        } catch (error) {
            // 如果API失敗但有緩存數據，返回緩存數據
            if (cached) {
                console.log('[API Cache] API失敗，使用過期緩存:', url);
                return cached.data;
            }
            throw error;
        }
    }
    
    set(key, data, maxAge = this.defaultMaxAge) {
        // 清理過期緩存
        this.cleanup();
        
        // 限制緩存大小
        if (this.cache.size >= this.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        
        this.cache.set(key, {
            data: data,
            timestamp: Date.now(),
            maxAge: maxAge
        });
    }
    
    get(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        if (Date.now() - cached.timestamp > cached.maxAge) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.data;
    }
    
    delete(key) {
        this.cache.delete(key);
    }
    
    clear() {
        this.cache.clear();
    }
    
    cleanup() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > value.maxAge) {
                this.cache.delete(key);
            }
        }
    }
    
    generateCacheKey(url, options) {
        const { method = 'GET', body, headers } = options;
        const keyParts = [
            url,
            method,
            body ? JSON.stringify(body) : '',
            headers ? JSON.stringify(headers) : ''
        ];
        return keyParts.join('|');
    }
    
    getStats() {
        return {
            size: this.cache.size,
            maxSize: this.maxCacheSize,
            hitRate: this.calculateHitRate()
        };
    }
    
    calculateHitRate() {
        // 簡單的命中率計算
        const total = this.hits + this.misses;
        return total > 0 ? (this.hits / total) * 100 : 0;
    }
}

// 全局 API 緩存實例
window.apiCache = new ApiCache();