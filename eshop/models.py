# eshop/models.py
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

logger = logging.getLogger(__name__)


# Shop Item
class CoffeeItem(models.Model):
    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    image = models.ImageField(upload_to='coffee_images/')
    image_index = models.ImageField(upload_to='coffee_images/index/', blank=True, null=True, verbose_name='首页图片')
    price = models.DecimalField(max_digits=5, decimal_places=2)
    origin = models.CharField(max_length=30, blank=True)
    flavor = models.TextField(max_length=200, blank=True)
    list_date = models.DateTimeField(default=timezone.now,blank=True)
    # Cup level choices
    CUP_LEVEL_CHOICES = [
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
    ]
    cup_level = models.CharField(max_length=10, choices=CUP_LEVEL_CHOICES, default='Medium')
    # Milk level choices
    MILK_LEVEL_CHOICES = [
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Extra', 'Extra'),
    ]
    milk_level = models.CharField(max_length=10, choices=MILK_LEVEL_CHOICES, default='Medium')
    is_published = models.BooleanField(default=True)
    is_shop_hot_item = models.BooleanField(default=False)
    # 新增排序字段
    hot_item_order = models.PositiveIntegerField(default=0, verbose_name='热门商品排序', help_text='数字越小显示越靠前')

    def __str__(self):
        return self.name

    # 获取图片方法 - 优先返回首页图片
    def get_index_image(self):
        """获取首页专用图片，如果没有则返回默认图片"""
        if self.image_index:
            return self.image_index.url
        elif self.image:
            return self.image.url
        else:
            return '/static/images/default-coffee-index.png'

    def get_detail_image(self):
        """获取详情页图片 - 修复版本"""
        # 检查 image 字段是否存在且有文件
        if self.image and hasattr(self.image, 'url'):
            try:
                # 尝试获取URL，如果文件不存在会抛出异常
                return self.image.url
            except (ValueError, AttributeError):
                # 文件不存在，返回默认图片
                return '/static/images/default-coffee-detail.png'
        else:
            # 没有图片，返回默认图片
            return '/static/images/default-coffee-detail.png'

    class Meta:
        verbose_name_plural = "Coffee"
        ordering = []


class BeanItem(models.Model):
    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    image = models.ImageField(upload_to='bean_images/')
    image_index = models.ImageField(upload_to='bean_images/index/', blank=True, null=True, verbose_name='首页图片')
    price_200g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_500g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    origin = models.CharField(max_length=50, blank=True)
    
    GRINDING_LEVEL_CHOICES = [
        ('Non', '免研磨'),
        ('Light', '細研磨'),
        ('Medium', '中研磨'),
        ('Deep', '粗研磨'),
    ]
    grinding_level = models.CharField(max_length=10, choices=GRINDING_LEVEL_CHOICES, default='Non') 
    flavor = models.TextField(max_length=200, blank=True)
    list_date = models.DateTimeField(default=timezone.now,blank=True)
    is_published = models.BooleanField(default=True)
    is_shop_hot_item = models.BooleanField(default=False)
    # 新增排序字段
    hot_item_order = models.PositiveIntegerField(default=0, verbose_name='热门商品排序', help_text='数字越小显示越靠前')

    def __str__(self):
        return self.name
    
    # 获取图片方法 - 优先返回首页图片
    def get_index_image(self):
        """获取首页专用图片，如果没有则返回默认图片"""
        if self.image_index:
            return self.image_index.url
        elif self.image:
            return self.image.url
        else:
            return '/static/images/default-bean-index.png'

    def get_detail_image(self):
        """获取详情页图片 - 修复版本"""
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except (ValueError, AttributeError):
                return '/static/images/default-bean-detail.png'
        else:
            return '/static/images/default-bean-detail.png'
    
    class Meta:
        verbose_name_plural = "Bean"
        ordering = []
    
    # 获取价格的方法
    def get_price(self, weight):
        if weight == '200g':
            return self.price_200g
        elif weight == '500g':
            return self.price_500g
        return self.price_200g  # 默认返回200克价格


