# eshop/models.py
import json
import random
import string
from django.conf import settings
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from .time_utils import get_hong_kong_time, is_time_ready, get_remaining_minutes, format_time_for_display

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
    hot_item_order = models.PositiveIntegerField(default=0, verbose_name='热门商品排序', 
                                               help_text='数字越小显示越靠前')

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
        """获取详情页图片"""
        if self.image:
            return self.image.url
        else:
            return '/static/images/default-coffee-detail.png'

    class Meta:
        verbose_name_plural = "Coffee"
        ordering = ['hot_item_order', '-list_date']  # 添加默认排序


class BeanItem(models.Model):
    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    image = models.ImageField(upload_to='bean_images/')
    image_index = models.ImageField(upload_to='bean_images/index/', blank=True, null=True, verbose_name='首页图片')
    price_200g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_1kg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
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
    hot_item_order = models.PositiveIntegerField(default=0, verbose_name='热门商品排序',
                                               help_text='数字越小显示越靠前')

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
        """获取详情页图片"""
        if self.image:
            return self.image.url
        else:
            return '/static/images/default-bean-detail.png'
    
    class Meta:
        verbose_name_plural = "Bean"
        ordering = ['hot_item_order', '-list_date']  # 添加默认排序
    
    # 获取价格的方法
    def get_price(self, weight):
        if weight == '200g':
            return self.price_200g
        elif weight == '1kg':
            return self.price_1kg
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
                # Convert price to float
                item['price'] = float(item['price'])
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
            except (TypeError, ValueError):
                item['price'] = 0.0
                item['total_price'] = 0.0
                item['image'] = '/static/images/default-product.png'
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


