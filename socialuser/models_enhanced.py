# socialuser/models_enhanced.py
# 會員系統強化 - 忠誠度計劃模型
from datetime import timedelta
from decimal import Decimal
import logging

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)

# 注意：Profile模型已經在socialuser/models.py中定義
# 這裡只定義新的忠誠度相關模型


class CustomerLoyalty(models.Model):
    """客戶忠誠度計劃 - 新增模型"""
    TIER_CHOICES = [
        ('bronze', '銅級會員'),      # 新客戶
        ('silver', '銀級會員'),      # 消費滿$500
        ('gold', '金級會員'),        # 消費滿$1000
        ('platinum', '白金會員'),    # 消費滿$2000
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    points = models.IntegerField(default=0, verbose_name='積分')
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='累計消費')
    total_orders = models.IntegerField(default=0, verbose_name='累計訂單')
    last_order_date = models.DateTimeField(null=True, blank=True, verbose_name='最後訂單日期')
    join_date = models.DateTimeField(auto_now_add=True, verbose_name='加入日期')
    
    # 會員權益
    discount_rate = models.DecimalField(max_digits=4, decimal_places=2, default=1.0, verbose_name='折扣率')
    free_upgrade = models.BooleanField(default=False, verbose_name='免費升級杯型')
    priority_service = models.BooleanField(default=False, verbose_name='優先服務')
    
    class Meta:
        verbose_name = '客戶忠誠度'
        verbose_name_plural = '客戶忠誠度'
        indexes = [
            models.Index(fields=['tier']),
            models.Index(fields=['points']),
            models.Index(fields=['total_spent']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tier_display()}"
    
    def update_tier(self):
        """根據消費金額更新會員等級"""
        if self.total_spent >= Decimal('2000'):
            new_tier = 'platinum'
            new_discount_rate = Decimal('0.85')  # 85折
            new_free_upgrade = True
            new_priority_service = True
        elif self.total_spent >= Decimal('1000'):
            new_tier = 'gold'
            new_discount_rate = Decimal('0.90')  # 9折
            new_free_upgrade = True
            new_priority_service = False
        elif self.total_spent >= Decimal('500'):
            new_tier = 'silver'
            new_discount_rate = Decimal('0.95')  # 95折
            new_free_upgrade = False
            new_priority_service = False
        else:
            new_tier = 'bronze'
            new_discount_rate = Decimal('1.00')  # 無折扣
            new_free_upgrade = False
            new_priority_service = False
        
        # 檢查是否有變化
        tier_changed = self.tier != new_tier
        self.tier = new_tier
        self.discount_rate = new_discount_rate
        self.free_upgrade = new_free_upgrade
        self.priority_service = new_priority_service
        self.save()
        
        if tier_changed:
            logger.info(f"用戶 {self.user.username} 升級為 {self.get_tier_display()}")
        
        return tier_changed
    
    def add_points_from_order(self, order):
        """從訂單添加積分"""
        try:
            # 每消費$10 = 1積分
            points_earned = int(float(order.total_price) / 10)
            self.points += points_earned
            self.total_spent += Decimal(str(order.total_price))
            self.total_orders += 1
            self.last_order_date = order.created_at
            
            # 更新等級
            self.update_tier()
            self.save()
            
            logger.info(f"用戶 {self.user.username} 訂單 #{order.id} 獲得 {points_earned} 積分")
            return points_earned
            
        except Exception as e:
            logger.error(f"更新忠誠度積分失敗: {str(e)}")
            return 0
    
    def get_available_rewards(self):
        """獲取可兌換獎勵"""
        rewards = []
        
        # 免費咖啡一杯 (10積分)
        if self.points >= 10:
            rewards.append({
                'id': 'free_coffee',
                'name': '免費咖啡一杯',
                'points_required': 10,
                'description': '兌換任意標準杯型咖啡一杯',
                'icon': 'fa-mug-hot',
                'color': 'success'
            })
        
        # 免費升級大杯 (20積分)
        if self.points >= 20:
            rewards.append({
                'id': 'free_upgrade',
                'name': '免費升級大杯',
                'points_required': 20,
                'description': '免費升級任意咖啡至大杯',
                'icon': 'fa-arrow-up',
                'color': 'warning'
            })
        
        # 生日驚喜禮包 (50積分)
        if self.points >= 50:
            rewards.append({
                'id': 'birthday_gift',
                'name': '生日驚喜禮包',
                'points_required': 50,
                'description': '生日當月免費咖啡+甜點',
                'icon': 'fa-gift',
                'color': 'danger'
            })
        
        return rewards
    
    def redeem_reward(self, reward_id):
        """兌換獎勵"""
        rewards = self.get_available_rewards()
        reward = next((r for r in rewards if r['id'] == reward_id), None)
        
        if not reward:
            return False, "獎勵不存在"
        
        if self.points < reward['points_required']:
            return False, "積分不足"
        
        # 扣除積分
        self.points -= reward['points_required']
        self.save()
        
        logger.info(f"用戶 {self.user.username} 兌換獎勵: {reward['name']}, 消耗 {reward['points_required']} 積分")
        return True, f"成功兌換 {reward['name']}"
    
    def get_tier_info(self):
        """獲取會員等級詳細信息"""
        tier_info = {
            'bronze': {
                'name': '銅級會員',
                'min_spent': 0,
                'discount': '無折扣',
                'benefits': ['積分累積'],
                'color': '#CD7F32',
                'icon': 'fa-star'
            },
            'silver': {
                'name': '銀級會員',
                'min_spent': 500,
                'discount': '95折',
                'benefits': ['積分累積', '95折優惠'],
                'color': '#C0C0C0',
                'icon': 'fa-star-half-alt'
            },
            'gold': {
                'name': '金級會員',
                'min_spent': 1000,
                'discount': '9折',
                'benefits': ['積分累積', '9折優惠', '免費升級杯型'],
                'color': '#FFD700',
                'icon': 'fa-star'
            },
            'platinum': {
                'name': '白金會員',
                'min_spent': 2000,
                'discount': '85折',
                'benefits': ['積分累積', '85折優惠', '免費升級杯型', '優先服務'],
                'color': '#E5E4E2',
                'icon': 'fa-crown'
            }
        }
        
        current_tier = tier_info.get(self.tier, tier_info['bronze'])
        next_tier = None
        
        # 計算下一等級信息
        if self.tier == 'bronze':
            next_tier = tier_info['silver']
            next_tier['points_needed'] = max(0, 500 - float(self.total_spent))
        elif self.tier == 'silver':
            next_tier = tier_info['gold']
            next_tier['points_needed'] = max(0, 1000 - float(self.total_spent))
        elif self.tier == 'gold':
            next_tier = tier_info['platinum']
            next_tier['points_needed'] = max(0, 2000 - float(self.total_spent))
        
        return {
            'current': current_tier,
            'next': next_tier,
            'progress': self._calculate_tier_progress()
        }
    
    def _calculate_tier_progress(self):
        """計算升級進度"""
        if self.tier == 'platinum':
            return 100  # 最高等級
        
        tier_thresholds = {
            'bronze': 500,
            'silver': 1000,
            'gold': 2000
        }
        
        next_threshold = tier_thresholds.get(self.tier, 500)
        progress = min(100, (float(self.total_spent) / next_threshold) * 100)
        return round(progress, 1)


class CustomerCoupon(models.Model):
    """客戶優惠券 - 新增模型"""
    COUPON_TYPES = [
        ('percentage', '百分比折扣'),
        ('fixed', '固定金額'),
        ('free_item', '免費商品'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True, verbose_name='優惠碼')
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES, verbose_name='優惠類型')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='優惠值')
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='最低消費金額')
    valid_from = models.DateTimeField(verbose_name='生效時間')
    valid_to = models.DateTimeField(verbose_name='過期時間')
    is_used = models.BooleanField(default=False, verbose_name='已使用')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用時間')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='創建時間')
    description = models.TextField(blank=True, verbose_name='優惠描述')
    
    class Meta:
        verbose_name = '客戶優惠券'
        verbose_name_plural = '客戶優惠券'
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['valid_to']),
            models.Index(fields=['code']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.user.username}"
    
    def is_valid(self):
        """檢查優惠券是否有效"""
        now = timezone.now()
        return (
            not self.is_used and
            self.valid_from <= now <= self.valid_to
        )
    
    def apply_discount(self, order_amount):
        """應用折扣"""
        if not self.is_valid():
            return 0, "優惠券無效或已過期"
        
        if order_amount < self.min_order_amount:
            return 0, f"訂單金額需滿 ${self.min_order_amount}"
        
        if self.coupon_type == 'percentage':
            discount = order_amount * (self.value / 100)
            message = f"已應用 {self.value}% 折扣"
        elif self.coupon_type == 'fixed':
            discount = min(self.value, order_amount)
            message = f"已減免 ${discount}"
        else:  # free_item
            discount = 0  # 免費商品需要特殊處理
            message = "免費商品優惠"
        
        return discount, message
    
    def mark_as_used(self):
        """標記為已使用"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
        logger.info(f"優惠券 {self.code} 已被使用")
    
    @classmethod
    def generate_coupon_code(cls):
        """生成優惠券代碼"""
        import secrets
        import string
        
        # 生成8位隨機碼：字母+數字
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            if not cls.objects.filter(code=code).exists():
                return code
    
    @classmethod
    def create_welcome_coupon(cls, user):
        """創建歡迎優惠券（新用戶）"""
        from django.utils import timezone
        from datetime import timedelta
        
        code = cls.generate_coupon_code()
        valid_from = timezone.now()
        valid_to = valid_from + timedelta(days=30)  # 30天有效期
        
        coupon = cls.objects.create(
            user=user,
            code=code,
            coupon_type='percentage',
            value=Decimal('10.00'),  # 9折
            min_order_amount=Decimal('0.00'),
            valid_from=valid_from,
            valid_to=valid_to,
            description='新會員歡迎優惠，全單9折'
        )
        
        logger.info(f"為新用戶 {user.username} 創建歡迎優惠券: {code}")
        return coupon
    
    @classmethod
    def create_birthday_coupon(cls, user):
        """創建生日優惠券"""
        code = cls.generate_coupon_code()
        valid_from = timezone.now()
        valid_to = valid_from + timedelta(days=30)  # 生日月有效
        
        coupon = cls.objects.create(
            user=user,
            code=code,
            coupon_type='fixed',
            value=Decimal('20.00'),  # $20優惠
            min_order_amount=Decimal('50.00'),
            valid_from=valid_from,
            valid_to=valid_to,
            description='生日快樂！$20優惠券'
        )
        
        logger.info(f"為用戶 {user.username} 創建生日優惠券: {code}")
        return coupon


class CustomerActivity(models.Model):
    """客戶活動記錄 - 新增模型"""
    ACTIVITY_TYPES = [
        ('points_earned', '獲得積分'),
        ('tier_upgraded', '等級升級'),
        ('reward_redeemed', '兌換獎勵'),
        ('coupon_used', '使用優惠券'),
        ('order_placed', '下單成功'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name='活動類型')
    points_change = models.IntegerField(default=0, verbose_name='積分變化')
    description = models.TextField(verbose_name='活動描述')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='附加數據')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='記錄時間')
    
    class Meta:
        verbose_name = '客戶活動記錄'
        verbose_name_plural = '客戶活動記錄'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"
    
    @classmethod
    def record_points_earned(cls, user, order_id, points_earned, order_amount):
        """記錄獲得積分"""
        activity = cls.objects.create(
            user=user,
            activity_type='points_earned',
            points_change=points_earned,
            description=f"訂單 #{order_id} 消費 ${order_amount}，獲得 {points_earned} 積分",
            metadata={
                'order_id': order_id,
                'order_amount': float(order_amount),
                'points_earned': points_earned
            }
        )
        return activity
    
    @classmethod
    def record_tier_upgrade(cls, user, old_tier, new_tier):
        """記錄等級升級"""
        activity = cls.objects.create(
            user=user,
            activity_type='tier_upgraded',
            points_change=0,
            description=f"會員等級從 {old_tier} 升級為 {new_tier}",
            metadata={
                'old_tier': old_tier,
                'new_tier': new_tier
            }
        )
        return activity
    
    @classmethod
    def record_reward_redeemed(cls, user, reward_name, points_used):
        """記錄兌換獎勵"""
        activity = cls.objects.create(
            user=user,
            activity_type='reward_redeemed',
            points_change=-points_used,
            description=f"兌換獎勵: {reward_name}，消耗 {points_used} 積分",
            metadata={
                'reward_name': reward_name,
                'points_used': points_used
            }
        )
        return activity
    
    @classmethod
    def record_coupon_used(cls, user, coupon_code, discount_amount):
        """記錄使用優惠券"""
        activity = cls.objects.create(
            user=user,
            activity_type='coupon_used',
            points_change=0,
            description=f"使用優惠券 {coupon_code}，節省 ${discount_amount}",
            metadata={
                'coupon_code': coupon_code,
                'discount_amount': float(discount_amount)
            }
        )
        return activity
    
    @classmethod
    def record_order_placed(cls, user, order_id, order_amount):
        """記錄下單成功"""
        activity = cls.objects.create(
            user=user,
            activity_type='order_placed',
            points_change=0,
            description=f"下單成功 #${order_id}，金額 ${order_amount}",
            metadata={
                'order_id': order_id,
                'order_amount': float(order_amount)
            }
        )
        return activity
           