# Session store cart items
class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    product_type = models.CharField(max_length=10)  # 'coffee' or 'bean'
    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    cup_level = models.CharField(max_length=10, blank=True, null=True)
    milk_level = models.CharField(max_length=10, blank=True, null=True)
    grinding_level = models.CharField(max_length=10, blank=True, null=True)
    weight = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product_type', 'product_id', 'cup_level', 'milk_level', 'grinding_level', 'weight')
        
    def __str__(self):
        return f"{self.user.username}'s {self.product_type} item"


    
    def get_items(self):
        """Parse the JSON string and return the list of items with numeric values."""
        # 延迟导入在需要使用, 以避免循环导入
        from .models import CoffeeItem, BeanItem

        if isinstance(self.items, str):
            items = json.loads(self.items)
        else:
            items = self.items  # If it's already a list
            
        # Convert prices to floats and ensure image URLs are present
        for item in items:
            try:
                # 修复：确保 price 键存在
                if 'price' not in item:
                    # 尝试从产品获取价格
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                            item['price'] = float(product.price)
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                            # 根据重量获取价格
                            weight = item.get('weight', '200g')
                            item['price'] = float(product.get_price(weight))
                        else:
                            item['price'] = 0.0
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist, KeyError):
                        item['price'] = 0.0
                else:
                    # Convert price to float
                    item['price'] = float(item['price'])
                
                # 确保 quantity 存在
                if 'quantity' not in item:
                    item['quantity'] = 1
                
                # Calculate total price if not present
                if 'total_price' not in item:
                    item['total_price'] = item['price'] * item['quantity']
                else:
                    item['total_price'] = float(item['total_price'])
                
                # Ensure image URL exists
                if 'image' not in item:
                    # Try to get image from product
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                        else:
                            product = None
                            
                        if product:
                            item['image'] = product.image.url
                    except:
                        item['image'] = '/static/images/default-product.png'
            except (TypeError, ValueError, KeyError) as e:
                print(f"Error processing cart item: {item}, error: {e}")
                item['price'] = 0.0
                item['total_price'] = 0.0
                item['image'] = '/static/images/default-product.png'
                if 'quantity' not in item:
                    item['quantity'] = 1
        return items


    def get_items_display(self):
        """Format the items for display."""
        items = self.get_items()
        display_text = []
        for item in items:
            raw_price = item['price']
            if isinstance(raw_price, float):
                price_str = f"{raw_price:.2f}"
            else:
                price_str = str(raw_price)
                
            if '.00' in price_str:
                price_str = price_str.replace('.00', '')
                
            item_text = f"{item['name']} (Qty: {item['quantity']}, Price: ${price_str})"
            if item['type'] == 'coffee':
                item_text += f", Cup: {item['cup_level']}, Milk: {item['milk_level']}"
            elif item['type'] == 'bean':
                item_text += f", Grinding: {item['grinding_level']}"
            display_text.append(item_text)
        return "\n".join(display_text)
    

    def clean(self):
        """Validate the items field before saving."""
        if not isinstance(self.items, (str, list)):
            raise ValidationError("Items must be a JSON string or a list.")
        if isinstance(self.items, list):
            self.items = json.dumps(self.items)  # Convert list to JSON string

    class Meta:
        verbose_name_plural = "Order"





