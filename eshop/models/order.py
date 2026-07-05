# eshop/models/order.py
"""
訂單模型：OrderModel

從 models.py 提取的核心訂單模型。
包含所有字段、方法和屬性。
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

from .base import get_image_url
from ..time_calculation import unified_time_service

logger = logging.getLogger(__name__)


class OrderModel(models.Model):
    """核心訂單模型"""
    
    # ====== 基础字段 ======
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=80, blank=True, null=True, default='')
    phone = models.CharField(max_length=12, blank=True, null=True)
    
    # ====== 支付状态字段 ======
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待支付'),
        ('payment_pending', '付款待確認'),
        ('paid', '已支付'),
        ('cancelled', '已取消'),
        ('expired', '已過期'),
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
    
    # ====== 弃用字段：is_paid (向后兼容) ======
    @property
    def is_paid(self):
        """弃用字段：使用 payment_status 替代"""
        warnings.warn(
            "OrderModel.is_paid 字段已弃用，请使用 payment_status 字段。",
            DeprecationWarning,
            stacklevel=2
        )
        return self.payment_status == 'paid'
    
    @is_paid.setter
    def is_paid(self, value):
        """弃用字段设置器：同步到 payment_status"""
        warnings.warn(
            "OrderModel.is_paid 字段已弃用，请使用 payment_status 字段。",
            DeprecationWarning,
            stacklevel=2
        )
        if value:
            self.payment_status = 'paid'
        elif self.payment_status == 'paid':
            self.payment_status = 'pending'
    
    is_delivery = models.BooleanField(default=False)
    items = models.JSONField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    
    # ====== 订单状态相关字段 ======
    ORDER_TYPE_CHOICES = [
        ('normal', '普通訂單'),
        ('quick', '快速訂單'),
    ]
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='normal')
    is_quick_order = models.BooleanField(default=False, verbose_name='快速訂單', help_text='優先處理')
    
    pickup_code = models.CharField(max_length=4, unique=True, blank=True)
    qr_code = models.TextField(blank=True, null=True)
    estimated_ready_time = models.DateTimeField(blank=True, null=True)
    
    # ====== 制作时间字段 ======
    preparation_started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始制作时间")
    ready_at = models.DateTimeField(null=True, blank=True, verbose_name="完成制作时间")
    
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', '待處理'),
        ('waiting', '等待制作'),
        ('preparing', '制作中'),
        ('ready', '已就緒'),
        ('completed', '已提取'),
    ])
    
    picked_up_at = models.DateTimeField(null=True, blank=True, verbose_name="提取时间")
    picked_up_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="提取人员")
    
    # ====== 支付超时相关字段 ======
    payment_timeout = models.DateTimeField(null=True, blank=True, verbose_name="支付超时时间")
    payment_attempts = models.IntegerField(default=0)
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    payment_reminder_sent = models.BooleanField(default=False)
    
    # ====== 支付时间字段 ======
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")
    
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
    
    # ====== 優惠券和折扣相關字段 ======
    applied_coupon_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='應用優惠碼')
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='優惠券折扣金額')
    original_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='原始總價')
    
    # ====== 會員折扣相關字段（已棄用） ======
    loyalty_discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name='會員折扣率')
    loyalty_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='會員折扣金額')
    
    # ====== 積分獎勵相關字段 ======
    applied_reward_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='應用獎勵ID')
    applied_reward_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='應用獎勵名稱')
    reward_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='獎勵折扣金額')
    
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
    
    # ==================== 模板优化专用方法和属性 ====================
    
    @property
    def formatted_pickup_time(self):
        """獲取格式化的取貨時間顯示"""
        formatted_info = unified_time_service.format_pickup_time_for_order(self)
        if formatted_info:
            return {
                'text': formatted_info['text'],
                'css_class': formatted_info['css_class'],
                'icon': formatted_info['icon'],
                'estimated_time': formatted_info.get('estimated_time'),
                'remaining_minutes': formatted_info.get('remaining_minutes'),
                'is_immediate': formatted_info.get('is_immediate', False),
                'display_type': formatted_info.get('display_type', 'default'),
            }
        return {
            'text': self.get_pickup_time_display(),
            'css_class': 'text-info',
            'icon': 'fa-clock',
            'is_immediate': False,
        }
    
    @property
    def should_display_pickup_time(self):
        """是否顯示取貨時間"""
        return self.is_quick_order or self.is_beans_only()
    
    def get_order_type_summary(self):
        """獲取訂單類型摘要"""
        items = self.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        return {
            'has_coffee': has_coffee,
            'has_beans': has_beans,
            'is_beans_only': has_beans and not has_coffee,
            'is_coffee_only': has_coffee and not has_beans,
            'is_mixed_order': has_coffee and has_beans,
            'display_name': self._get_order_type_display_name(has_coffee, has_beans),
            'requires_preparation': has_coffee,
            'is_quick': self.is_quick_order,
        }
    
    def _get_order_type_display_name(self, has_coffee, has_beans):
        """獲取訂單類型顯示名稱"""
        if has_beans and not has_coffee:
            return "純咖啡豆訂單"
        elif has_coffee and not has_beans:
            return "咖啡訂單"
        elif has_coffee and has_beans:
            return "混合訂單"
        else:
            return "普通訂單"
    
    def get_payment_display_info(self):
        """獲取支付狀態顯示信息"""
        if self.status in ['completed', 'picked_up']:
            return {
                'status': 'paid',
                'title': '已完成！',
                'message': '讓我們的咖啡保持您的節奏, 同步呼吸！',
                'icon': 'fa-trophy',
                'icon_color': 'text-success',
                'icon_size': '3rem',
            }
        else:
            status_map = {
                'paid': {
                    'status': 'paid',
                    'title': '支付成功！',
                    'message': '您的訂單我們已收到，感謝您的購買！',
                    'icon': 'fa-check-circle',
                    'icon_color': 'text-success',
                    'icon_size': '3rem',
                },
                'pending': {
                    'status': 'pending',
                    'title': '支付處理中',
                    'message': '您的付款正在處理中，請稍後查看訂單狀態。',
                    'icon': 'fa-clock',
                    'icon_color': 'text-warning',
                    'icon_size': '3rem',
                    'timeout_message': f'若長時間未更新，請聯絡客服並提供訂單號碼: #{self.id}',
                },
                'payment_pending': {
                    'status': 'payment_pending',
                    'title': '付款已提交',
                    'message': '您的付款已提交，請稍候店員確認。',
                    'icon': 'fa-hourglass-half',
                    'icon_color': 'text-info',
                    'icon_size': '3rem',
                    'timeout_message': f'若長時間未更新，請聯絡客服並提供訂單號碼: #{self.id}',
                },
                'unknown': {
                    'status': 'unknown',
                    'title': '支付狀態未知',
                    'message': '無法確定您的付款狀態，請檢查訂單歷史或聯絡客服。',
                    'icon': 'fa-question-circle',
                    'icon_color': 'text-info',
                    'icon_size': '3rem',
                },
            }
            
            if self.payment_status == 'paid':
                payment_key = 'paid'
            elif self.payment_status == 'pending':
                payment_key = 'pending'
            elif self.payment_status == 'payment_pending':
                payment_key = 'payment_pending'
            else:
                payment_key = 'unknown'
            
            return status_map.get(payment_key, status_map['unknown'])
    
    def get_order_display_items(self):
        """獲取訂單顯示項目"""
        items = self.get_items_with_chinese_options()
        display_items = []
        
        for item in items:
            display_item = item.copy()
            
            if 'image' not in display_item or not display_item['image']:
                display_item['image'] = '/static/images/default-product.png'
            
            if 'price' in display_item:
                display_item['price_formatted'] = f"HK$ {float(display_item['price']):.2f}"
            
            if 'total_price' in display_item:
                display_item['total_price_formatted'] = f"HK$ {float(display_item.get('total_price', 0)):.2f}"
            
            item_type = display_item.get('type', 'unknown')
            
            if item_type == 'coffee':
                display_item['type_display'] = '咖啡'
                options = []
                if display_item.get('cup_level_cn'):
                    options.append(f"杯型: {display_item['cup_level_cn']}")
                if display_item.get('milk_level_cn'):
                    options.append(f"牛奶: {display_item['milk_level_cn']}")
                display_item['options_display'] = " | ".join(options)
            elif item_type == 'bean':
                display_item['type_display'] = '咖啡豆'
                options = []
                if display_item.get('weight_cn'):
                    options.append(f"重量: {display_item['weight_cn']}")
                elif display_item.get('weight'):
                    options.append(f"重量: {display_item['weight']}")
                if display_item.get('grinding_level_cn'):
                    options.append(f"研磨: {display_item['grinding_level_cn']}")
                display_item['options_display'] = " | ".join(options)
            else:
                display_item['type_display'] = '其他商品'
                display_item['options_display'] = ''
            
            display_items.append(display_item)
        
        return display_items
    
    @property
    def qr_code_data_url(self):
        """獲取二維碼的data URL"""
        if self.qr_code:
            return f"data:image/png;base64,{self.qr_code}"
        return ""
    
    @property
    def order_summary_info(self):
        """訂單摘要信息"""
        if self.created_at:
            created_display = unified_time_service.format_time_for_display(self.created_at)
        else:
            created_display = "時間未知"
        
        return {
            'order_id': self.id,
            'created_at': created_display,
            'total_price': f"HK$ {float(self.total_price):.2f}",
            'payment_status': self.get_payment_status_display(),
            'payment_status_badge': self.payment_status_badge,
            'is_quick_order': self.is_quick_order,
            'pickup_time_info': self.formatted_pickup_time,
        }
    
    def can_be_reused(self):
        """检查订单是否可以被重用（未支付且未过期）"""
        if self.payment_status == 'paid':
            return False
        if self.status != 'pending':
            return False
        time_threshold = timedelta(minutes=15)
        if self.created_at and timezone.now() - self.created_at > time_threshold:
            return False
        return True
    
    # ====== 支付状态管理方法 ======
    def set_payment_timeout(self, minutes=5):
        """设置支付超时时间"""
        self.payment_timeout = unified_time_service.get_hong_kong_time() + timedelta(minutes=minutes)
        self.save()
        return self.payment_timeout
    
    def is_payment_timeout(self):
        """检查是否支付超时"""
        if self.payment_timeout and unified_time_service.get_hong_kong_time() > self.payment_timeout:
            return True
        return False
    
    def increment_payment_attempts(self):
        """增加支付尝试次数"""
        self.payment_attempts += 1
        self.last_payment_attempt = timezone.now()
        self.save()
    
    def can_retry_payment(self):
        """检查是否可以重新支付"""
        if self.payment_status == 'paid':
            return False
        if self.payment_attempts >= 5:
            return False
        if self.is_payment_timeout():
            return False
        return True
    
    # ====== 订单商品处理方法 ======
    def get_items(self):
        """解析 JSON 字符串，并返回包含数值项的列表"""
        if isinstance(self.items, str):
            items = json.loads(self.items)
        else:
            items = self.items
        
        for item in items:
            try:
                if 'price' not in item:
                    try:
                        if item['type'] == 'coffee':
                            from .shop_items import CoffeeItem
                            product = CoffeeItem.objects.get(id=item['id'])
                            item['price'] = float(product.price)
                        elif item['type'] == 'bean':
                            from .shop_items import BeanItem
                            product = BeanItem.objects.get(id=item['id'])
                            weight = item.get('weight', '200g')
                            item['price'] = float(product.get_price(weight))
                        else:
                            item['price'] = 0.0
                    except Exception:
                        item['price'] = 0.0
                else:
                    item['price'] = float(item['price'])
                
                if 'quantity' not in item:
                    item['quantity'] = 1
                
                if 'total_price' not in item:
                    item['total_price'] = item['price'] * item['quantity']
                else:
                    item['total_price'] = float(item['total_price'])
                
                if 'image' not in item:
                    try:
                        if item['type'] == 'coffee':
                            from .shop_items import CoffeeItem
                            product = CoffeeItem.objects.get(id=item['id'])
                            if product.image and hasattr(product.image, 'name') and product.image.name:
                                item['image'] = get_image_url(product.image, '/static/images/default-coffee.png')
                            else:
                                item['image'] = '/static/images/default-coffee.png'
                        elif item['type'] == 'bean':
                            from .shop_items import BeanItem
                            product = BeanItem.objects.get(id=item['id'])
                            if product.image and hasattr(product.image, 'name') and product.image.name:
                                item['image'] = get_image_url(product.image, '/static/images/default-bean.png')
                            else:
                                item['image'] = '/static/images/default-bean.png'
                        else:
                            item['image'] = '/static/images/default-product.png'
                    except Exception:
                        item['image'] = '/static/images/default-product.png'
            except (TypeError, ValueError, KeyError) as e:
                item['price'] = 0.0
                item['total_price'] = 0.0
                item['image'] = '/static/images/default-product.png'
                if 'quantity' not in item:
                    item['quantity'] = 1
        return items
    
    def get_items_with_chinese_options(self):
        """返回带有中文选项的商品列表"""
        items = self.get_items()
        
        for item in items:
            item['image'] = get_product_image_url(item)
            
            item_type = item.get('type', 'unknown')
            
            if item_type == 'coffee':
                if 'cup_level' in item:
                    item['cup_level_cn'] = self.translate_option('cup_level', item['cup_level'])
                if 'milk_level' in item:
                    item['milk_level_cn'] = self.translate_option('milk_level', item['milk_level'])
                if 'weight' in item:
                    logger.debug(f"咖啡商品 {item.get('name', '未知')} 包含重量选项: {item['weight']}")
                    item.pop('weight', None)
            elif item_type == 'bean':
                if 'grinding_level' in item:
                    item['grinding_level_cn'] = self.translate_option('grinding_level', item['grinding_level'])
                if 'weight' in item:
                    item['weight_cn'] = self.translate_weight(item['weight'])
            else:
                if 'cup_level' in item:
                    item['cup_level_cn'] = self.translate_option('cup_level', item['cup_level'])
                if 'milk_level' in item:
                    item['milk_level_cn'] = self.translate_option('milk_level', item['milk_level'])
                if 'grinding_level' in item:
                    item['grinding_level_cn'] = self.translate_option('grinding_level', item['grinding_level'])
        
        return items
    
    @staticmethod
    def translate_option(option_type, value):
        """转换选项值为中文"""
        mappings = {
            'cup_level': {
                'Small': '細', 'Medium': '中', 'Large': '大',
            },
            'milk_level': {
                'Light': '少', 'Medium': '正常', 'Extra': '追加',
            },
            'grinding_level': {
                'Non': '免研磨', 'Light': '細', 'Medium': '中', 'Deep': '粗',
            },
        }
        return mappings.get(option_type, {}).get(value, value)
    
    @staticmethod
    def translate_weight(weight_value):
        """转换重量值为中文显示"""
        if not weight_value:
            return ''
        weight_str = str(weight_value).strip().lower()
        weight_mappings = {
            '200g': '200克', '500g': '500克',
            '200克': '200克', '500克': '500克',
            '200': '200克', '500': '500克',
        }
        if weight_str in weight_mappings:
            return weight_mappings[weight_str]
        for key, value in weight_mappings.items():
            if weight_str in key or key in weight_str:
                return value
        return weight_value
    
    def get_display_time(self):
        """获取格式化的预计完成时间（香港时区）"""
        if not self.estimated_ready_time:
            return None
        return unified_time_service.format_time_for_display(self.estimated_ready_time)
    
    def calculate_times_based_on_pickup_choice(self):
        """根據取貨時間選擇計算相關時間"""
        if not self.is_quick_order:
            return None, None
        
        try:
            time_info = unified_time_service.calculate_quick_order_times(self)
            if time_info:
                self.estimated_ready_time = time_info['estimated_pickup_time']
                self.latest_start_time = time_info['latest_start_time']
                logger.info(f"時間計算: 選擇{time_info['minutes_to_add']}分鐘, 預計{self.estimated_ready_time}, 最晚開始{self.latest_start_time}")
                return self.estimated_ready_time, self.latest_start_time
        except Exception as e:
            logger.error(f"計算取貨時間失敗: {str(e)}")
        
        current_time = unified_time_service.get_hong_kong_time()
        if not self.pickup_time_choice:
            self.pickup_time_choice = '5'
        try:
            minutes_to_add = int(self.pickup_time_choice)
        except (ValueError, TypeError):
            minutes_to_add = 5
        
        self.estimated_ready_time = current_time + timedelta(minutes=minutes_to_add)
        preparation_minutes = self.get_total_preparation_minutes()
        buffer_minutes = 2
        self.latest_start_time = self.estimated_ready_time - timedelta(minutes=(preparation_minutes + buffer_minutes))
        logger.info(f"備用時間計算: 選擇{minutes_to_add}分鐘, 製作{preparation_minutes}分鐘, 預計{self.estimated_ready_time}, 最晚開始{self.latest_start_time}")
        return self.estimated_ready_time, self.latest_start_time
    
    def get_total_preparation_minutes(self):
        """計算總製作時間（分鐘）"""
        items = self.get_items()
        coffee_count = 0
        for item in items:
            if item.get('type') == 'coffee':
                coffee_count += item.get('quantity', 1)
        if coffee_count == 0:
            return 0
        from ..queue_manager_refactored import CoffeeQueueManager
        return CoffeeQueueManager.get_preparation_time(coffee_count)
    
    def should_be_in_queue_by_now(self):
        """檢查是否應該已經在隊列中"""
        current_time = unified_time_service.get_hong_kong_time()
        if not self.latest_start_time:
            return True
        return current_time >= self.latest_start_time
    
    def get_pickup_time_display(self):
        """獲取消費時間顯示文本"""
        formatted_info = unified_time_service.format_pickup_time_for_order(self)
        if formatted_info:
            return formatted_info['text']
        if not self.pickup_time_choice:
            return "5分鐘後"
        choice_map = {
            '5': '5分鐘後', '10': '10分鐘後', '15': '15分鐘後',
            '20': '20分鐘後', '30': '30分鐘後',
        }
        return choice_map.get(self.pickup_time_choice, '5分鐘後')
    
    def get_status_display(self):
        """获取订单状态显示文本"""
        status_map = {
            'pending': '待處理', 'waiting': '等待制作',
            'preparing': '製作中', 'ready': '已就緒',
            'completed': '已完成', 'cancelled': '已取消',
        }
        return status_map.get(self.status, self.status)
    
    def get_payment_status_display(self):
        """获取支付状态显示文本"""
        status_map = {
            'pending': '待支付', 'paid': '已支付',
            'cancelled': '已取消', 'expired': '已过期',
        }
        return status_map.get(self.payment_status, self.payment_status)
    
    def has_coffee(self):
        """检查订单是否包含咖啡"""
        items = self.get_items()
        return any(item.get('type') == 'coffee' for item in items)
    
    def is_beans_only(self):
        """检查订单是否只包含咖啡豆"""
        items = self.get_items()
        has_beans = any(item.get('type') == 'bean' for item in items)
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        return has_beans and not has_coffee
    
    def calculate_estimated_ready_time(self):
        """根据订单中的商品计算预计就绪时间"""
        items = self.get_items()
        total_coffee_quantity = 0
        has_coffee = False
        has_beans = False
        
        for item in items:
            if item['type'] == 'coffee':
                has_coffee = True
                total_coffee_quantity += item['quantity']
            elif item['type'] == 'bean':
                has_beans = True
        
        if has_beans and not has_coffee:
            logger.info("纯咖啡豆订单，不设置预计时间")
            return None
        if not has_coffee and not has_beans:
            logger.info("无商品订单，不设置预计时间")
            return None
        
        if total_coffee_quantity == 1:
            preparation_minutes = 5
        else:
            preparation_minutes = 5 + (total_coffee_quantity - 1) * 3
        
        import random
        fluctuation = random.randint(-1, 1)
        total_minutes = max(1, preparation_minutes + fluctuation)
        
        base_time = unified_time_service.get_hong_kong_time()
        estimated_time = base_time + timedelta(minutes=total_minutes)
        logger.info(f"计算制作时间: {total_minutes}分钟, 预计时间: {estimated_time}")
        return estimated_time
    
    def get_preparation_time_display(self):
        """获取制作时间显示文本"""
        items = self.get_items()
        total_coffee_quantity = 0
        has_coffee = False
        has_beans = False
        
        for item in items:
            if item['type'] == 'coffee':
                has_coffee = True
                total_coffee_quantity += item['quantity']
            elif item['type'] == 'bean':
                has_beans = True
        
        if has_beans and not has_coffee:
            return "随时可取"
        if total_coffee_quantity == 1:
            return "预计制作时间: 5分钟"
        else:
            preparation_minutes = 5 + (total_coffee_quantity - 1) * 3
            return f"预计制作时间: {preparation_minutes}分钟"
    
    def get_order_type_display(self):
        """获取订单类型显示文本"""
        items = self.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        if has_beans and not has_coffee:
            return "純咖啡豆訂單"
        elif has_coffee and not has_beans:
            return "咖啡訂單 - 需要制作"
        elif has_coffee and has_beans:
            return "混合訂單 - 咖啡需要制作"
        else:
            return "普通訂單"
    
    def should_show_preparation_time(self):
        """判断是否应该显示制作时间"""
        items = self.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        return has_coffee
    
    def get_remaining_minutes(self):
        """获取剩余分钟数"""
        return unified_time_service.get_remaining_minutes(self.estimated_ready_time)
    
    def is_ready(self):
        """检查订单是否已完成制作"""
        from ..order_status_manager import OrderStatusManager
        manager = OrderStatusManager(self)
        return manager.order.status in ['ready', 'completed']
    
    def get_payment_status_for_display(self):
        """获取支付状态显示信息"""
        status_map = {
            'pending': {'text': '待支付', 'badge': 'warning', 'icon': 'clock'},
            'paid': {'text': '已支付', 'badge': 'success', 'icon': 'check-circle'},
            'cancelled': {'text': '已取消', 'badge': 'danger', 'icon': 'times-circle'},
            'expired': {'text': '已过期', 'badge': 'secondary', 'icon': 'hourglass-end'},
        }
        return status_map.get(self.payment_status, {
            'text': self.payment_status, 'badge': 'info', 'icon': 'question-circle',
        })
    
    @property
    def payment_status_badge(self):
        """支付状态对应的Bootstrap徽章颜色"""
        badge_map = {
            'pending': 'warning', 'paid': 'success',
            'cancelled': 'danger', 'expired': 'secondary',
        }
        return badge_map.get(self.payment_status, 'info')
    
    # 兼容性属性
    @property
    def created_on(self):
        """弃用字段：使用 created_at 替代"""
        warnings.warn("OrderModel.created_on 字段已弃用，请使用 created_at 字段。", DeprecationWarning, stacklevel=2)
        return self.created_at
    
    @created_on.setter
    def created_on(self, value):
        warnings.warn("OrderModel.created_on 字段已弃用，请使用 created_at 字段。", DeprecationWarning, stacklevel=2)
        self.created_at = value
    
    @property
    def cup_size(self):
        """弃用字段：返回空字符串"""
        warnings.warn("OrderModel.cup_size 字段已弃用，该字段未使用。", DeprecationWarning, stacklevel=2)
        return ''
    
    @property
    def pickup_time(self):
        """弃用字段：通过 estimated_ready_time 计算"""
        warnings.warn("OrderModel.pickup_time 字段已弃用，请使用 estimated_ready_time 字段。", DeprecationWarning, stacklevel=2)
        if self.estimated_ready_time:
            return self.estimated_ready_time.strftime('%H:%M')
        return ''
    
    def save(self, *args, **kwargs):
        """保存订单，处理取餐码、二维码和预计时间"""
        try:
            logger.info(f"=== 开始保存订单 {self.id or '新订单'} ===")
            
            if not self.pickup_code or self.pickup_code == '':
                logger.info("为新订单生成取餐码")
                self.pickup_code = self.generate_unique_pickup_code()
                logger.info(f"生成取餐码: {self.pickup_code}")
            
            self.updated_at = timezone.now()
            
            if not self.pickup_code:
                logger.info("为新订单生成取餐码")
                self.pickup_code = self.generate_unique_pickup_code()
                logger.info(f"生成取餐码: {self.pickup_code}")
            
            if self.payment_status == 'paid' and not self.estimated_ready_time and self.has_coffee():
                logger.info("支付成功，计算预计就绪时间")
                self.estimated_ready_time = self.calculate_estimated_ready_time()
                logger.info(f"预计就绪时间: {self.estimated_ready_time}")
            
            if not self.qr_code and self.pickup_code:
                logger.info("生成二维码数据")
                self.qr_code = self.generate_qr_code_data()
            
            if self.payment_status == 'paid' and self.status == 'pending':
                logger.info("更新订单状态为 waiting（等待制作）")
                self.status = 'waiting'
            
            super().save(*args, **kwargs)
            logger.info(f"订单保存成功: {self.id}")
            
            # 队列处理逻辑
            if self.status == 'waiting' and self.payment_status == 'paid':
                from ..order_status_manager import OrderStatusManager
                manager = OrderStatusManager(self)
                
                if manager.should_add_to_queue():
                    logger.info(f"订单 {self.id} 符合加入队列条件，尝试加入队列")
                    try:
                        from ..queue_manager_refactored import CoffeeQueueManager
                        from .queue import CoffeeQueue
                        queue_manager = CoffeeQueueManager()
                        
                        existing_queue_item = CoffeeQueue.objects.filter(order=self).first()
                        if existing_queue_item:
                            logger.info(f"订单 {self.id} 已在队列中，位置: {existing_queue_item.position}")
                        else:
                            queue_item = queue_manager.add_order_to_queue(self)
                            if queue_item:
                                if isinstance(queue_item, dict):
                                    position = queue_item.get('position', 0)
                                    logger.info(f"订单 {self.id} 已加入制作队列，位置: {position}")
                                else:
                                    logger.info(f"订单 {self.id} 已加入制作队列，位置: {queue_item.position}")
                            else:
                                logger.error(f"订单 {self.id} 加入队列失败")
                    except Exception as e:
                        logger.error(f"队列处理失败: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"OrderModel保存错误: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            if 'pickup_code_key' in str(e):
                logger.info("检测到取餐码重复，重新生成并重试")
                self.pickup_code = self.generate_unique_pickup_code()
                super().save(*args, **kwargs)
            else:
                raise e
    
    def generate_unique_pickup_code(self):
        """生成唯一的取餐码 - 4位数字版本"""
        import secrets
        import string
        import time
        import uuid
        
        max_attempts = 100
        
        # 方法1：使用时间戳 + 随机数
        for attempt in range(max_attempts):
            timestamp_part = str(int(time.time() * 1000))[-2:]
            random_part = ''.join(secrets.choice(string.digits) for _ in range(2))
            code = timestamp_part + random_part
            
            if not OrderModel.objects.filter(pickup_code=code).exists():
                logger.info(f"生成时间戳取餐码: {code}")
                return code
        
        # 方法2：纯随机4位数字
        for attempt in range(max_attempts):
            code = ''.join(secrets.choice(string.digits) for _ in range(4))
            if not OrderModel.objects.filter(pickup_code=code).exists():
                logger.info(f"生成随机取餐码: {code}")
                return code
        
        # 方法3：UUID简化版
        for attempt in range(max_attempts):
            uuid_int = uuid.uuid4().int
            code = str(uuid_int % 10000).zfill(4)
            if not OrderModel.objects.filter(pickup_code=code).exists():
                logger.info(f"使用UUID取餐码: {code}")
                return code
        
        # 方法4：顺序生成
        last_code = OrderModel.objects.order_by('-id').first()
        if last_code and last_code.pickup_code:
            try:
                last_num = int(last_code.pickup_code)
                for i in range(1, 100):
                    code = str((last_num + i) % 10000).zfill(4)
                    if not OrderModel.objects.filter(pickup_code=code).exists():
                        logger.info(f"使用顺序取餐码: {code}")
                        return code
            except ValueError:
                pass
        
        code = '1234'
        logger.warning(f"所有取餐码生成方法都失败，使用默认值: {code}")
        return code
    
    def generate_qr_code_data(self):
        """生成二维码数据"""
        logger.info(f"开始生成二维码，订单: {self.id}")
        
        if not self.pickup_code:
            logger.info(f"订单 {self.id} 没有取餐码，调用 save() 生成")
            self.save()
        
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
            logger.info(f"订单 {self.id} 二维码生成成功")
            
            return qr_code_data
            
        except Exception as e:
            logger.error(f"生成二维码失败: {str(e)}")
            return ''
    
    def clean(self):
        """验证模型数据"""
        super().clean()
        if self.pickup_code == '0000':
            raise ValidationError({'pickup_code': '取餐码不能为0000'})
        if OrderModel.objects.exclude(id=self.id).filter(pickup_code=self.pickup_code).exists():
            raise ValidationError({'pickup_code': '取餐码必须唯一'})


def get_product_image_url(item_data):
    """
    根据商品数据获取正确的图片URL
    
    MEDIA_URL 已根據環境動態設置（settings.py），image.url 在所有環境中都返回正確的路徑。
    """
    if item_data.get('image'):
        return item_data['image']
    
    try:
        if item_data.get('type') == 'coffee':
            from .shop_items import CoffeeItem
            coffee = CoffeeItem.objects.get(id=item_data['id'])
            if coffee.image and hasattr(coffee.image, 'name') and coffee.image.name:
                return get_image_url(coffee.image, '/static/images/default-coffee.png')
            return '/static/images/default-coffee.png'
        elif item_data.get('type') == 'bean':
            from .shop_items import BeanItem
            bean = BeanItem.objects.get(id=item_data['id'])
            if bean.image and hasattr(bean.image, 'name') and bean.image.name:
                return get_image_url(bean.image, '/static/images/default-bean.png')
            return '/static/images/default-bean.png'
    except Exception:
        pass
    
    return '/static/images/default-product.png'
