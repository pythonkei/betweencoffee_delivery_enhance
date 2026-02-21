# eshop/models_refactored.py
"""
模型類 - 使用統一錯誤處理框架（遷移版本）

這個版本將關鍵方法遷移到新的錯誤處理框架，提供：
1. 統一的錯誤處理
2. 標準化的響應格式
3. 詳細的錯誤日誌
4. 錯誤ID追蹤

注意：這個文件只包含遷移後的方法，其他部分保持不變
"""

import warnings
import json
import random
import string
import secrets
import qrcode
import io
import base64
import logging
import pytz
from django.conf import settings
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

from .time_calculation import unified_time_service
from .error_handling import (
    handle_error,
    handle_success,
    handle_database_error,
    ErrorHandler
)

logger = logging.getLogger(__name__)

# 創建模型錯誤處理器
models_error_handler = ErrorHandler(module_name='models')


# ==================== 遷移的關鍵方法 ====================

class OrderModel(models.Model):
    """
    訂單模型 - 遷移版本
    只包含遷移到錯誤處理框架的方法
    """
    
    # ====== 基礎字段 ======
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=80, blank=True, null=True, default='')
    phone = models.CharField(max_length=12, blank=True, null=True)
    
    # ====== 支付狀態字段 ======
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('cancelled', '已取消'),
        ('expired', '已过期'),
    ]
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending',
        verbose_name='支付状态'
    )
    
    # ====== 取貨時間相關字段 ======
    pickup_time_choice = models.CharField(
        max_length=20, 
        choices=[
            ('5', '5分鐘後'),
            ('10', '10分鐘後'), 
            ('15', '15分鐘後'),
            ('20', '20分鐘後'),
            ('30', '30分鐘後'),
        ],
        default='5',
        verbose_name='取貨時間選擇'
    )
    
    latest_start_time = models.DateTimeField(null=True, blank=True, verbose_name="最晚開始時間")
    is_delivery = models.BooleanField(default=False)
    items = models.JSONField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    
    # ====== 訂單狀態相關字段 ======
    ORDER_TYPE_CHOICES = [
        ('normal', '普通訂單'),
        ('quick', '快速訂單'),
    ]
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='normal')
    is_quick_order = models.BooleanField(default=False, verbose_name='快速訂單', help_text='優先處理')
    
    pickup_code = models.CharField(max_length=4, unique=True, blank=True)
    qr_code = models.TextField(blank=True, null=True)
    estimated_ready_time = models.DateTimeField(blank=True, null=True)
    
    # ====== 製作時間字段 ======
    preparation_started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始制作时间")
    ready_at = models.DateTimeField(null=True, blank=True, verbose_name="完成制作时间")
    
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', '待處理'),
        ('waiting', '等待制作'),
        ('preparing', '制作中'),
        ('ready', '已就緒'),
        ('completed', '已提取')
    ])
    
    picked_up_at = models.DateTimeField(null=True, blank=True, verbose_name="提取时间")
    picked_up_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="提取人员")
    
    # ====== 支付超時相關字段 ======
    payment_timeout = models.DateTimeField(null=True, blank=True, verbose_name="支付超时时间")
    payment_attempts = models.IntegerField(default=0)
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    payment_reminder_sent = models.BooleanField(default=False)
    
    # ====== 支付方式字段 ======
    PAYMENT_METHOD_CHOICES = [
        ('alipay', '支付宝'),
        ('paypal', 'PayPal'),
        ('fps', 'FPS转数快'),
        ('cash', '现金支付'),
    ]
    payment_method = models.CharField(
        max_length=10, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='alipay',
        verbose_name='支付方式'
    )
    
    fps_reference = models.CharField(max_length=50, blank=True, null=True, verbose_name='FPS参考编号')
    fps_qr_code = models.TextField(blank=True, null=True, verbose_name='FPS二维码')
    
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['payment_status', 'payment_timeout']),
            models.Index(fields=['created_at', 'payment_status']),
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['status', 'updated_at']),
        ]
        verbose_name = '订单'
        verbose_name_plural = '订单'
    
    def __str__(self):
        local_time = timezone.localtime(self.created_at)
        return f'Order: {local_time.strftime("%b %d %I: %M %p")}'
    
    # ==================== 遷移的方法 ====================
    
    def get_items(self):
        """
        解析 JSON 字符串，並返回包含數值項的列表 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'items': [...],  # 商品列表
                'count': 0,      # 商品數量
                'has_coffee': True/False,
                'has_beans': True/False
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 延遲導入，避免循環導入
            from .models import CoffeeItem, BeanItem
            
            if isinstance(self.items, str):
                items = json.loads(self.items)
            else:
                items = self.items
            
            processed_items = []
            has_coffee = False
            has_beans = False
            
            for item in items:
                try:
                    processed_item = item.copy()
                    
                    # 確保 price 鍵存在
                    if 'price' not in processed_item:
                        try:
                            if processed_item['type'] == 'coffee':
                                product = CoffeeItem.objects.get(id=processed_item['id'])
                                processed_item['price'] = float(product.price)
                            elif processed_item['type'] == 'bean':
                                product = BeanItem.objects.get(id=processed_item['id'])
                                weight = processed_item.get('weight', '200g')
                                processed_item['price'] = float(product.get_price(weight))
                            else:
                                processed_item['price'] = 0.0
                        except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist, KeyError) as e:
                            logger.warning(f"獲取商品價格失敗: {str(e)}")
                            processed_item['price'] = 0.0
                    else:
                        processed_item['price'] = float(processed_item['price'])
                    
                    # 確保 quantity 存在
                    if 'quantity' not in processed_item:
                        processed_item['quantity'] = 1
                    
                    # 計算總價
                    if 'total_price' not in processed_item:
                        processed_item['total_price'] = processed_item['price'] * processed_item['quantity']
                    else:
                        processed_item['total_price'] = float(processed_item['total_price'])
                    
                    # 確保圖片 URL 存在
                    if 'image' not in processed_item:
                        try:
                            if processed_item['type'] == 'coffee':
                                product = CoffeeItem.objects.get(id=processed_item['id'])
                            elif processed_item['type'] == 'bean':
                                product = BeanItem.objects.get(id=processed_item['id'])
                            else:
                                product = None
                                
                            if product:
                                processed_item['image'] = product.image.url
                            else:
                                processed_item['image'] = '/static/images/default-product.png'
                        except Exception as e:
                            logger.warning(f"獲取商品圖片失敗: {str(e)}")
                            processed_item['image'] = '/static/images/default-product.png'
                    
                    # 記錄商品類型
                    if processed_item.get('type') == 'coffee':
                        has_coffee = True
                    elif processed_item.get('type') == 'bean':
                        has_beans = True
                    
                    processed_items.append(processed_item)
                    
                except (TypeError, ValueError, KeyError) as e:
                    logger.error(f"處理商品項目失敗: {item}, 錯誤: {str(e)}")
                    # 創建一個安全的默認項目
                    safe_item = {
                        'id': item.get('id', 0),
                        'name': item.get('name', '未知商品'),
                        'type': item.get('type', 'unknown'),
                        'price': 0.0,
                        'quantity': item.get('quantity', 1),
                        'total_price': 0.0,
                        'image': '/static/images/default-product.png'
                    }
                    processed_items.append(safe_item)
            
            return handle_success(
                operation='get_items',
                data={
                    'items': processed_items,
                    'count': len(processed_items),
                    'has_coffee': has_coffee,
                    'has_beans': has_beans,
                    'is_beans_only': has_beans and not has_coffee,
                    'is_coffee_only': has_coffee and not has_beans,
                    'is_mixed_order': has_coffee and has_beans
                },
                message=f'成功解析 {len(processed_items)} 個商品'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderModel.get_items',
                operation='get_items',
                data={
                    'order_id': self.id,
                    'items_raw': str(self.items)[:100] if self.items else None
                }
            )
    
    def get_items_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的商品列表
        
        為了保持向後兼容性，這個方法返回原始的商品列表格式
        而不是錯誤處理框架的響應格式
        """
        result = self.get_items()
        
        if result.get('success'):
            return result['data']['items']
        else:
            # 如果失敗，返回空列表
            logger.error(f"獲取商品失敗，返回空列表: {result.get('error_id', 'N/A')}")
            return []
    
    def save(self, *args, **kwargs):
        """
        保存訂單，處理取餐碼、二維碼和預計時間 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'order_id': self.id,
                'pickup_code': self.pickup_code,
                'has_qr_code': bool(self.qr_code),
                'estimated_ready_time': self.estimated_ready_time,
                'status': self.status,
                'payment_status': self.payment_status
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            logger.info(f"=== 開始保存訂單 {self.id or '新訂單'} ===")
            
            # 修復：確保在保存前就有 pickup_code
            if not self.pickup_code or self.pickup_code == '':
                logger.info("為新訂單生成取餐碼")
                pickup_result = self.generate_unique_pickup_code()
                
                if pickup_result.get('success'):
                    self.pickup_code = pickup_result['data']['pickup_code']
                    logger.info(f"生成取餐碼: {self.pickup_code}")
                else:
                    logger.error(f"生成取餐碼失敗: {pickup_result.get('error_id', 'N/A')}")
                    # 使用備用取餐碼
                    self.pickup_code = self._generate_fallback_pickup_code()
            
            # 更新時間戳
            self.updated_at = timezone.now()
            
            # 確保在支付成功後計算預計就緒時間
            if self.payment_status == 'paid' and not self.estimated_ready_time:
                time_result = self.calculate_estimated_ready_time()
                
                if time_result.get('success') and time_result['data'].get('estimated_ready_time'):
                    self.estimated_ready_time = time_result['data']['estimated_ready_time']
                    logger.info(f"預計就緒時間: {self.estimated_ready_time}")
            
            # 生成二維碼數據
            if not self.qr_code and self.pickup_code:
                qr_result = self.generate_qr_code_data()
                
                if qr_result.get('success') and qr_result['data'].get('qr_code_data'):
                    self.qr_code = qr_result['data']['qr_code_data']
                    logger.info("生成二維碼數據成功")
                else:
                    logger.warning(f"生成二維碼失敗: {qr_result.get('error_id', 'N/A')}")
            
            # ====== 檢查並更新訂單狀態 ======
            # 如果訂單已支付且狀態是 pending，更新為 waiting
            if self.payment_status == 'paid' and self.status == 'pending':
                logger.info("更新訂單狀態為 waiting（等待制作）")
                self.status = 'waiting'
            
            # 調用父類保存方法
            super().save(*args, **kwargs)
            logger.info(f"訂單保存成功: {self.id}")
            
            # ========== 隊列處理邏輯 ==========
            # 使用 OrderStatusManager 來處理隊列加入
            if self.status == 'waiting' and self.payment_status == 'paid':
                try:
                    from .order_status_manager import OrderStatusManager
                    manager = OrderStatusManager(self)
                    
                    if manager.should_add_to_queue():
                        logger.info(f"訂單 {self.id} 符合加入隊列條件，嘗試加入隊列")
                        
                        from .queue_manager_refactored import CoffeeQueueManager
                        from .models import CoffeeQueue
                        
                        queue_manager = CoffeeQueueManager()
                        
                        # 檢查是否已經在隊列中
                        existing_queue_item = CoffeeQueue.objects.filter(order=self).first()
                        if existing_queue_item:
                            logger.info(f"訂單 {self.id} 已在隊列中，位置: {existing_queue_item.position}")
                        else:
                            # 將訂單加入隊列
                            queue_item = queue_manager.add_order_to_queue(self)
                            if queue_item:
                                logger.info(f"訂單 {self.id} 已加入制作隊列，位置: {queue_item.position}")
                            else:
                                logger.warning(f"訂單 {self.id} 加入隊列失敗")
                except Exception as e:
                    logger.error(f"隊列處理失敗: {str(e)}")
                    # 不拋出異常，繼續執行
            # ========== 隊列處理結束 ==========
            
            return handle_success(
                operation='save',
                data={
                    'order_id': self.id,
                    'pickup_code': self.pickup_code,
                    'has_qr_code': bool(self.qr_code),
                    'estimated_ready_time': self.estimated_ready_time,
                    'status': self.status,
                    'payment_status': self.payment_status,
                    'created': self.id is not None  # 是否是新創建的訂單
                },
                message=f'訂單保存成功'
            )
                
        except Exception as e:
            # 如果是唯一約束錯誤，重新生成取餐碼並重試
            if 'pickup_code_key' in str(e):
                logger.info("檢測到取餐碼重複，重新生成並重試")
                self.pickup_code = self._generate_fallback_pickup_code()
                
                try:
                    super().save(*args, **kwargs)
                    
                    return handle_success(
                        operation='save',
                        data={
                            'order_id': self.id,
                            'pickup_code': self.pickup_code,
                            'retry_success': True
                        },
                        message='訂單保存成功（重試後）'
                    )
                except Exception as retry_error:
                    return handle_database_error(
                        error=retry_error,
                        context='OrderModel.save_retry',
                        operation='save',
                        data={
                            'order_id': self.id,
                            'original_error': str(e),
                            'retry_error': str(retry_error)
                        }
                    )
            else:
                return handle_database_error(
                    error=e,
                    context='OrderModel.save',
                    operation='save',
                    data={'order_id': self.id}
                )
    
    def generate_unique_pickup_code(self):
        """
        生成唯一的取餐碼 - 4位數字版本 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'pickup_code': '1234',
                'generation_method': 'timestamp/random/uuid/sequential',
                'attempts': 0
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            import time
            import uuid
            
            max_attempts = 100
            generation_method = 'unknown'
            attempts = 0
            
            # 方法1：使用時間戳 + 隨機數（推薦）
            for attempt in range(max_attempts):
                attempts = attempt + 1
                # 生成4位數字碼：時間戳後2位 + 隨機2位
                timestamp_part = str(int(time.time() * 1000))[-2:]  # 時間戳後2位
                random_part = ''.join(secrets.choice(string.digits) for _ in range(2))
                code = timestamp_part + random_part
                
                if not OrderModel.objects.filter(pickup_code=code).exists():
                    generation_method = 'timestamp'
                    logger.info(f"生成時間戳取餐碼: {code}, 嘗試次數: {attempts}")
                    
                    return handle_success(
                        operation='generate_unique_pickup_code',
                        data={
                            'pickup_code': code,
                            'generation_method': generation_method,
                            'attempts': attempts
                        },
                        message='取餐碼生成成功（時間戳方法）'
                    )
            
            # 方法2：純隨機4位數字
            for attempt in range(max_attempts):
                attempts += 1
                code = ''.join(secrets.choice(string.digits) for _ in range(4))
                if not OrderModel.objects.filter(pickup_code=code).exists():
                    generation_method = 'random'
                    logger.info(f"生成隨機取餐碼: {code}, 嘗試次數: {attempts}")
                    
                    return handle_success(
                        operation='generate_unique_pickup_code',
                        data={
                            'pickup_code': code,
                            'generation_method': generation_method,
                            'attempts': attempts
                        },
                        message='取餐碼生成成功（隨機方法）'
                    )
            
            # 方法3：UUID簡化版（取前4位數字）
            for attempt in range(max_attempts):
                attempts += 1
                uuid_int = uuid.uuid4().int
                # 從UUID中提取4位數字
                code = str(uuid_int % 10000).zfill(4)  # 確保4位，不足補0
                if not OrderModel.objects.filter(pickup_code=code).exists():
                    generation_method = 'uuid'
                    logger.info(f"使用UUID取餐碼: {code}, 嘗試次數: {attempts}")
                    
                    return handle_success(
                        operation='generate_unique_pickup_code',
                        data={
                            'pickup_code': code,
                            'generation_method': generation_method,
                            'attempts': attempts
                        },
                        message='取餐碼生成成功（UUID方法）'
                    )
            
            # 方法4：最後的手段 - 順序生成
            last_code = OrderModel.objects.order_by('-id').first()
            if last_code and last_code.pickup_code:
                try:
                    last_num = int(last_code.pickup_code)
                    for i in range(1, 100):
                        attempts += 1
                        code = str((last_num + i) % 10000).zfill(4)
                        if not OrderModel.objects.filter(pickup_code=code).exists():
                            generation_method = 'sequential'
                            logger.info(f"使用順序取餐碼: {code}, 嘗試次數: {attempts}")
                            
                            return handle_success(
                                operation='generate_unique_pickup_code',
                                data={
                                    'pickup_code': code,
                                    'generation_method': generation_method,
                                    'attempts': attempts
                                },
                                message='取餐碼生成成功（順序方法）'
                            )
                except ValueError:
                    pass
            
            # 如果所有方法都失敗，返回一個安全的默認值
            code = '1234'
            generation_method = 'fallback'
            logger.warning(f"所有取餐碼生成方法都失敗，使用默認值: {code}, 總嘗試次數: {attempts}")
            
            return handle_success(
                operation='generate_unique_pickup_code',
                data={
                    'pickup_code': code,
                    'generation_method': generation_method,
                    'attempts': attempts,
                    'is_fallback': True
                },
                message='取餐碼生成成功（備用方法）'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderModel.generate_unique_pickup_code',
                operation='generate_unique_pickup_code',
                data={'max_attempts': 100}
            )
    
    def _generate_fallback_pickup_code(self):
        """生成備用取餐碼（內部使用）"""
        import time
        import secrets
        
        # 使用時間戳生成簡單的取餐碼
        timestamp = int(time.time() * 1000)
        code = str(timestamp % 10000).zfill(4)
        
        # 如果還是重複，使用隨機數
        if OrderModel.objects.filter(pickup_code=code).exists():
            code = ''.join(secrets.choice(string.digits) for _ in range(4))
        
        logger.warning(f"使用備用取餐碼: {code}")
        return code
    
    def generate_qr_code_data(self):
        """
        生成二維碼數據 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'qr_code_data': 'base64_encoded_data',
                'pickup_code': self.pickup_code,
                'order_id': self.id
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            logger.info(f"開始生成二維碼，訂單: {self.id}")
            
            # 確保取餐碼已生成
            if not self.pickup_code:
                logger.info(f"訂單 {self.id} 沒有取餐碼，調用 save() 生成")
                save_result = self.save()
                
                if not save_result.get('success'):
                    return handle_error(
                        error=Exception("無法生成取餐碼"),
                        context='OrderModel.generate_qr_code_data',
                        operation='generate_qr_code_data',
                        data={'order_id': self.id, 'save_result': save_result}
                    )
            
            # 二維碼包含訂單ID和取餐碼
            qr_data = f"Order: {self.id}, Pickup Code: {self.pickup_code}"
            
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                
                qr_code_data = base64.b64encode(buffer.getvalue()).decode()
                logger.info(f"訂單 {self.id} 二維碼生成成功")
                
                return handle_success(
                    operation='generate_qr_code_data',
                    data={
                        'qr_code_data': qr_code_data,
                        'pickup_code': self.pickup_code,
                        'order_id': self.id,
                        'qr_data': qr_data
                    },
                    message='二維碼生成成功'
                )
                
            except Exception as qr_error:
                logger.error(f"生成二維碼失敗: {str(qr_error)}")
                return handle_error(
                    error=qr_error,
                    context='OrderModel.generate_qr_code_data_qr',
                    operation='generate_qr_code_data',
                    data={
                        'order_id': self.id,
                        'pickup_code': self.pickup_code,
                        'qr_data': qr_data
                    }
                )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderModel.generate_qr_code_data',
                operation='generate_qr_code_data',
                data={'order_id': self.id}
            )
    
    def calculate_estimated_ready_time(self):
        """
        根據訂單中的商品計算預計就緒時間 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'estimated_ready_time': datetime,
                'total_coffee_quantity': 0,
                'has_coffee': True/False,
                'has_beans': True/False,
                'preparation_minutes': 0
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            from datetime import timedelta
            import random
            
            # 獲取商品列表
            items_result = self.get_items()
            
            if not items_result.get('success'):
                return handle_error(
                    error=Exception("無法獲取商品列表"),
                    context='OrderModel.calculate_estimated_ready_time',
                    operation='calculate_estimated_ready_time',
                    data={'order_id': self.id, 'items_result': items_result}
                )
            
            items = items_result['data']['items']
            has_coffee = items_result['data']['has_coffee']
            has_beans = items_result['data']['has_beans']
            
            # 如果只有咖啡豆，不需要預計就緒時間
            if has_beans and not has_coffee:
                logger.info("純咖啡豆訂單，不設置預計時間")
                
                return handle_success(
                    operation='calculate_estimated_ready_time',
                    data={
                        'estimated_ready_time': None,
                        'total_coffee_quantity': 0,
                        'has_coffee': False,
                        'has_beans': True,
                        'preparation_minutes': 0,
                        'is_beans_only': True
                    },
                    message='純咖啡豆訂單，無需制作時間'
                )
            
            # 如果沒有任何商品，返回None
            if not has_coffee and not has_beans:
                logger.info("無商品訂單，不設置預計時間")
                
                return handle_success(
                    operation='calculate_estimated_ready_time',
                    data={
                        'estimated_ready_time': None,
                        'total_coffee_quantity': 0,
                        'has_coffee': False,
                        'has_beans': False,
                        'preparation_minutes': 0,
                        'is_empty_order': True
                    },
                    message='無商品訂單，無需制作時間'
                )
            
            # 計算咖啡總數量
            total_coffee_quantity = 0
            for item in items:
                if item['type'] == 'coffee':
                    total_coffee_quantity += item['quantity']
            
            # 計算制作時間
            if total_coffee_quantity == 1:
                preparation_minutes = 5  # 單一杯5分鐘
            else:
                preparation_minutes = 5 + (total_coffee_quantity - 1) * 3  # 之後每杯遞增3分鐘
            
            # 添加隨機浮動（±1分鐘）
            fluctuation = random.randint(-1, 1)
            total_minutes = max(1, preparation_minutes + fluctuation)
            
            # 使用香港時區當前時間作為基準
            base_time = unified_time_service.get_hong_kong_time()
            estimated_time = base_time + timedelta(minutes=total_minutes)
            logger.info(f"計算制作時間: {total_minutes}分鐘, 預計時間: {estimated_time}")
            
            return handle_success(
                operation='calculate_estimated_ready_time',
                data={
                    'estimated_ready_time': estimated_time,
                    'total_coffee_quantity': total_coffee_quantity,
                    'has_coffee': True,
                    'has_beans': has_beans,
                    'preparation_minutes': total_minutes,
                    'base_preparation_minutes': preparation_minutes,
                    'fluctuation': fluctuation,
                    'base_time': base_time
                },
                message=f'預計制作時間: {total_minutes}分鐘'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderModel.calculate_estimated_ready_time',
                operation='calculate_estimated_ready_time',
                data={'order_id': self.id}
            )
    
    def get_items_with_chinese_options(self):
        """
        返回帶有中文選項的商品列表 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'items': [...],  # 帶中文選項的商品列表
                'count': 0,
                'has_chinese_options': True/False
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 獲取基本商品列表
            items_result = self.get_items()
            
            if not items_result.get('success'):
                return handle_error(
                    error=Exception("無法獲取商品列表"),
                    context='OrderModel.get_items_with_chinese_options',
                    operation='get_items_with_chinese_options',
                    data={'order_id': self.id, 'items_result': items_result}
                )
            
            items = items_result['data']['items']
            items_with_chinese = []
            has_chinese_options = False
            
            for item in items:
                item_with_chinese = item.copy()
                
                # 確保圖片路徑正確
                from .models import get_product_image_url
                item_with_chinese['image'] = get_product_image_url(item_with_chinese)
                
                # 根據商品類型處理不同的選項
                item_type = item_with_chinese.get('type', 'unknown')
                
                if item_type == 'coffee':
                    # 咖啡商品：只處理杯型和牛奶選項
                    if 'cup_level' in item_with_chinese:
                        item_with_chinese['cup_level_cn'] = self.translate_option('cup_level', item_with_chinese['cup_level'])
                        has_chinese_options = True
                    if 'milk_level' in item_with_chinese:
                        item_with_chinese['milk_level_cn'] = self.translate_option('milk_level', item_with_chinese['milk_level'])
                        has_chinese_options = True
                    # 咖啡商品不應該有重量選項，確保不顯示
                    if 'weight' in item_with_chinese:
                        logger.debug(f"咖啡商品 {item_with_chinese.get('name', '未知')} 包含重量選項: {item_with_chinese['weight']}")
                        # 移除重量選項，避免前端顯示
                        item_with_chinese.pop('weight', None)
                        
                elif item_type == 'bean':
                    # 咖啡豆商品：處理研磨選項和重量
                    if 'grinding_level' in item_with_chinese:
                        item_with_chinese['grinding_level_cn'] = self.translate_option('grinding_level', item_with_chinese['grinding_level'])
                        has_chinese_options = True
                    if 'weight' in item_with_chinese:
                        # 將重量轉換為中文顯示
                        item_with_chinese['weight_cn'] = self.translate_weight(item_with_chinese['weight'])
                        has_chinese_options = True
                else:
                    # 其他類型商品：處理所有可能的選項
                    if 'cup_level' in item_with_chinese:
                        item_with_chinese['cup_level_cn'] = self.translate_option('cup_level', item_with_chinese['cup_level'])
                        has_chinese_options = True
                    if 'milk_level' in item_with_chinese:
                        item_with_chinese['milk_level_cn'] = self.translate_option('milk_level', item_with_chinese['milk_level'])
                        has_chinese_options = True
                    if 'grinding_level' in item_with_chinese:
                        item_with_chinese['grinding_level_cn'] = self.translate_option('grinding_level', item_with_chinese['grinding_level'])
                        has_chinese_options = True
                
                items_with_chinese.append(item_with_chinese)
            
            return handle_success(
                operation='get_items_with_chinese_options',
                data={
                    'items': items_with_chinese,
                    'count': len(items_with_chinese),
                    'has_chinese_options': has_chinese_options,
                    'original_count': len(items)
                },
                message=f'成功處理 {len(items_with_chinese)} 個帶中文選項的商品'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderModel.get_items_with_chinese_options',
                operation='get_items_with_chinese_options',
                data={'order_id': self.id}
            )
    
    def get_items_with_chinese_options_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的帶中文選項商品列表
        """
        result = self.get_items_with_chinese_options()
        
        if result.get('success'):
            return result['data']['items']
        else:
            logger.error(f"獲取帶中文選項商品失敗，返回空列表: {result.get('error_id', 'N/A')}")
            return []
    
    @staticmethod
    def translate_option(option_type, value):
        """靜態方法：轉換選項值為中文"""
        mappings = {
            'cup_level': {
                'Small': '細',
                'Medium': '中',
                'Large': '大'
            },
            'milk_level': {
                'Light': '少',
                'Medium': '正常',
                'Extra': '追加'
            },
            'grinding_level': {
                'Non': '免研磨',
                'Light': '細',
                'Medium': '中',
                'Deep': '粗'
            }
        }
        return mappings.get(option_type, {}).get(value, value)
    
    @staticmethod
    def translate_weight(weight_value):
        """靜態方法：轉換重量值為中文顯示"""
        if not weight_value:
            return ''
        
        weight_str = str(weight_value).strip().lower()
        
        # 重量轉換映射
        weight_mappings = {
            '200g': '200克',
            '500g': '500克',
            '200克': '200克',
            '500克': '500克',
            '200': '200克',
            '500': '500克',
        }
        
        # 嘗試精確匹配
        if weight_str in weight_mappings:
            return weight_mappings[weight_str]
        
        # 嘗試模糊匹配
        for key, value in weight_mappings.items():
            if weight_str in key or key in weight_str:
                return value
        
        # 默認返回原值
        return weight_value


# ==================== 其他遷移的方法 ====================

def get_product_image_url(item_data):
    """
    根據商品數據獲取正確的圖片URL - 使用錯誤處理框架
    
    返回格式:
    {
        'success': True/False,
        'message': '操作消息',
        'data': {
            'image_url': 'url',
            'product_id': 0,
            'product_type': 'coffee/bean/unknown'
        },
        'details': {...},
        'timestamp': '...',
        'error_id': '...' (如果失敗)
    }
    """
    try:
        # 如果已經有圖片URL，直接返回
        if item_data.get('image'):
            return handle_success(
                operation='get_product_image_url',
                data={
                    'image_url': item_data['image'],
                    'product_id': item_data.get('id', 0),
                    'product_type': item_data.get('type', 'unknown'),
                    'source': 'provided'
                },
                message='使用提供的圖片URL'
            )
        
        # 如果沒有圖片URL，嘗試從數據庫獲取
        try:
            if item_data.get('type') == 'coffee':
                from .models import CoffeeItem
                coffee = CoffeeItem.objects.get(id=item_data['id'])
                image_url = coffee.image.url if coffee.image else '/static/images/default-coffee.png'
                product_type = 'coffee'
                
                return handle_success(
                    operation='get_product_image_url',
                    data={
                        'image_url': image_url,
                        'product_id': item_data['id'],
                        'product_type': product_type,
                        'source': 'database_coffee',
                        'has_image': bool(coffee.image)
                    },
                    message='從咖啡商品獲取圖片URL'
                )
            elif item_data.get('type') == 'bean':
                from .models import BeanItem
                bean = BeanItem.objects.get(id=item_data['id'])
                image_url = bean.image.url if bean.image else '/static/images/default-bean.png'
                product_type = 'bean'
                
                return handle_success(
                    operation='get_product_image_url',
                    data={
                        'image_url': image_url,
                        'product_id': item_data['id'],
                        'product_type': product_type,
                        'source': 'database_bean',
                        'has_image': bool(bean.image)
                    },
                    message='從咖啡豆商品獲取圖片URL'
                )
            else:
                # 默認圖片
                return handle_success(
                    operation='get_product_image_url',
                    data={
                        'image_url': '/static/images/default-product.png',
                        'product_id': item_data.get('id', 0),
                        'product_type': 'unknown',
                        'source': 'default'
                    },
                    message='使用默認圖片URL'
                )
        except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist) as e:
            logger.warning(f"商品不存在: {item_data.get('id', '未知')}, 類型: {item_data.get('type', '未知')}")
            
            return handle_success(
                operation='get_product_image_url',
                data={
                    'image_url': '/static/images/default-product.png',
                    'product_id': item_data.get('id', 0),
                    'product_type': item_data.get('type', 'unknown'),
                    'source': 'default_not_found'
                },
                message='商品不存在，使用默認圖片URL'
            )
            
    except Exception as e:
        return handle_error(
            error=e,
            context='get_product_image_url',
            operation='get_product_image_url',
            data={
                'item_data': str(item_data)[:100] if item_data else None
            }
        )


def get_product_image_url_compatible(item_data):
    """
    兼容性包裝器 - 返回原始格式的圖片URL
    """
    result = get_product_image_url(item_data)
    
    if result.get('success'):
        return result['data']['image_url']
    else:
        logger.error(f"獲取商品圖片URL失敗，返回默認圖片: {result.get('error_id', 'N/A')}")
        return '/static/images/default-product.png'


# ==================== 測試函數 ====================

if __name__ == "__main__":
    """測試模型遷移模塊"""
    import sys
    
    print("🔍 測試模型遷移模塊 - 使用統一錯誤處理框架")
    print("=" * 60)
    
    # 測試錯誤處理
    print("1. 測試錯誤處理...")
    # 模擬一個錯誤情況
    try:
        # 這裡可以模擬一個錯誤
        raise ValueError("測試錯誤")
    except Exception as e:
        error_result = handle_error(
            error=e,
            context='test_error_handling',
            operation='test_error_handling',
            data={'test': 'data'}
        )
        print(f"   錯誤處理測試: {error_result.get('success', False)}")
        print(f"   錯誤ID: {error_result.get('error_id', 'N/A')}")
    
    # 測試成功處理
    print("\n2. 測試成功處理...")
    success_result = handle_success(
        operation='test_success',
        data={'test': 'data'},
        message='測試成功'
    )
    print(f"   成功處理測試: {success_result.get('success', False)}")
    print(f"   消息: {success_result.get('message', 'N/A')}")
    
    # 測試圖片URL獲取
    print("\n3. 測試圖片URL獲取...")
    test_item = {'id': 1, 'type': 'coffee', 'name': '測試咖啡'}
    image_result = get_product_image_url(test_item)
    print(f"   圖片URL測試: {image_result.get('success', False)}")
    if image_result.get('success'):
        print(f"   圖片URL: {image_result['data'].get('image_url', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ 模型遷移模塊測試完成")
    
    sys.exit(0)