class OrderModel(models.Model):
    # ====== 基础字段 ======
    # created_on 字段已移除，使用 created_at 替代
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=80, blank=True, null=True, default='')
    phone = models.CharField(max_length=12, blank=True, null=True)
    
    # ====== 支付状态字段 ======
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
    
    # ====== 弃用字段：pickup_time 和 cup_size (可计算，移除) ======
    # pickup_time 字段已移除，可通过 estimated_ready_time 计算
    # cup_size 字段已移除，未使用
    
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
        ('completed', '已提取')
    ])
    
    picked_up_at = models.DateTimeField(null=True, blank=True, verbose_name="提取时间")
    picked_up_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="提取人员")
    
    # ====== 支付超时相关字段 ======
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


    # ==================== 新增：模板优化专用方法和属性 ====================
    
    @property
    def formatted_pickup_time(self):
        """
        獲取格式化的取貨時間顯示
        返回包含文本和CSS類的字典 - 使用統一格式化函數
        """
        formatted_info = unified_time_service.format_pickup_time_for_order(self)
        if formatted_info:
            return {
                'text': formatted_info['text'],
                'css_class': formatted_info['css_class'],
                'icon': formatted_info['icon'],
                'estimated_time': formatted_info.get('estimated_time'),
                'remaining_minutes': formatted_info.get('remaining_minutes'),
                'is_immediate': formatted_info.get('is_immediate', False),
                'display_type': formatted_info.get('display_type', 'default')
            }
        
        # 默認返回
        return {
            'text': self.get_pickup_time_display(),
            'css_class': 'text-info',
            'icon': 'fa-clock',
            'is_immediate': False
        }


    @property
    def should_display_pickup_time(self):
        """
        是否顯示取貨時間
        快速訂單和純咖啡豆訂單顯示，其他不顯示
        """
        return self.is_quick_order or self.is_beans_only()

    def get_order_type_summary(self):
        """
        獲取訂單類型摘要 - 增強版本
        返回結構化的訂單類型信息
        """
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
            'is_quick': self.is_quick_order
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
        """
        獲取支付狀態顯示信息
        返回結構化的支付狀態信息
        """
        status_map = {
            'paid': {
                'status': 'paid',
                'title': '支付成功！',
                'message': '您的訂單我們已收到，感謝您的購買！',
                'icon': 'fa-check-circle',
                'icon_color': 'text-success',
                'icon_size': '3rem'
            },
            'pending': {
                'status': 'pending',
                'title': '支付處理中',
                'message': '您的付款正在處理中，請稍後查看訂單狀態。',
                'icon': 'fa-clock',
                'icon_color': 'text-warning',
                'icon_size': '3rem',
                'timeout_message': f'若長時間未更新，請聯絡客服並提供訂單號碼: #{self.id}'
            },
            'unknown': {
                'status': 'unknown',
                'title': '支付狀態未知',
                'message': '無法確定您的付款狀態，請檢查訂單歷史或聯絡客服。',
                'icon': 'fa-question-circle',
                'icon_color': 'text-info',
                'icon_size': '3rem'
            }
        }
        
        # 確定支付狀態
        if self.payment_status == 'paid':
            payment_key = 'paid'
        elif self.payment_status == 'pending':
            payment_key = 'pending'
        else:
            payment_key = 'unknown'
        
        return status_map.get(payment_key, status_map['unknown'])

    def get_order_display_items(self):
        """
        獲取訂單顯示項目
        返回結構化的商品列表，包含中文選項和格式化信息
        """
        items = self.get_items_with_chinese_options()
        display_items = []
        
        for item in items:
            display_item = item.copy()
            
            # 確保圖片URL正確
            if 'image' not in display_item or not display_item['image']:
                display_item['image'] = '/static/images/default-product.png'
            
            # 格式化價格
            if 'price' in display_item:
                display_item['price_formatted'] = f"HK$ {float(display_item['price']):.2f}"
            
            if 'total_price' in display_item:
                display_item['total_price_formatted'] = f"HK$ {float(display_item.get('total_price', 0)):.2f}"
            
            # 添加商品類型顯示
            item_type = display_item.get('type', 'unknown')
            
            if item_type == 'coffee':
                display_item['type_display'] = '咖啡'
                # 構建設置顯示 - 只顯示杯型和牛奶選項
                options = []
                if display_item.get('cup_level_cn'):
                    options.append(f"杯型: {display_item['cup_level_cn']}")
                if display_item.get('milk_level_cn'):
                    options.append(f"牛奶: {display_item['milk_level_cn']}")
                display_item['options_display'] = " | ".join(options)
                
            elif item_type == 'bean':
                display_item['type_display'] = '咖啡豆'
                # 構建設置顯示 - 顯示重量和研磨選項
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
        """
        獲取二維碼的data URL
        用於模板中直接顯示二維碼圖片
        """
        if self.qr_code:
            return f"data:image/png;base64,{self.qr_code}"
        return ""

    @property
    def order_summary_info(self):
        """
        訂單摘要信息
        用於訂單確認頁面的頂部顯示
        """
        # 格式化創建時間
        created_at = self.created_at
        if created_at.tzinfo is None:
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            created_at = timezone.make_aware(created_at, hk_tz)
        
        created_display = created_at.strftime('%Y-%m-%d %H:%M')
        
        return {
            'order_id': self.id,
            'created_at': created_display,
            'total_price': f"HK$ {float(self.total_price):.2f}",
            'payment_status': self.get_payment_status_display(),
            'payment_status_badge': self.payment_status_badge,
            'is_quick_order': self.is_quick_order,
            'pickup_time_info': self.formatted_pickup_time
        }

    # ==================== 現有方法保持不變 ====================
    
    def can_be_reused(self):
        """
        检查订单是否可以被重用（未支付且未过期）
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # 如果订单已经支付，不能重用
        if self.payment_status == 'paid':
            return False
            
        # 如果订单状态不是pending，不能重用
        if self.status != 'pending':
            return False
            
        # 检查订单是否在15分钟内创建（防止重用过旧的订单）
        time_threshold = timedelta(minutes=15)
        if self.created_at and timezone.now() - self.created_at > time_threshold:
            return False
            
        return True
        
    
    # ====== 支付状态管理方法 ======
    def set_payment_timeout(self, minutes=5):
        """设置支付超时时间"""
        from django.utils import timezone
        self.payment_timeout = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()
        return self.payment_timeout
    
    def is_payment_timeout(self):
        """检查是否支付超时"""
        from django.utils import timezone
        if self.payment_timeout and timezone.now() > self.payment_timeout:
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
        if self.payment_attempts >= 5:  # 最大尝试次数
            return False
        if self.is_payment_timeout():
            return False
        return True
    
    # ====== 订单商品处理方法 ======
    def get_items(self):
        """解析 JSON 字符串，并返回包含数值项的列表"""
        from .models import CoffeeItem, BeanItem
        
        if isinstance(self.items, str):
            items = json.loads(self.items)
        else:
            items = self.items
            
        for item in items:
            try:
                # 确保 price 键存在
                if 'price' not in item:
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                            item['price'] = float(product.price)
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                            weight = item.get('weight', '200g')
                            item['price'] = float(product.get_price(weight))
                        else:
                            item['price'] = 0.0
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist, KeyError):
                        item['price'] = 0.0
                else:
                    item['price'] = float(item['price'])
                
                # 确保 quantity 存在
                if 'quantity' not in item:
                    item['quantity'] = 1
                
                # Calculate total price if not present
                if 'total_price' not in item:
                    item['total_price'] = item['price'] * item['quantity']
                else:
                    item['total_price'] = float(item['total_price'])
                
                # Ensure image URL exists
                if 'image' not in item:
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                        else:
                            product = None
                            
                        if product:
                            item['image'] = product.image.url
                        else:
                            item['image'] = '/static/images/default-product.png'
                    except:
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
            # 确保图片路径正确
            item['image'] = get_product_image_url(item)
            
            # 根据商品类型处理不同的选项
            item_type = item.get('type', 'unknown')
            
            if item_type == 'coffee':
                # 咖啡商品：只处理杯型和牛奶选项
                if 'cup_level' in item:
                    item['cup_level_cn'] = self.translate_option('cup_level', item['cup_level'])
                if 'milk_level' in item:
                    item['milk_level_cn'] = self.translate_option('milk_level', item['milk_level'])
                # 咖啡商品不应该有重量选项，确保不显示
                if 'weight' in item:
                    # 记录调试信息但不显示重量选项
                    logger.debug(f"咖啡商品 {item.get('name', '未知')} 包含重量选项: {item['weight']}")
                    # 移除重量选项，避免前端显示
                    item.pop('weight', None)
                    
            elif item_type == 'bean':
                # 咖啡豆商品：处理研磨选项和重量
                if 'grinding_level' in item:
                    item['grinding_level_cn'] = self.translate_option('grinding_level', item['grinding_level'])
                if 'weight' in item:
                    # 将重量转换为中文显示
                    item['weight_cn'] = self.translate_weight(item['weight'])
            else:
                # 其他类型商品：处理所有可能的选项
                if 'cup_level' in item:
                    item['cup_level_cn'] = self.translate_option('cup_level', item['cup_level'])
                if 'milk_level' in item:
                    item['milk_level_cn'] = self.translate_option('milk_level', item['milk_level'])
                if 'grinding_level' in item:
                    item['grinding_level_cn'] = self.translate_option('grinding_level', item['grinding_level'])
        
        return items
    
    @staticmethod
    def translate_option(option_type, value):
        """静态方法：转换选项值为中文"""
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
        """静态方法：转换重量值为中文显示"""
        if not weight_value:
            return ''
        
        weight_str = str(weight_value).strip().lower()
        
        # 重量转换映射
        weight_mappings = {
            '200g': '200克',
            '500g': '500克',
            '200克': '200克',
            '500克': '500克',
            '200': '200克',
            '500': '500克',
        }
        
        # 尝试精确匹配
        if weight_str in weight_mappings:
            return weight_mappings[weight_str]
        
        # 尝试模糊匹配
        for key, value in weight_mappings.items():
            if weight_str in key or key in weight_str:
                return value
        
        # 默认返回原值
        return weight_value
    
    def get_display_time(self):
        """获取格式化的预计完成时间（香港时区）"""
        if not self.estimated_ready_time:
            return None
        return unified_time_service.format_time_for_display(self.estimated_ready_time)
    

    def calculate_times_based_on_pickup_choice(self):
        """根據取貨時間選擇計算相關時間 - 使用統一時間服務"""
        # 只有快速訂單才需要重新計算
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
        
        # 備用計算邏輯
        current_time = unified_time_service.get_hong_kong_time()
        
        # 確保有取貨時間選擇
        if not self.pickup_time_choice:
            self.pickup_time_choice = '5'
        
        try:
            minutes_to_add = int(self.pickup_time_choice)
        except (ValueError, TypeError):
            minutes_to_add = 5
        
        self.estimated_ready_time = current_time + timedelta(minutes=minutes_to_add)
        
        # 計算最晚開始製作時間
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
            return 0  # 純咖啡豆訂單無需製作
        
        # 使用統一的製作時間計算（與queue_manager一致）
        from .queue_manager_refactored import CoffeeQueueManager
        return CoffeeQueueManager.get_preparation_time_compatible(coffee_count)
    
    def should_be_in_queue_by_now(self):
        """檢查是否應該已經在隊列中（基於最晚開始時間）"""
        current_time = unified_time_service.get_hong_kong_time()
        
        if not self.latest_start_time:
            return True  # 如果沒有最晚開始時間，立即加入隊列
        
        return current_time >= self.latest_start_time
    

    def get_pickup_time_display(self):
        """獲取消費時間顯示文本 - 使用統一的格式化函數"""
        formatted_info = unified_time_service.format_pickup_time_for_order(self)
        if formatted_info:
            return formatted_info['text']
        
        # 備用邏輯
        if not self.pickup_time_choice:
            return "5分鐘後"
        
        choice_map = {
            '5': '5分鐘後',
            '10': '10分鐘後',
            '15': '15分鐘後',
            '20': '20分鐘後',
            '30': '30分鐘後',
        }
        return choice_map.get(self.pickup_time_choice, '5分鐘後')




    def get_status_display(self):
        """获取订单状态显示文本"""
        status_map = {
            'pending': '待處理',
            'waiting': '等待制作',
            'preparing': '製作中', 
            'ready': '已就緒',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        return status_map.get(self.status, self.status)
    
    def get_payment_status_display(self):
        """获取支付状态显示文本"""
        status_map = {
            'pending': '待支付',
            'paid': '已支付',
            'cancelled': '已取消',
            'expired': '已过期'
        }
        return status_map.get(self.payment_status, self.payment_status)
    
    def has_coffee(self):
        """检查订单是否包含咖啡"""
        items = self.get_items()
        return any(item.get('type') == 'coffee' for item in items)
    
    # 确保 is_beans_only 方法存在（应该已经有了，检查拼写）
    def is_beans_only(self):
        """检查订单是否只包含咖啡豆 - 明确版本"""
        items = self.get_items()
        has_beans = any(item.get('type') == 'bean' for item in items)
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        return has_beans and not has_coffee
    
    # 确保 calculate_estimated_ready_time 方法正确处理纯咖啡豆订单
    def calculate_estimated_ready_time(self):
        """根据订单中的商品计算预计就绪时间"""
        from datetime import timedelta
        import random
        
        # 解析订单项
        items = self.get_items()
        
        # 计算咖啡总数量
        total_coffee_quantity = 0
        has_coffee = False
        has_beans = False
        
        for item in items:
            if item['type'] == 'coffee':
                has_coffee = True
                total_coffee_quantity += item['quantity']
            elif item['type'] == 'bean':
                has_beans = True
        
        # 如果只有咖啡豆，不需要预计就绪时间
        if has_beans and not has_coffee:
            logger.info("纯咖啡豆订单，不设置预计时间")
            return None
        
        # 如果没有任何商品，返回None
        if not has_coffee and not has_beans:
            logger.info("无商品订单，不设置预计时间")
            return None
        
        # 计算制作时间
        if total_coffee_quantity == 1:
            preparation_minutes = 5  # 单一杯5分钟
        else:
            preparation_minutes = 5 + (total_coffee_quantity - 1) * 3  # 之后每杯递增3分钟
        
        # 添加随机浮动（±1分钟）
        fluctuation = random.randint(-1, 1)
        total_minutes = max(1, preparation_minutes + fluctuation)
        
        # 使用香港时区当前时间作为基准
        base_time = unified_time_service.get_hong_kong_time()
        estimated_time = base_time + timedelta(minutes=total_minutes)
        logger.info(f"计算制作时间: {total_minutes}分钟, 预计时间: {estimated_time}")
        
        return estimated_time
    
    def get_preparation_time_display(self):
        """获取制作时间显示文本 - 修复版本"""
        items = self.get_items()
        
        # 计算咖啡总数量
        total_coffee_quantity = 0
        has_coffee = False
        has_beans = False
        
        for item in items:
            if item['type'] == 'coffee':
                has_coffee = True
                total_coffee_quantity += item['quantity']
            elif item['type'] == 'bean':
                has_beans = True
        
        # 如果只有咖啡豆，返回空字符串
        if has_beans and not has_coffee:
            return "随时可取"
        
        # 计算制作时间
        if total_coffee_quantity == 1:
            return "预计制作时间: 5分钟"
        else:
            preparation_minutes = 5 + (total_coffee_quantity - 1) * 3
            return f"预计制作时间: {preparation_minutes}分钟"
    
    def get_order_type_display(self):
        """获取订单类型显示文本 - 修正：純咖啡豆訂單特別標註"""
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
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        # 只有包含咖啡的订单才显示制作时间
        return has_coffee
    
    def get_remaining_minutes(self):
        """获取剩余分钟数"""
        return unified_time_service.get_remaining_minutes(self.estimated_ready_time)
    
    def is_ready(self):
        """检查订单是否已完成制作"""
        # 使用 OrderStatusManager 来检查状态
        from .order_status_manager import OrderStatusManager
        manager = OrderStatusManager(self)
        return manager.order.status in ['ready', 'completed']
    
    def get_payment_status_for_display(self):
        """
        获取支付状态显示信息（新增）
        返回支付状态和对应的样式
        """
        status_map = {
            'pending': {
                'text': '待支付',
                'badge': 'warning',
                'icon': 'clock'
            },
            'paid': {
                'text': '已支付',
                'badge': 'success',
                'icon': 'check-circle'
            },
            'cancelled': {
                'text': '已取消',
                'badge': 'danger',
                'icon': 'times-circle'
            },
            'expired': {
                'text': '已过期',
                'badge': 'secondary',
                'icon': 'hourglass-end'
            }
        }
        
        status_info = status_map.get(self.payment_status, {
            'text': self.payment_status,
            'badge': 'info',
            'icon': 'question-circle'
        })
        
        return status_info
    
    @property
    def payment_status_badge(self):
        """支付状态对应的Bootstrap徽章颜色（属性）"""
        badge_map = {
            'pending': 'warning',
            'paid': 'success',
            'cancelled': 'danger',
            'expired': 'secondary'
        }
        return badge_map.get(self.payment_status, 'info')
    
    # 兼容性属性（用于弃用字段）
    @property
    def created_on(self):
        """弃用字段：使用 created_at 替代"""
        warnings.warn(
            "OrderModel.created_on 字段已弃用，请使用 created_at 字段。",
            DeprecationWarning,
            stacklevel=2
        )
        return self.created_at
    
    @created_on.setter
    def created_on(self, value):
        """弃用字段设置器：同步到 created_at"""
        warnings.warn(
            "OrderModel.created_on 字段已弃用，请使用 created_at 字段。",
            DeprecationWarning,
            stacklevel=2
        )
        self.created_at = value
    
    @property
    def cup_size(self):
        """弃用字段：返回空字符串"""
        warnings.warn(
            "OrderModel.cup_size 字段已弃用，该字段未使用。",
            DeprecationWarning,
            stacklevel=2
        )
        return ''
    
    @property
    def pickup_time(self):
        """弃用字段：通过 estimated_ready_time 计算"""
        warnings.warn(
            "OrderModel.pickup_time 字段已弃用，请使用 estimated_ready_time 字段。",
            DeprecationWarning,
            stacklevel=2
        )
        if self.estimated_ready_time:
            return self.estimated_ready_time.strftime('%H:%M')
        return ''
    

    def save(self, *args, **kwargs):
        """保存订单，处理取餐码、二维码和预计时间 - 修复版本"""
        try:
            logger.info(f"=== 开始保存订单 {self.id or '新订单'} ===")
            
            # 修复：确保在保存前就有 pickup_code
            if not self.pickup_code or self.pickup_code == '':
                logger.info("为新订单生成取餐码")
                self.pickup_code = self.generate_unique_pickup_code()
                logger.info(f"生成取餐码: {self.pickup_code}")
            
            # 更新时间戳
            self.updated_at = timezone.now()
            
            # 修复取餐码生成逻辑
            if not self.pickup_code:
                logger.info("为新订单生成取餐码")
                self.pickup_code = self.generate_unique_pickup_code()
                logger.info(f"生成取餐码: {self.pickup_code}")
            
            # 确保在支付成功后计算预计就绪时间
            if self.payment_status == 'paid' and not self.estimated_ready_time and self.has_coffee():
                logger.info("支付成功，计算预计就绪时间")
                self.estimated_ready_time = self.calculate_estimated_ready_time()
                logger.info(f"预计就绪时间: {self.estimated_ready_time}")
            
            # 生成二维码数据
            if not self.qr_code and self.pickup_code:
                logger.info("生成二维码数据")
                self.qr_code = self.generate_qr_code_data()
            
            # ====== 检查并更新订单状态 ======
            # 如果订单已支付且状态是 pending，更新为 waiting
            if self.payment_status == 'paid' and self.status == 'pending':
                logger.info("更新订单状态为 waiting（等待制作）")
                self.status = 'waiting'
            
            # 调用父类保存方法
            super().save(*args, **kwargs)
            logger.info(f"订单保存成功: {self.id}")
            
            # ========== 队列处理逻辑 ==========
            # 使用 OrderStatusManager 来处理队列加入
            if self.status == 'waiting' and self.payment_status == 'paid':
                from .order_status_manager import OrderStatusManager
                manager = OrderStatusManager(self)
                
                if manager.should_add_to_queue():
                    logger.info(f"订单 {self.id} 符合加入队列条件，尝试加入队列")
                    try:
                        from .queue_manager_refactored import CoffeeQueueManager
                        queue_manager = CoffeeQueueManager()
                        
                        # 检查是否已经在队列中
                        existing_queue_item = CoffeeQueue.objects.filter(order=self).first()
                        if existing_queue_item:
                            logger.info(f"订单 {self.id} 已在队列中，位置: {existing_queue_item.position}")
                        else:
                            # 将订单加入队列
                            queue_item = queue_manager.add_order_to_queue(self)
                            if queue_item:
                                logger.info(f"订单 {self.id} 已加入制作队列，位置: {queue_item.position}")
                            else:
                                logger.error(f"订单 {self.id} 加入队列失败")
                    except Exception as e:
                        logger.error(f"队列处理失败: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
            # ========== 队列处理结束 ==========
                
        except Exception as e:
            logger.error(f"OrderModel保存错误: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            # 如果是唯一约束错误，重新生成取餐码并重试
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
        
        max_attempts = 100
        
        # 方法1：使用时间戳 + 随机数（推荐）
        for attempt in range(max_attempts):
            # 生成4位数字码：时间戳后2位 + 随机2位
            timestamp_part = str(int(time.time() * 1000))[-2:]  # 时间戳后2位
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
        
        # 方法3：UUID简化版（取前4位数字）
        import uuid
        for attempt in range(max_attempts):
            uuid_int = uuid.uuid4().int
            # 从UUID中提取4位数字
            code = str(uuid_int % 10000).zfill(4)  # 确保4位，不足补0
            if not OrderModel.objects.filter(pickup_code=code).exists():
                logger.info(f"使用UUID取餐码: {code}")
                return code
        
        # 方法4：最后的手段 - 顺序生成
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
        
        # 如果所有方法都失败，返回一个安全的默认值
        code = '1234'
        logger.warning(f"所有取餐码生成方法都失败，使用默认值: {code}")
        return code
    
    def generate_qr_code_data(self):
        """生成二维码数据"""
        logger.info(f"开始生成二维码，订单: {self.id}")
        
        # 确保取餐码已生成
        if not self.pickup_code:
            logger.info(f"订单 {self.id} 没有取餐码，调用 save() 生成")
            self.save()  # 这会触发取餐码生成
        
        # 二维码包含订单ID和取餐码
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
            # 返回空字符串而不是报错
            return ''
    
    # 取餐码验证
    def clean(self):
        super().clean()
        # 确保取餐码不是"0000"
        if self.pickup_code == '0000':
            raise ValidationError({'pickup_code': '取餐码不能为0000'})
        
        # 确保取餐码唯一（虽然数据库层面已经有约束）
        if OrderModel.objects.exclude(id=self.id).filter(pickup_code=self.pickup_code).exists():
            raise ValidationError({'pickup_code': '取餐码必须唯一'})





# 咖啡制作队列管理
class CoffeeQueue(models.Model):
    """咖啡制作队列"""
    STATUS_CHOICES = [
        ('waiting', '等待中'), # 等待开始制作 - 订单已支付，排队等待咖啡师开始制作, 需要被计入前面等待时间
        ('preparing', '制作中'), # 正在制作咖啡 - 咖啡师已开始制作该订单的咖啡
        ('ready', '已就緒'), # 制作完成，等待提取 - 咖啡制作已完成，放在取餐区等待客户提取
        ('completed', '已完成'),
    ]
    '''
    整个队列系统的完整逻辑流程图:
    订单支付成功
        ↓
    自动加入CoffeeQueue (status='waiting')
        ↓
    计算队列位置 (position)
        ↓
    计算预计时间 (estimated_start_time, estimated_completion_time)
        ↓
    ↓←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        ↓
    咖啡师点击"开始制作"
        ↓
    状态变为'preparing'，记录actual_start_time
        ↓
    ↓←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        ↓
    咖啡师点击"标记就绪"
        ↓
    状态变为'ready'，记录actual_completion_time
        ↓
    客户提取咖啡
        ↓
    可选：标记为已提取 (可移除或归档)
    '''
    
    order = models.OneToOneField(OrderModel, on_delete=models.CASCADE, related_name='queue_item')
    position = models.PositiveIntegerField(default=0, verbose_name='队列位置')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    estimated_start_time = models.DateTimeField(null=True, blank=True, verbose_name='预计开始时间')
    estimated_completion_time = models.DateTimeField(null=True, blank=True, verbose_name='预计完成时间')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_completion_time = models.DateTimeField(null=True, blank=True, verbose_name='实际完成时间')
    barista = models.CharField(max_length=100, blank=True, null=True, verbose_name='制作人员')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    
    # 制作时间估算字段
    coffee_count = models.PositiveIntegerField(default=0, verbose_name='咖啡杯数')
    preparation_time_minutes = models.PositiveIntegerField(default=0, verbose_name='预计制作时间(分钟)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        verbose_name = '咖啡制作队列'
        verbose_name_plural = '咖啡制作队列'
        indexes = [
            models.Index(fields=['status', 'position']),
            models.Index(fields=['estimated_completion_time']),
        ]
    
    def __str__(self):
        return f"订单 #{self.order.id} - {self.get_status_display()}"


class Barista(models.Model):
    """咖啡师/制作人员"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    is_active = models.BooleanField(default=True, verbose_name='是否在岗')
    efficiency_factor = models.FloatField(default=1.0, verbose_name='效率因子', 
                                         help_text='1.0为正常，<1.0为较快，>1.0为较慢')
    max_concurrent_orders = models.PositiveIntegerField(default=3, verbose_name='最大并发订单数')
    current_load = models.PositiveIntegerField(default=0, verbose_name='当前负载')
    
    class Meta:
        verbose_name = '咖啡师'
        verbose_name_plural = '咖啡师'
    
    def __str__(self):
        return self.name
    
    def is_available(self):
        """检查咖啡师是否可用"""
        return self.is_active and self.current_load < self.max_concurrent_orders


class CoffeePreparationTime(models.Model):
    """咖啡制作时间配置"""
    coffee_type = models.CharField(max_length=100, verbose_name='咖啡类型')
    base_preparation_minutes = models.PositiveIntegerField(default=5, verbose_name='基础制作时间(分钟)')
    additional_per_cup_minutes = models.PositiveIntegerField(default=3, verbose_name='每增加一杯额外时间(分钟)')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '咖啡制作时间配置'
        verbose_name_plural = '咖啡制作时间配置'
    
    def __str__(self):
        return f"{self.coffee_type}: {self.base_preparation_minutes}+{self.additional_per_cup_minutes}分钟"


    # 队列相关方法
    def add_to_queue(self):
        """将订单添加到制作队列"""
        from django.utils import timezone
        
        # 检查是否已加入队列
        if hasattr(self, 'queue_item'):
            return self.queue_item
        
        items = self.get_items()
        
        # 计算咖啡杯数
        coffee_count = sum(item['quantity'] for item in items if item['type'] == 'coffee')
        
        # 只有包含咖啡的订单才需要加入队列
        if coffee_count == 0:
            return None
        
        # 获取队列管理实例
        queue_manager = CoffeeQueueManager()
        
        # 计算制作时间
        preparation_time = queue_manager.calculate_preparation_time(coffee_count)
        
        # 获取队列位置
        position = queue_manager.get_next_position()
        
        # 创建队列项
        queue_item = CoffeeQueue.objects.create(
            order=self,
            position=position,
            coffee_count=coffee_count,
            preparation_time_minutes=preparation_time,
            status='waiting'
        )
        
        # 计算并更新预计时间
        queue_manager.update_estimated_times()
        
        return queue_item
    

    def get_queue_position(self):
        """获取订单在队列中的位置"""
        if hasattr(self, 'queue_item'):
            return self.queue_item.position
        return None
    
    def get_queue_wait_time(self):
        """获取队列等待时间"""
        if not hasattr(self, 'queue_item'):
            return 0
        
        from django.utils import timezone
        queue_manager = CoffeeQueueManager()
        return queue_manager.calculate_wait_time(self.queue_item)


def get_product_image_url(item_data):
    """
    根据商品数据获取正确的图片URL
    """
    # 如果已经有图片URL，直接返回
    if item_data.get('image'):
        return item_data['image']
    
    # 如果没有图片URL，尝试从数据库获取
    try:
        if item_data.get('type') == 'coffee':
            coffee = CoffeeItem.objects.get(id=item_data['id'])
            return coffee.image.url if coffee.image else '/static/images/default-coffee.png'
        elif item_data.get('type') == 'bean':
            bean = BeanItem.objects.get(id=item_data['id'])
            return bean.image.url if bean.image else '/static/images/default-bean.png'
    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
        pass
    
    # 默认图片
    return '/static/images/default-product.png'
