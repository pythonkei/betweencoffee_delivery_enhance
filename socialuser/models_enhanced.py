# socialuser/models_enhanced.py
# 會員系統強化 - 簡化版忠誠度計劃模型
# 移除會員升級邏輯和權益，專注於積分系統
from decimal import Decimal
import logging

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)

# 注意：Profile模型已經在socialuser/models.py中定義
# 這裡只定義新的忠誠度相關模型


class CustomerLoyalty(models.Model):
    """客戶忠誠度計劃 - 簡化版模型（專注積分系統）"""
    
    # 積分類型選擇
    POINT_TYPE_CHOICES = [
        ('purchase', '消費積分'),      # 從消費獲得的積分
        ('bonus', '獎勵積分'),         # 活動或獎勵獲得的積分
        ('referral', '推薦積分'),      # 推薦好友獲得的積分
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    
    # 核心積分字段
    points = models.IntegerField(default=0, verbose_name='當前積分')
    total_points_earned = models.IntegerField(default=0, verbose_name='累計獲得積分')
    total_points_spent = models.IntegerField(default=0, verbose_name='累計使用積分')
    
    # 消費統計
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='累計消費')
    total_orders = models.IntegerField(default=0, verbose_name='累計訂單')
    last_order_date = models.DateTimeField(null=True, blank=True, verbose_name='最後訂單日期')
    
    # 積分有效期相關
    points_expiry_date = models.DateTimeField(null=True, blank=True, verbose_name='積分到期日')
    last_points_update = models.DateTimeField(auto_now=True, verbose_name='最後積分更新時間')
    
    # 會員信息
    join_date = models.DateTimeField(auto_now_add=True, verbose_name='加入日期')
    membership_number = models.CharField(max_length=20, blank=True, verbose_name='會員編號')
    
    class Meta:
        verbose_name = '客戶忠誠度'
        verbose_name_plural = '客戶忠誠度'
        indexes = [
            models.Index(fields=['membership_number']),
            models.Index(fields=['user']),
        ]
        indexes = [
            models.Index(fields=['points']),
            models.Index(fields=['total_spent']),
            models.Index(fields=['points_expiry_date']),
            models.Index(fields=['join_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.points} 積分"
    
    def get_membership_info(self):
        """獲取會員基本信息"""
        return {
            'username': self.user.username,
            'points': self.points,
            'total_spent': float(self.total_spent),
            'total_orders': self.total_orders,
            'join_date': self.join_date,
            'membership_number': self.membership_number or '未分配',
            'points_expiry_date': self.points_expiry_date,
            'points_earned': self.total_points_earned,
            'points_spent': self.total_points_spent,
            'points_balance': self.points,
        }
    
    def add_points_from_order(self, order):
        """從訂單添加積分 - 增強版"""
        try:
            # 每消費$10 = 1積分
            points_earned = int(float(order.total_price) / 10)
            
            # 更新積分統計
            self.points += points_earned
            self.total_points_earned += points_earned
            self.total_spent += Decimal(str(order.total_price))
            self.total_orders += 1
            self.last_order_date = order.created_at
            
            # 積分永久有效，不設置有效期
            
            self.save()
            
            # 記錄活動
            from .models_enhanced import CustomerActivity
            CustomerActivity.record_points_earned(
                self.user, 
                order.id, 
                points_earned, 
                order.total_price
            )
            
            msg = f"用戶 {self.user.username} 訂單 #{order.id} 獲得 {points_earned} 積分"
            logger.info(msg)
            return points_earned
            
        except Exception as e:
            logger.error(f"更新忠誠度積分失敗: {str(e)}")
            return 0
    
    def get_available_rewards(self):
        """獲取可兌換獎勵"""
        rewards = []
        
        # $30 現金券 (300積分)
        if self.points >= 300:
            rewards.append({
                'id': 'voucher_30',
                'name': '$30 現金券',
                'points_required': 300,
                'description': '兌換 $30 現金券折扣',
                'icon': 'fa-ticket-alt',
                'color': 'success'
            })
        
        # $5 現金券 (30積分)
        if self.points >= 30:
            rewards.append({
                'id': 'voucher_5',
                'name': '$5 現金券',
                'points_required': 30,
                'description': '兌換 $5 現金券折扣',
                'icon': 'fa-ticket-alt',
                'color': 'success'
            })


        
        return rewards
    
    def redeem_reward(self, reward_id):
        """兌換獎勵 - 增強版（創建兌換記錄，供訂單自動套用）"""
        rewards = self.get_available_rewards()
        reward = next((r for r in rewards if r['id'] == reward_id), None)
        
        if not reward:
            return False, "獎勵不存在"
        
        if self.points < reward['points_required']:
            return False, "積分不足"
        
        # 扣除積分並更新統計
        self.points -= reward['points_required']
        self.total_points_spent += reward['points_required']
        self.save()
        
        # 創建兌換記錄（供訂單自動套用）
        RedeemedReward.objects.create(
            user=self.user,
            reward_id=reward['id'],
            reward_name=reward['name'],
            points_spent=reward['points_required'],
            is_used=False,
        )
        
        # 記錄活動
        from .models_enhanced import CustomerActivity
        CustomerActivity.record_reward_redeemed(
            self.user,
            reward['name'],
            reward['points_required']
        )
        
        logger.info(f"用戶 {self.user.username} 兌換獎勵: {reward['name']}, 消耗 {reward['points_required']} 積分")
        return True, f"成功兌換 {reward['name']}，將在下次下單時自動套用"
    
    def add_bonus_points(self, points, point_type='bonus', description='獎勵積分'):
        """添加獎勵積分"""
        self.points += points
        self.total_points_earned += points
        
        # 積分永久有效，不設置有效期
        
        self.save()
        
        # 記錄活動
        from .models_enhanced import CustomerActivity
        CustomerActivity.objects.create(
            user=self.user,
            activity_type='points_earned',
            points_change=points,
            description=f"{description}: 獲得 {points} 積分",
            metadata={
                'point_type': point_type,
                'description': description,
                'points': points
            }
        )
        
        logger.info(f"用戶 {self.user.username} 獲得獎勵積分: {points} ({description})")
        return points
    
    def check_points_expiry(self):
        """檢查積分有效期（已棄用 - 積分永久有效）"""
        # 積分永久有效，不再執行過期清除
        return 0
    
    def get_points_summary(self):
        """獲取積分摘要信息"""
        return {
            'current_points': self.points,
            'total_earned': self.total_points_earned,
            'total_spent': self.total_points_spent,
            'points_expiry_date': None,
            'days_until_expiry': None,
            'total_spent_amount': float(self.total_spent),
            'total_orders': self.total_orders,
            'membership_days': (timezone.now() - self.join_date).days,
        }
    
    def generate_membership_number(self):
        """生成會員編號"""
        import secrets
        import string
        
        # 格式: BC-XXXXXX (BC代表Between Coffee)
        prefix = "BC-"
        
        # 生成6位隨機數字
        while True:
            number = ''.join(secrets.choice(string.digits) for _ in range(6))
            membership_number = f"{prefix}{number}"
            
            # 檢查是否已存在
            if not CustomerLoyalty.objects.filter(
                membership_number=membership_number
            ).exists():
                return membership_number
    
    def assign_membership_number(self):
        """分配會員編號（如果尚未分配）"""
        if not self.membership_number:
            self.membership_number = self.generate_membership_number()
            self.save()
            logger.info(f"為用戶 {self.user.username} 分配會員編號: {self.membership_number}")
            return self.membership_number
        return self.membership_number
    
    def should_assign_membership_number(self):
        """判斷是否應該分配會員編號"""
        # 條件：累計消費超過$100或累計訂單超過5筆
        return (
            float(self.total_spent) >= 100 or 
            self.total_orders >= 5
        )
    
    def check_and_assign_membership_number(self):
        """檢查並分配會員編號（如果符合條件）"""
        if not self.membership_number and self.should_assign_membership_number():
            return self.assign_membership_number()
        return self.membership_number or '未分配'


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


class CustomerActivity(models.Model):
    """客戶活動記錄 - 新增模型"""
    ACTIVITY_TYPES = [
        ('points_earned', '獲得積分'),
        ('tier_upgraded', '等級升級（已棄用）'),
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
        # 嘗試獲取訂單的實際創建時間
        order_created_at = None
        try:
            from eshop.models import OrderModel
            order = OrderModel.objects.filter(id=order_id).first()
            if order:
                order_created_at = order.created_at.isoformat()
        except Exception:
            pass
        
        activity = cls.objects.create(
            user=user,
            activity_type='points_earned',
            points_change=points_earned,
            description=f"訂單 #{order_id} 消費 ${float(order_amount):.2f}",
            metadata={
                'order_id': order_id,
                'order_amount': float(order_amount),
                'points_earned': points_earned,
                'order_created_at': order_created_at,
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
            description=f"兌換獎勵: {reward_name}",
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
            description=f"下單成功 #{order_id}，金額 ${float(order_amount):.2f}",
            metadata={
                'order_id': order_id,
                'order_amount': float(order_amount)
            }
        )
        return activity


class RedeemedReward(models.Model):
    """已兌換獎勵記錄 - 供訂單自動套用折扣"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redeemed_rewards')
    reward_id = models.CharField(max_length=50, verbose_name='獎勵ID')
    reward_name = models.CharField(max_length=100, verbose_name='獎勵名稱')
    points_spent = models.IntegerField(default=0, verbose_name='消耗積分')
    is_used = models.BooleanField(default=False, verbose_name='已使用')
    redeemed_at = models.DateTimeField(auto_now_add=True, verbose_name='兌換時間')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用時間')
    applied_order_id = models.IntegerField(null=True, blank=True, verbose_name='應用訂單ID')
    
    class Meta:
        verbose_name = '已兌換獎勵'
        verbose_name_plural = '已兌換獎勵'
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['reward_id']),
        ]
        ordering = ['-redeemed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.reward_name} ({'已使用' if self.is_used else '未使用'})"
    
    def mark_as_used(self, order_id=None):
        """標記獎勵為已使用"""
        self.is_used = True
        self.used_at = timezone.now()
        if order_id:
            self.applied_order_id = order_id
        self.save()
        logger.info(f"獎勵 {self.reward_name} 已在訂單 #{order_id} 中使用")
    
    @classmethod
    def get_unused_rewards(cls, user):
        """獲取用戶未使用的獎勵"""
        return cls.objects.filter(user=user, is_used=False)
    
    @classmethod
    def get_reward_discount_amount(cls, reward_id):
        """根據獎勵ID獲取折扣金額"""
        # $30 現金券：減去 $30
        if reward_id == 'voucher_30':
            return Decimal('30.00')
        # $5 現金券：減去 $5
        elif reward_id == 'voucher_5':
            return Decimal('5.00')

        return Decimal('0.00')

    
    @classmethod
    def get_available_rewards_for_checkout(cls, user):
        """
        獲取用戶在結帳頁面可直接使用的獎勵（無需預先兌換）
        返回獎勵列表，每個獎勵包含 id, name, discount, points_required
        """
        available = []
        try:
            loyalty = CustomerLoyalty.objects.get(user=user)
            # $30 現金券：積分 >= 300 即可使用
            if loyalty.points >= 300:
                available.append({
                    'id': 'voucher_30',
                    'reward_id': 'voucher_30',
                    'reward_name': '$30 現金券',
                    'discount': float(cls.get_reward_discount_amount('voucher_30')),
                    'points_required': 300,
                    'description': '兌換 $30 現金券折扣',
                })
            # $5 現金券：積分 >= 30 即可使用
            if loyalty.points >= 30:
                available.append({
                    'id': 'voucher_5',
                    'reward_id': 'voucher_5',
                    'reward_name': '$5 現金券',
                    'discount': float(cls.get_reward_discount_amount('voucher_5')),
                    'points_required': 30,
                    'description': '兌換 $5 現金券折扣',
                })


        except CustomerLoyalty.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"獲取結帳可用獎勵失敗: {str(e)}")
        return available
    
    @classmethod
    def apply_reward_at_checkout(cls, user, reward_id, order_id=None):
        """
        在結帳時直接兌換並使用獎勵（無需預先兌換）
        1. 扣除積分
        2. 創建 RedeemedReward 記錄
        3. 標記為已使用
        返回 (成功與否, 折扣金額, 獎勵名稱)
        """
        try:
            loyalty = CustomerLoyalty.objects.get(user=user)
            reward_info = cls.get_reward_discount_amount(reward_id)
            
            # 檢查獎勵是否存在
            if reward_id == 'voucher_30':
                points_needed = 300
                reward_name = '$30 現金券'
            elif reward_id == 'voucher_5':
                points_needed = 30
                reward_name = '$5 現金券'


            else:
                return False, Decimal('0.00'), ''
            
            # 檢查積分是否足夠
            if loyalty.points < points_needed:
                logger.warning(f"用戶 {user.username} 積分不足，無法使用 {reward_name}")
                return False, Decimal('0.00'), ''
            
            # 扣除積分
            loyalty.points -= points_needed
            loyalty.total_points_spent += points_needed
            loyalty.save()
            
            # 創建兌換記錄並立即標記為已使用
            redeemed = cls.objects.create(
                user=user,
                reward_id=reward_id,
                reward_name=reward_name,
                points_spent=points_needed,
                is_used=True,
                used_at=timezone.now(),
                applied_order_id=order_id,
            )
            
            # 記錄活動
            try:
                from .models_enhanced import CustomerActivity
                CustomerActivity.record_reward_redeemed(user, reward_name, points_needed)
            except Exception:
                pass
            
            logger.info(f"用戶 {user.username} 在結帳時使用 {reward_name}，消耗 {points_needed} 積分，折扣 ${reward_info}")
            return True, reward_info, reward_name
            
        except CustomerLoyalty.DoesNotExist:
            logger.warning(f"用戶 {user.username} 沒有忠誠度記錄")
            return False, Decimal('0.00'), ''
        except Exception as e:
            logger.error(f"結帳時應用獎勵失敗: {str(e)}")
            return False, Decimal('0.00'), ''
           