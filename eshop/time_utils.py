# eshop/time_utils.py
from django.utils import timezone
import pytz


def get_hong_kong_time():
    """获取香港时区当前时间"""
    return timezone.now().astimezone(pytz.timezone('Asia/Hong_Kong'))


def format_time_for_display(dt):
    """统一格式化时间为香港时区显示"""
    if not dt:
        return None
    hk_time = dt.astimezone(pytz.timezone('Asia/Hong_Kong'))
    return hk_time.strftime('%H:%M')


def is_time_ready(target_time):
    """检查目标时间是否已到达（香港时区）"""
    if not target_time:
        return True
    current_hk = get_hong_kong_time()
    target_hk = target_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
    return current_hk >= target_hk


def get_remaining_minutes(target_time):
    """获取剩余分钟数（香港时区）"""
    if not target_time:
        return 0
    
    current_hk = get_hong_kong_time()
    target_hk = target_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
    
    if current_hk >= target_hk:
        return 0
    
    diff = target_hk - current_hk
    return max(0, int(diff.total_seconds() / 60) + 1)  # 向上取整