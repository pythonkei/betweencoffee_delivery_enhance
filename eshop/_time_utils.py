# eshop/time_utils.py
"""
时间工具模块 - 简化版本，只保留必要函数
已将所有复杂时间计算迁移到 time_service.py
"""
import warnings
import logging

logger = logging.getLogger(__name__)

# 从统一时间服务导入函数
try:
    from .time_service import time_service
except ImportError:
    logger.error("无法导入 time_service，使用备用实现")
    
    # 备用实现（只在 time_service 不可用时使用）
    import pytz
    from django.utils import timezone
    
    def get_hong_kong_time():
        warnings.warn("使用备用时间实现，请确保 time_service.py 存在")
        return timezone.now().astimezone(pytz.timezone('Asia/Hong_Kong'))
    
    # 创建临时的 time_service 对象
    class BackupTimeService:
        @staticmethod
        def get_hong_kong_time():
            return get_hong_kong_time()
    
    time_service = BackupTimeService()

# ==================== 代理函数（保持原有接口） ====================

def get_hong_kong_time():
    """获取香港时区当前时间 - 代理到统一时间服务"""
    try:
        return time_service.get_hong_kong_time()
    except Exception as e:
        logger.error(f"获取香港时间失败: {str(e)}")
        # 备用实现
        import pytz
        from django.utils import timezone
        return timezone.now().astimezone(pytz.timezone('Asia/Hong_Kong'))

def format_time_for_display(dt):
    """统一格式化时间为香港时区显示 - 代理到统一时间服务"""
    try:
        return time_service.format_time_for_display(dt)
    except Exception as e:
        logger.error(f"格式化时间失败: {str(e)}")
        if not dt:
            return None
        try:
            import pytz
            hk_time = dt.astimezone(pytz.timezone('Asia/Hong_Kong'))
            return hk_time.strftime('%H:%M')
        except:
            return "--:--"

def is_time_ready(target_time):
    """检查目标时间是否已到达（香港时区）- 代理到统一时间服务"""
    try:
        return time_service.is_time_ready(target_time)
    except Exception as e:
        logger.error(f"检查时间就绪失败: {str(e)}")
        return True

def get_remaining_minutes(target_time):
    """获取剩余分钟数（香港时区）- 代理到统一时间服务"""
    try:
        return time_service.get_remaining_minutes(target_time)
    except Exception as e:
        logger.error(f"获取剩余分钟数失败: {str(e)}")
        return 0

def calculate_remaining_time(target_time):
    """计算剩余时间（秒）- 代理到统一时间服务"""
    try:
        return time_service.calculate_remaining_time(target_time)
    except Exception as e:
        logger.error(f"计算剩余时间失败: {str(e)}")
        return 0

def format_remaining_time(seconds):
    """格式化剩余时间显示 - 代理到统一时间服务"""
    try:
        return time_service.format_remaining_time(seconds)
    except Exception as e:
        logger.error(f"格式化剩余时间失败: {str(e)}")
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds_remaining = seconds % 60
            if seconds_remaining > 0:
                return f"{minutes}分{seconds_remaining}秒"
            return f"{minutes}分钟"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"

def calculate_progress_percentage(order):
    """计算订单制作进度百分比 - 代理到统一时间服务"""
    try:
        return time_service.calculate_progress_percentage(order)
    except Exception as e:
        logger.error(f"计算进度百分比失败: {str(e)}")
        return 0

# ==================== 快速订单相关函数（代理） ====================

def get_pickup_time_display_from_choice(pickup_time_choice):
    """統一處理取貨時間選擇的顯示 - 代理到统一时间服务"""
    try:
        return time_service._get_pickup_time_display_from_choice(pickup_time_choice)
    except Exception as e:
        logger.error(f"获取取货时间显示失败: {str(e)}")
        choice_map = {
            '5': '5分鐘後',
            '10': '10分鐘後',
            '15': '15分鐘後',
            '20': '20分鐘後',
            '30': '30分鐘後',
        }
        return choice_map.get(str(pickup_time_choice).strip(), '5分鐘後')

def get_minutes_from_pickup_choice(pickup_time_choice):
    """從取貨時間選擇中提取分鐘數 - 代理到统一时间服务"""
    try:
        return time_service._get_minutes_from_pickup_choice(pickup_time_choice)
    except Exception as e:
        logger.error(f"从取货时间选择提取分钟数失败: {str(e)}")
        return 5

def calculate_pickup_time_for_quick_order(order):
    """為快速訂單計算取貨時間相關信息 - 代理到统一时间服务"""
    try:
        return time_service.calculate_quick_order_pickup_time(order)
    except Exception as e:
        logger.error(f"计算快速订单取货时间失败: {str(e)}")
        return None

# 修改 format_pickup_time_for_order 函数
def format_pickup_time_for_order(order):
    """
    為訂單統一格式化取貨時間信息
    
    參數:
        order (OrderModel): 訂單實例
    
    返回:
        dict: 格式化的取貨時間信息
    """
    if not order:
        return None
    
    try:
        # 获取订单项目
        items = order.get_items()
        
        # 檢查是否純咖啡豆訂單（直接检查项目，不调用方法）
        has_beans = any(item.get('type') == 'bean' for item in items)
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        is_beans_only = has_beans and not has_coffee
        
        # 純咖啡豆訂單
        if is_beans_only:
            return {
                'text': '隨時可取',
                'css_class': 'text-success',
                'icon': 'fa-clock',
                'is_immediate': True,
                'display_type': 'beans_only'
            }
        
        # 快速訂單
        if order.is_quick_order:
            quick_order_info = calculate_pickup_time_for_quick_order(order)
            if quick_order_info:
                return {
                    'text': quick_order_info['pickup_time_display'],
                    'css_class': 'text-success',
                    'icon': 'fa-clock',
                    'estimated_time': quick_order_info['estimated_pickup_display'],
                    'remaining_minutes': quick_order_info['remaining_minutes'],
                    'remaining_display': quick_order_info['remaining_display'],
                    'is_immediate': False,
                    'display_type': 'quick_order',
                    'raw_info': quick_order_info
                }
        
        # 普通咖啡訂單
        if has_coffee:
            return {
                'text': '製作中，請稍候',
                'css_class': 'text-info',
                'icon': 'fa-coffee',
                'is_immediate': False,
                'display_type': 'coffee_order'
            }
        
        # 默認情況
        return {
            'text': '處理中',
            'css_class': 'text-secondary',
            'icon': 'fa-hourglass-half',
            'is_immediate': False,
            'display_type': 'default'
        }
        
    except Exception as e:
        logger.error(f"格式化訂單取貨時間失敗: {str(e)}")
        # 返回默認值
        return {
            'text': '處理中',
            'css_class': 'text-secondary',
            'icon': 'fa-hourglass-half',
            'is_immediate': False,
            'display_type': 'default'
        }

def calculate_all_quick_order_times():
    """計算所有快速訂單的時間信息 - 代理到统一时间服务"""
    try:
        return time_service.calculate_all_quick_order_times()
    except Exception as e:
        logger.error(f"批量計算快速訂單時間失敗: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'results': {}
        }

def update_order_pickup_times(order_ids):
    """更新指定訂單的取貨時間信息 - 代理到统一时间服务"""
    try:
        return time_service.update_order_pickup_times(order_ids)
    except Exception as e:
        logger.error(f"批量更新訂單取貨時間失敗: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }