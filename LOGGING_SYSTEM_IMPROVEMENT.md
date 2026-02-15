# 日誌系統改進指南

## 概述
本文檔說明如何改進咖啡店外帶網站的日誌系統。良好的日誌系統有助於問題排查、性能監控和系統維護。

## 當前日誌系統分析

### 現有問題
1. **日誌分散**：不同模塊使用不同的日誌格式
2. **信息不全**：缺少關鍵上下文信息（如請求ID、用戶ID）
3. **級別混亂**：日誌級別使用不一致
4. **難以查詢**：日誌文件分散，難以集中查看

## 改進方案

### 1. 統一日誌配置

#### Django 日誌配置
```python
# settings.py 中添加

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s", "request_id": "%(request_id)s", "user_id": "%(user_id)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'request_context': {
            '()': 'betweencoffee_delivery.logging.RequestContextFilter',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['request_context'],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'json_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/json.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
            'filters': ['request_context'],
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'eshop': {
            'handlers': ['console', 'file', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cart': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'websocket': {
            'handlers': ['console', 'file', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'payment': {
            'handlers': ['console', 'file', 'error_file', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'queue': {
            'handlers': ['console', 'file', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. 請求上下文過濾器

```python
# betweencoffee_delivery/logging.py
import logging
from threading import local
import uuid

_thread_locals = local()

class RequestContextFilter(logging.Filter):
    """
    日誌過濾器，添加請求上下文信息。
    """
    
    def filter(self, record):
        # 添加請求ID
        if hasattr(_thread_locals, 'request_id'):
            record.request_id = _thread_locals.request_id
        else:
            record.request_id = 'no-request'
        
        # 添加用戶ID
        if hasattr(_thread_locals, 'user_id'):
            record.user_id = _thread_locals.user_id
        else:
            record.user_id = 'anonymous'
        
        # 添加IP地址
        if hasattr(_thread_locals, 'ip_address'):
            record.ip_address = _thread_locals.ip_address
        else:
            record.ip_address = 'unknown'
        
        return True


def set_request_context(request_id=None, user_id=None, ip_address=None):
    """
    設置當前請求的上下文信息。
    """
    if request_id:
        _thread_locals.request_id = request_id
    if user_id:
        _thread_locals.user_id = user_id
    if ip_address:
        _thread_locals.ip_address = ip_address


def clear_request_context():
    """
    清除請求上下文信息。
    """
    if hasattr(_thread_locals, 'request_id'):
        delattr(_thread_locals, 'request_id')
    if hasattr(_thread_locals, 'user_id'):
        delattr(_thread_locals, 'user_id')
    if hasattr(_thread_locals, 'ip_address'):
        delattr(_thread_locals, 'ip_address')


class RequestIDMiddleware:
    """
    中間件：為每個請求生成唯一ID。
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 生成請求ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # 獲取用戶信息
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        ip_address = self.get_client_ip(request)
        
        # 設置日誌上下文
        set_request_context(request_id, user_id, ip_address)
        
        try:
            response = self.get_response(request)
            # 在響應頭中添加請求ID
            response['X-Request-ID'] = request_id
            return response
        finally:
            clear_request_context()
    
    def get_client_ip(self, request):
        """
        獲取客戶端IP地址。
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### 3. 統一日誌工具

```python
# eshop/logging_utils.py
"""
日誌工具模塊，提供統一的日誌接口。
"""
import logging
import json
from datetime import datetime
from functools import wraps

# 獲取日誌記錄器
def get_logger(name):
    """
    獲取日誌記錄器實例。
    
    Args:
        name (str): 日誌記錄器名稱，通常是模塊名
    
    Returns:
        Logger: 配置好的日誌記錄器
    """
    return logging.getLogger(name)


# 業務日誌記錄器
ORDER_LOGGER = get_logger('eshop.order')
PAYMENT_LOGGER = get_logger('eshop.payment')
QUEUE_LOGGER = get_logger('eshop.queue')
WEBSOCKET_LOGGER = get_logger('eshop.websocket')


def log_order_event(order_id, event_type, message, extra_data=None):
    """
    記錄訂單事件。
    
    Args:
        order_id (int): 訂單ID
        event_type (str): 事件類型（created, updated, completed, etc.）
        message (str): 事件描述
        extra_data (dict, optional): 額外數據
    """
    log_data = {
        'order_id': order_id,
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    ORDER_LOGGER.info(
        f"訂單事件: {event_type} - {message}",
        extra={'log_data': json.dumps(log_data)}
    )


def log_payment_event(order_id, payment_method, amount, status, extra_data=None):
    """
    記錄支付事件。
    
    Args:
        order_id (int): 訂單ID
        payment_method (str): 支付方式（alipay, paypal, fps, cash）
        amount (Decimal): 支付金額
        status (str): 支付狀態（success, failed, pending）
        extra_data (dict, optional): 額外數據
    """
    log_data = {
        'order_id': order_id,
        'payment_method': payment_method,
        'amount': str(amount),
        'status': status,
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    level = logging.INFO if status == 'success' else logging.ERROR
    
    PAYMENT_LOGGER.log(
        level,
        f"支付事件: {payment_method} - {status} - HK${amount}",
        extra={'log_data': json.dumps(log_data)}
    )


def log_queue_event(order_id, old_status, new_status, staff_id=None, extra_data=None):
    """
    記錄隊列事件（訂單狀態變化）。
    
    Args:
        order_id (int): 訂單ID
        old_status (str): 舊狀態
        new_status (str): 新狀態
        staff_id (int, optional): 員工ID
        extra_data (dict, optional): 額外數據
    """
    log_data = {
        'order_id': order_id,
        'old_status': old_status,
        'new_status': new_status,
        'staff_id': staff_id,
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    QUEUE_LOGGER.info(
        f"隊列事件: {order_id} - {old_status} -> {new_status}",
        extra={'log_data': json.dumps(log_data)}
    )


def log_websocket_event(event_type, channel_name, message, extra_data=None):
    """
    記錄 WebSocket 事件。
    
    Args:
        event_type (str): 事件類型（connect, disconnect, message, error）
        channel_name (str): 頻道名稱
        message (str): 消息內容
        extra_data (dict, optional): 額外數據
    """
    log_data = {
        'event_type': event_type,
        'channel_name': channel_name,
        'message': message[:100],  # 限制長度
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    level = logging.ERROR if event_type == 'error' else logging.INFO
    
    WEBSOCKET_LOGGER.log(
        level,
        f"WebSocket事件: {event_type} - {channel_name}",
        extra={'log_data': json.dumps(log_data)}
    )


def log_performance_metric(metric_name, value, unit='ms', extra_data=None):
    """
    記錄性能指標。
    
    Args:
        metric_name (str): 指標名稱
        value (float): 指標值
        unit (str): 單位（ms, s, count, etc.）
        extra_data (dict, optional): 額外數據
    """
    log_data = {
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    # 使用專用的性能日誌記錄器
    perf_logger = get_logger('performance')
    perf_logger.info(
        f"性能指標: {metric_name} = {value}{unit}",
        extra={'log_data': json.dumps(log_data)}
    )


def timed_logger(metric_name):
    """
    裝飾器：記錄函數執行時間。
    
    Args:
        metric_name (str): 指標名稱
    
    Returns:
        function: 裝飾器函數
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # 轉為毫秒
                
                log_performance_metric(
                    metric_name,
                    duration,
                    'ms',
                    {'function': func.__name__}
                )
        
        return wrapper
    return decorator


# 示例使用
class OrderService:
    """
    訂單服務示例，展示日誌使用。
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    @timed_logger('create_order')
    def create_order(self, order_data):
        """
        創建訂單。
        """
        try:
            self.logger.info(f"開始創建訂單: {order_data}")
            
            # 業務邏輯...
            order = self._save_order(order_data)
            
            # 記錄訂單創建事件
            log_order_event(
                order.id,
                'created',
                '訂單創建成功',
                {'order_data': order_data}
            )
            
            self.logger.info(f"訂單創建成功: {order.id}")
            return order
            
        except Exception as e:
            self.logger.error(f"創建訂單失敗: {str(e)}", exc_info=True)
            raise
    
    @timed_logger('update_order_status')
    def update_order_status(self, order_id, new_status, staff_member=None):
        """
        更新訂單狀態。
        """
        try:
            self.logger.info(f"開始更新訂單狀態: {order_id} -> {new_status}")
            
            # 獲取當前狀態
            order = self._get_order(order_id)
            old_status = order.status
            
            # 更新狀態
            order.status = new_status
            order.save()
            
            # 記錄隊列事件
            staff_id = staff_member.id if staff_member else None
            log_queue_event(
                order_id,
                old_status,
                new_status,
                staff_id,
                {'staff_name': staff_member.get_full_name() if staff_member else None}
            )
            
            self.logger.info(f"訂單狀態更新成功: {order_id}")
            
        except Exception as e:
            self.logger.error(f"更新訂單狀態失敗: {str(e)}", exc_info=True)
            raise
```

### 4. 日誌查看工具

```python
# eshop/management/commands/view_logs.py
"""
日誌查看管理命令。
"""
import os
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = '查看和分析日誌文件'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='app.log',
            help='日誌文件名（默認: app.log）'
        )
        parser.add_argument(
            '--level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='日誌級別（默認: INFO）'
        )
        parser.add_argument(
            '--since',
            type=str,
            help='起始時間（格式: YYYY-MM-DD HH:MM:SS）'
        )
        parser.add_argument(
            '--until',
            type=str,
            help='結束時間（格式: YYYY-MM-DD HH:MM:SS）'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='搜索關鍵詞'
        )
        parser.add_argument(
            '--module',
            type=str,
            help='模塊名稱（如: eshop, cart, payment）'
        )
        parser.add_argument(
            '--order-id',
            type=int,
            help='訂單ID'
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='用戶ID'
        )
        parser.add_argument(
            '--request-id',
            type=str,
            help='請求ID'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='輸出JSON格式'
        )
        parser.add_argument(
            '--count',
            action='store_true',
            help='只顯示統計數量'
        )
        parser.add_argument(
            '--tail',
            type=int,
            help='顯示最後N行'
        )
    
    def handle(self, *args, **options):
        log_file = os.path.join('logs', options['file'])
        
        if not os.path.exists(log_file):
            self.stdout.write(self.style.ERROR(f"日誌文件不存在: {log_file}"))
            return
        
        # 讀取日誌文件
        with open(log_file, 'r', encoding='utf-8') as f:
            if options['tail']:
                # 讀取最後N行
                lines = self._tail(f, options['tail'])
            else:
                lines = f.readlines()
        
        # 過濾日誌
        filtered_lines = self.filter_logs(lines, options)
        
        # 輸出結果
        if options['count']:
            self.show_count(filtered_lines, options)
        elif options['json']:
            self.show_json(filtered_lines, options)
        else:
            self.show_logs(filtered_lines, options)
    
    def _tail(self, f, n):
        """
        讀取文件的最後N行。
        """
        # 簡單實現，對於大文件可能效率不高
        lines = f.readlines()
        return lines[-n:] if len(lines) >= n else lines
    
    def filter_logs(self, lines, options):
        """
        過濾日誌行。
        """
        filtered = []
        
        # 時間過濾
        since = None
        until = None
        
        if options['since']:
            since = datetime.strptime(options['since'], '%Y-%m-%d %H:%M:%S')
        if options['until']:
            until = datetime.strptime(options['until'], '%Y-%m-%d %H:%M:%S')
        
        for line in lines:
            # 提取時間戳
            try:
                # 嘗試解析時間戳
                parts = line.split()
                if len(parts) >= 2:
                    timestamp_str = f"{parts[0]} {parts[1]}"
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    # 時間過濾
                    if since and log_time < since:
                        continue
                    if until and log_time > until:
                        continue
            except:
                pass
            
            # 級別過濾
            level = options['level']
            if level and not self._check_log_level(line, level):
                continue
            
            # 關鍵詞搜索
            if options['search'] and options['search'].lower() not in line.lower():
                continue
            
            # 模塊過濾
            if options['module'] and f" {options['module']}." not in line:
                continue
            
            # 訂單ID過濾
            if options['order_id'] and f"order_id={options['order_id']}" not in line:
                continue
            
            # 用戶ID過濾
            if options['user_id'] and f"user_id={options['user_id']}" not in line:
                continue
            
            # 請求ID過濾
            if options['request_id'] and options['request_id'] not in line:
                continue
            
            filtered.append(line)
        
        return filtered
    
    def _check_log_level(self, line, min_level):
        """
        檢查日誌級別。
        """
        levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50,
        }
        
        min_level_num = levels.get(min_level, 20)
        
        for level_name, level_num in levels.items():
            if level_name in line and level_num >= min_level_num:
                return True
        
        return False
    
    def show_count(self, lines, options):
        """
        顯示統計數量。
        """
        self.stdout.write(f"總日誌行數: {len(lines)}")
        
        # 按級別統計
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level_counts = {level: 0 for level in levels}
        
        for line in lines:
            for level in levels:
                if level in line:
                    level_counts[level] += 1
                    break
        
        self.stdout.write("\n按級別統計:")
        for level, count in level_counts.items():
            if count > 0:
                self.stdout.write(f"  {level}: {count}")
    
    def show_json(self, lines, options):
        """
        以JSON格式輸出日誌。
        """
        import json
        
        logs = []
        for line in lines:
            # 嘗試解析為JSON（如果是JSON格式日誌）
            if line.strip().startswith('{'):
                try:
                    log_data = json.loads(line.strip())
                    logs.append(log_data)
                except:
                    pass
        
        self.stdout.write(json.dumps(logs, indent=2, ensure_ascii=False))
    
    def show_logs(self, lines, options):
        """
        以可讀格式輸出日誌。
        """
        for line in lines:
            # 高亮錯誤和警告
            if 'ERROR' in line or 'CRITICAL' in line:
                self.stdout.write(self.style.ERROR(line.rstrip()))
            elif 'WARNING' in line:
                self.stdout.write(self.style.WARNING(line.rstrip()))
            elif 'INFO' in line:
                self.stdout.write(self.style.SUCCESS(line.rstrip()))
            else:
                self.stdout.write(line.rstrip())
```

### 5. 日誌分析報告

```python
# eshop/management/commands/log_analysis.py
"""
日誌分析管理命令。
"""
import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = '分析日誌並生成報告'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='分析最近N天的日誌（默認: 1）'
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['console', 'json', 'html'],
            default='console',
            help='輸出格式（默認: console）'
        )
        parser.add_argument(
            '--save-to',
            type=str,
            help='保存報告到文件'
        )
    
    def handle(self, *args, **options):
        # 確定分析時間範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=options['days'])
        
        self.stdout.write(f"分析時間範圍: {start_date} 到 {end_date}")
        self.stdout.write(f"輸出格式: {options['output']}")
        
        # 收集分析數據
        analysis_data = self.analyze_logs(start_date, end_date)
        
        # 生成報告
        report = self.generate_report(analysis_data, options)
        
        # 輸出報告
        if options['save_to']:
            with open(options['save_to'], 'w', encoding='utf-8') as f:
                f.write(report)
            self.stdout.write(self.style.SUCCESS(f"報告已保存到: {options['save_to']}"))
        else:
            self.stdout.write(report)
    
    def analyze_logs(self, start_date, end_date):
        """
        分析日誌文件。
        """
        analysis = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'summary': {
                'total_logs': 0,
                'by_level': Counter(),
                'by_module': Counter(),
                'by_hour': Counter(),
            },
            'errors': [],
            'performance': {
                'slow_requests': [],
                'avg_response_time': 0,
                'max_response_time': 0,
            },
            'business_metrics': {
                'total_orders': 0,
                'total_payments': 0,
                'successful_payments': 0,
                'failed_payments': 0,
                'queue_transitions': defaultdict(Counter),
            },
            'alerts': [],
        }
        
        # 分析所有日誌文件
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            return analysis
        
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                self.analyze_log_file(filepath, start_date, end_date, analysis)
        
        return analysis
    
    def analyze_log_file(self, filepath, start_date, end_date, analysis):
        """
        分析單個日誌文件。
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 更新總計數
                    analysis['summary']['total_logs'] += 1
                    
                    # 分析日誌級別
                    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        if level in line:
                            analysis['summary']['by_level'][level] += 1
                            break
                    
                    # 分析模塊
                    if 'eshop.' in line:
                        analysis['summary']['by_module']['eshop'] += 1
                    elif 'cart.' in line:
                        analysis['summary']['by_module']['cart'] += 1
                    elif 'payment.' in line:
                        analysis['summary']['by_module']['payment'] += 1
                    
                    # 分析時間
                    try:
                        parts = line.split()
                        if len(parts) >= 2:
                            timestamp_str = f"{parts[0]} {parts[1].split(',')[0]}"
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            hour = log_time.hour
                            analysis['summary']['by_hour'][hour] += 1
                    except:
                        pass
                    
                    # 收集錯誤
                    if 'ERROR' in line or 'CRITICAL' in line:
                        analysis['errors'].append({
                            'message': line[:200],
                            'timestamp': timestamp_str if 'timestamp_str' in locals() else None,
                            'file': os.path.basename(filepath),
                        })
                    
                    # 分析性能指標
                    if '性能指標:' in line:
                        try:
                            # 提取性能數據
                            if 'duration_ms' in line:
                                import re
                                match = re.search(r'duration_ms=([\d.]+)', line)
                                if match:
                                    duration = float(match.group(1))
                                    analysis['performance']['slow_requests'].append({
                                        'duration': duration,
                                        'message': line[:100],
                                    })
                        except:
                            pass
                    
                    # 分析業務指標
                    if '訂單事件:' in line:
                        analysis['business_metrics']['total_orders'] += 1
                    
                    if '支付事件:' in line:
                        analysis['business_metrics']['total_payments'] += 1
                        if 'success' in line:
                            analysis['business_metrics']['successful_payments'] += 1
                        elif 'failed' in line:
                            analysis['business_metrics']['failed_payments'] += 1
                    
                    if '隊列事件:' in line:
                        # 分析狀態轉換
                        if '->' in line:
                            parts = line.split('->')
                            if len(parts) == 2:
                                old_status = parts[0].strip().split()[-1]
                                new_status = parts[1].strip().split()[0]
                                key = f"{old_status}->{new_status}"
                                analysis['business_metrics']['queue_transitions'][key] += 1
        
        except Exception as e:
            analysis['alerts'].append({
                'type': 'analysis_error',
                'message': f"分析文件 {filepath} 時出錯: {str(e)}",
            })
    
    def generate_report(self, analysis, options):
        """
        生成分析報告。
        """
        if options['output'] == 'json':
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        
        elif options['output'] == 'html':
            return self.generate_html_report(analysis)
        
        else:  # console
            return self.generate_console_report(analysis)
    
    def generate_console_report(self, analysis):
        """
        生成控制台報告。
        """
        report = []
        report.append("=" * 80)
        report.append("日誌分析報告")
        report.append("=" * 80)
        
        # 時間範圍
        report.append(f"\n時間範圍: {analysis['period']['start']} 到 {analysis['period']['end']}")
        
        # 摘要統計
        report.append("\n摘要統計:")
        report.append(f"  總日誌數: {analysis['summary']['total_logs']}")
        
        report.append("\n  按級別統計:")
        for level, count in sorted(analysis['summary']['by_level'].items()):
            report.append(f"    {level}: {count}")
        
        report.append("\n  按模塊統計:")
        for module, count in sorted(analysis['summary']['by_module'].items()):
            report.append(f"    {module}: {count}")
        
        # 業務指標
        report.append("\n業務指標:")
        report.append(f"  總訂單數: {analysis['business_metrics']['total_orders']}")
        report.append(f"  總支付數: {analysis['business_metrics']['total_payments']}")
        report.append(f"  支付成功率: {analysis['business_metrics']['successful_payments']}/{analysis['business_metrics']['total_payments']}")
        
        report.append("\n  隊列狀態轉換:")
        for transition, count in sorted(analysis['business_metrics']['queue_transitions'].items()):
            report.append(f"    {transition}: {count}")
        
        # 錯誤統計
        if analysis['errors']:
            report.append(f"\n錯誤統計（共 {len(analysis['errors'])} 個）:")
            for i, error in enumerate(analysis['errors'][:10], 1):
                report.append(f"  {i}. {error['message']}")
            
            if len(analysis['errors']) > 10:
                report.append(f"  ... 還有 {len(analysis['errors']) - 10} 個錯誤")
        
        # 警報
        if analysis['alerts']:
            report.append(f"\n警報（共 {len(analysis['alerts'])} 個）:")
            for alert in analysis['alerts']:
                report.append(f"  - {alert['message']}")
        
        report.append("\n" + "=" * 80)
        
        return '\n'.join(report)
    
    def generate_html_report(self, analysis):
        """
        生成HTML報告。
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>日誌分析報告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
                h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .error { color: #dc3545; }
                .warning { color: #ffc107; }
                .success { color: #28a745; }
                .info { color: #17a2b8; }
                .chart { height: 300px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>日誌分析報告</h1>
        """
        
        # 時間範圍
        html += f"""
            <p><strong>時間範圍:</strong> {analysis['period']['start']} 到 {analysis['period']['end']}</p>
        """
        
        # 摘要統計
        html += """
            <h2>摘要統計</h2>
            <table>
                <tr>
                    <th>指標</th>
                    <th>值</th>
                </tr>
        """
        
        html += f"""
                <tr>
                    <td>總日誌數</td>
                    <td>{analysis['summary']['total_logs']}</td>
                </tr>
        """
        
        for level, count in sorted(analysis['summary']['by_level'].items()):
            html += f"""
                <tr>
                    <td>{level}</td>
                    <td>{count}</td>
                </tr>
            """
        
        html += """
            </table>
        """
        
        # 業務指標
        html += """
            <h2>業務指標</h2>
            <table>
                <tr>
                    <th>指標</th>
                    <th>值</th>
                </tr>
        """
        
        html += f"""
                <tr>
                    <td>總訂單數</td>
                    <td>{analysis['business_metrics']['total_orders']}</td>
                </tr>
                <tr>
                    <td>總支付數</td>
                    <td>{analysis['business_metrics']['total_payments']}</td>
                </tr>
                <tr>
                    <td>支付成功率</td>
                    <td>{analysis['business_metrics']['successful_payments']}/{analysis['business_metrics']['total_payments']}</td>
                </tr>
        """
        
        html += """
            </table>
        """
        
        # 錯誤列表
        if analysis['errors']:
            html += f"""
                <h2>錯誤列表（共 {len(analysis['errors'])} 個）</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>錯誤信息</th>
                        <th>時間</th>
                    </tr>
            """
            
            for i, error in enumerate(analysis['errors'][:20], 1):
                html += f"""
                    <tr>
                        <td>{i}</td>
                        <td class="error">{error['message'][:100]}...</td>
                        <td>{error['timestamp'] or 'N/A'}</td>
                    </tr>
                """
            
            html += """
                </table>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
```

### 6. 日誌系統使用示例

```python
# 示例：在視圖中使用日誌

from eshop.logging_utils import (
    get_logger, log_order_event, log_payment_event,
    log_queue_event, log_websocket_event, timed_logger
)

logger = get_logger(__name__)

class OrderCreateView(View):
    """
    訂單創建視圖。
    """
    
    @timed_logger('order_create_view')
    def post(self, request):
        try:
            # 記錄請求開始
            logger.info(f"收到訂單創建請求: {request.POST}")
            
            # 處理訂單創建邏輯
            order_data = self.extract_order_data(request)
            order = self.create_order(order_data)
            
            # 記錄訂單事件
            log_order_event(
                order.id,
                'created',
                '訂單創建成功',
                {'customer_name': order.customer_name, 'total': order.total_price}
            )
            
            # 記錄支付事件（如果有）
            if order.payment_method:
                log_payment_event(
                    order.id,
                    order.payment_method,
                    order.total_price,
                    'pending',
                    {'customer_phone': order.phone}
                )
            
            logger.info(f"訂單創建成功: {order.id}")
            
            return JsonResponse({'success': True, 'order_id': order.id})
            
        except Exception as e:
            logger.error(f"訂單創建失敗: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# 示例：在 WebSocket Consumer 中使用日誌

from channels.generic.websocket import AsyncWebsocketConsumer
from eshop.logging_utils import log_websocket_event

class OrderConsumer(AsyncWebsocketConsumer):
    """
    訂單 WebSocket Consumer。
    """
    
    async def connect(self):
        try:
            await self.accept()
            
            # 記錄連接事件
            log_websocket_event(
                'connect',
                self.channel_name,
                f"用戶 {self.scope['user'].username} 連接成功"
            )
            
        except Exception as e:
            log_websocket_event(
                'error',
                self.channel_name,
                f"連接失敗: {str(e)}",
                {'error': str(e)}
            )
            raise
    
    async def disconnect(self, close_code):
        log_websocket_event(
            'disconnect',
            self.channel_name,
            f"連接關閉，代碼: {close_code}"
        )
```

## 部署步驟

### 1. 創建日誌目錄
```bash
mkdir -p logs
chmod 755 logs
```

### 2. 更新配置
將日誌配置添加到 `settings.py`。

### 3. 添加中間件
將 `RequestIDMiddleware` 添加到 `MIDDLEWARE` 設置中。

### 4. 安裝依賴
```bash
pip install python-json-logger  # 可選，用於 JSON 格式日誌
```

### 5. 配置日誌輪轉
```bash
# 設置 logrotate
sudo nano /etc/logrotate.d/betweencoffee

# 添加以下內容
/var/www/betweencoffee_delivery_enhance/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload betweencoffee
    endscript
}
```

## 監控和維護

### 1. 每日檢查
```bash
# 檢查日誌文件大小
du -sh logs/

# 檢查錯誤數量
grep -c "ERROR" logs/error.log

# 檢查磁盤空間
df -h
```

### 2. 自動清理
```bash
# 清理30天前的日誌
find logs/ -name "*.log.*" -mtime +30 -delete
```

### 3. 實時監控
```bash
# 實時查看日誌
tail -f logs/app.log

# 查看錯誤日誌
tail -f logs/error.log

# 查看特定訂單的日誌
grep "order_id=123" logs/app.log
```

## 總結

通過改進日誌系統，我們實現了：

1. **統一日誌格式**：所有模塊使用相同的日誌格式
2. **豐富的上下文**：包含請求ID、用戶ID、IP地址等信息
3. **結構化日誌**：支持JSON格式，便於分析
4. **性能監控**：自動記錄函數執行時間
5. **業務事件追蹤**：專門記錄訂單、支付、隊列等業務事件
6. **便捷的工具**：提供日誌查看和分析命令

