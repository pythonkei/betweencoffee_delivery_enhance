// static/js/staff-order-management/time-utils.js
// ==================== 统一的香港时间工具 ====================
class TimeUtils {
    static formatHKTime(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            // 转换为香港时区
            const hkTime = date.toLocaleString('zh-HK', {
                timeZone: 'Asia/Hong_Kong',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            return hkTime;
        } catch (error) {
            console.error('格式化香港时间错误:', error);
            return dateString;
        }
    }
    
    static formatHKTimeOnly(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            return date.toLocaleTimeString('zh-HK', {
                timeZone: 'Asia/Hong_Kong',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.error('格式化香港时间错误:', error);
            return dateString;
        }
    }
    
    static formatRelativeTime(dateString) {
        if (!dateString) return '刚刚';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return '刚刚';
            
            const now = new Date();
            const diffMs = now - date;
            const diffMinutes = Math.floor(diffMs / (1000 * 60));
            
            if (diffMinutes < 1) return '刚刚';
            if (diffMinutes < 60) return `${diffMinutes}分钟前`;
            
            const hours = Math.floor(diffMinutes / 60);
            if (hours < 24) return `${hours}小时前`;
            
            const days = Math.floor(hours / 24);
            return `${days}天前`;
        } catch (error) {
            return '刚刚';
        }
    }
    // 新增：格式化完成时间为中文格式（下午xx:xx:xx）
    static formatCompletedTime(dateString = null) {
        let date;
        
        if (dateString) {
            date = new Date(dateString);
        } else {
            date = new Date(); // 使用当前时间
        }
        
        if (isNaN(date.getTime())) {
            console.error('时间格式错误:', dateString);
            return '时间错误';
        }
        
        try {
            // 转换为香港时区
            const hkTime = date.toLocaleString('zh-HK', {
                timeZone: 'Asia/Hong_Kong',
                hour12: true, // 使用12小时制（上午/下午）
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            
            // 格式化为"下午xx:xx:xx"
            return hkTime;
        } catch (error) {
            console.error('格式化完成时间错误:', error);
            return date.toLocaleTimeString('zh-HK');
        }
    }
    
    // 新增：获取当前香港时间的完成时间格式
    static getCurrentCompletedTime() {
        return this.formatCompletedTime();
    }
    
    // 新增：格式化预计完成时间为中文格式（使用订单的预计完成时间）
    static formatEstimatedCompletionTime(estimatedTimeStr) {
        if (!estimatedTimeStr) return '時間未設定';
        
        try {
            const estimatedTime = new Date(estimatedTimeStr);
            if (isNaN(estimatedTime.getTime())) {
                console.error('預計完成時間格式錯誤:', estimatedTimeStr);
                return '時間錯誤';
            }
            
            // 轉換為香港時區並格式為"下午xx:xx:xx"
            return estimatedTime.toLocaleTimeString('zh-HK', {
                timeZone: 'Asia/Hong_Kong',
                hour12: true, // 上午/下午
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            console.error('格式化預計完成時間錯誤:', error);
            return '時間錯誤';
        }
    }
    
    // 新增：獲取倒計時完成的顯示文本
    static getCountdownCompletedText(estimatedTimeStr) {
        const formattedTime = this.formatEstimatedCompletionTime(estimatedTimeStr);
        return `已完成: ${formattedTime}`;
    }
}

// 暴露到全局
if (typeof window !== 'undefined') {
    window.TimeUtils = TimeUtils;
}