# Order processing between user what order
class OrderModel(models.Model):
    created_on = models.DateTimeField(default=timezone.now)
    # Track Users
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=80, blank=True, null=True, default='')
    phone = models.CharField(max_length=12, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    is_delivery = models.BooleanField(default=False)
    items = models.JSONField()  # Stores order items as JSON
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00  # 明确的数字默认值
    )
    created_at = models.DateTimeField(
        auto_now_add=True  # 对于时间字段使用 auto_now_add
    )

    ORDER_TYPE_CHOICES = [
        ('normal', '普通訂單'),
        ('quick', '快速訂單'),
    ]
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='normal')
    is_quick_order = models.BooleanField (default=False, verbose_name='快速訂單', help_text='優先處理')
    pickup_time = models.CharField(max_length=50, blank=True)
    cup_size = models.CharField(max_length=50, blank=True)
    pickup_code = models.CharField(max_length=6, unique=True, blank=True)
    qr_code = models.TextField(blank=True, null=True)  # 儲存二維碼數據
    estimated_ready_time = models.DateTimeField(blank=True, null=True)  # 預計就緒時間
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', '待處理'),
        ('preparing', '制作中'),
        ('ready', '已就緒'),
        ('completed', '已完成')
    ])
    notification_sent = models.BooleanField(default=False)  # 是否已發送通知
    
    # 支付方式选择
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
    
    # FPS支付相关字段
    fps_reference = models.CharField(max_length=50, blank=True, null=True, verbose_name='FPS参考编号')
    fps_qr_code = models.TextField(blank=True, null=True, verbose_name='FPS二维码')


    # get time display
    def __str__(self):
        local_time = timezone.localtime(self.created_on)
        return f'Order: {local_time.strftime("%b %d %I: %M %p")}'

    # 解析 JSON 字符串，并返回包含数值项的列表
    def get_items(self):
        
        # 延迟导入在需要使用,以避免循环导入
        from .models import CoffeeItem, BeanItem
        
        if isinstance(self.items, str):
            items = json.loads(self.items)
        else:
            items = self.items  # If it's already a list
            
        # Convert prices to floats and ensure image URLs are present
        for item in items:
            try:
                # Convert price to float
                item['price'] = float(item['price'])
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
            except (TypeError, ValueError):
                item['price'] = 0.0
                item['total_price'] = 0.0
                item['image'] = '/static/images/default-product.png'
        return items


    # 靜態方法：轉換選項值為中文
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

    # 取得訂單商品中文選項
    def get_items_with_chinese_options(self):
        """返回带有中文选项的商品列表"""
        items = self.get_items()
        
        for item in items:
            if 'cup_level' in item:
                item['cup_level_cn'] = self.translate_option('cup_level', item['cup_level'])
            if 'milk_level' in item:
                item['milk_level_cn'] = self.translate_option('milk_level', item['milk_level'])
            if 'grinding_level' in item:
                item['grinding_level_cn'] = self.translate_option('grinding_level', item['grinding_level'])
        
        return items



    # 檢查支付狀態
    def check_payment_status(self):

        if self.is_paid:
            return True
        
        # 如果是PayPal支付，可以在这里添加额外的状态检查
        # 如果是支付宝支付，可以调用支付宝API检查状态
        
        return self.is_paid
    

    # 根據訂單中的咖啡數量, 計算預計就緒時間
    def calculate_estimated_ready_time(self):
        """根据订单中的咖啡数量计算预计就绪时间"""
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
            return None
        
        # 如果没有任何商品，返回None
        if not has_coffee and not has_beans:
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
        base_time = get_hong_kong_time()
        return base_time + timedelta(minutes=total_minutes)
    
    def get_preparation_time_display(self):
        """获取制作时间显示文本"""
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
            return ""
        
        # 计算制作时间
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
            return "咖啡豆订单 - 随时可取"
        elif has_coffee and not has_beans:
            return "咖啡订单 - 需要制作"
        elif has_coffee and has_beans:
            return "混合订单 - 咖啡需要制作"
        else:
            return "普通订单"
    
    def should_show_preparation_time(self):
        """判断是否应该显示制作时间"""
        items = self.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        # 只有包含咖啡的订单才显示制作时间
        return has_coffee





    def update_status_based_on_time(self):
        """根据时间自动更新订单状态"""
        # 检查订单类型
        items = self.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        is_beans_only = has_beans and not has_coffee
        
        # 如果是纯咖啡豆订单，直接设置为就绪状态
        if is_beans_only:
            if self.status != 'ready' and self.status != 'completed':
                self.status = 'ready'
                self.save()
            return
        
        # 其他订单类型按原逻辑处理
        if not self.estimated_ready_time:
            # 没有预计时间，标记为就绪
            if self.status != 'ready' and self.status != 'completed':
                self.status = 'ready'
                self.save()
            return
        
        # 使用统一的时间检查方法
        if is_time_ready(self.estimated_ready_time):
            if self.status != 'ready' and self.status != 'completed':
                self.status = 'ready'
                self.save()
        else:
            if self.status != 'preparing':
                self.status = 'preparing'
                self.save()


    def is_ready(self):
        """检查订单是否已完成制作"""
        # 先更新状态
        self.update_status_based_on_time()
        return self.status in ['ready', 'completed']

    def get_remaining_minutes(self):
        """获取剩余分钟数"""
        return get_remaining_minutes(self.estimated_ready_time)

    def get_display_time(self):
        """获取显示用的时间格式"""
        return format_time_for_display(self.estimated_ready_time)



    # 訂單- 產生取餐碼
    def save(self, *args, **kwargs):
        # 如果是新订单，生成取餐码
        if not self.pk and not self.pickup_code:
            # 确保取餐码唯一
            while True:
                self.pickup_code = self.generate_pickup_code()
                if not OrderModel.objects.filter(pickup_code=self.pickup_code).exists():
                    break
        
        super().save(*args, **kwargs)


    # 生成4位数字取餐码
    def generate_pickup_code(self):
        import secrets
        import string
        return ''.join(secrets.choice(string.digits) for _ in range(4))


    # 生成二维码数据
    def generate_qr_code_data(self):
        import qrcode
        import io
        import base64
        
        # 确保取餐码已生成
        if not self.pickup_code:
            self.save()  # 这会触发取餐码生成
        
        # 二维码包含订单ID和取餐码
        qr_data = f"Order: {self.id}, Pickup Code: {self.pickup_code}"
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
        return base64.b64encode(buffer.getvalue()).decode()


    # 取餐码验证
    def clean(self):
        super().clean()
        # 确保取餐码不是"0000"
        if self.pickup_code == '0000':
            raise ValidationError({'pickup_code': '取餐码不能为0000'})
        
        # 确保取餐码唯一（虽然数据库层面已经有约束）
        if OrderModel.objects.exclude(id=self.id).filter(pickup_code=self.pickup_code).exists():
            raise ValidationError({'pickup_code': '取餐码必须唯一'})
