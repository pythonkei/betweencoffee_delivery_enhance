# socialuser/signals_enhanced.py
# 會員系統強化 - 信號處理
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from eshop.models import OrderModel
from .models import Profile  # 從現有模型導入
from .models_enhanced import (
    CustomerLoyalty, CustomerCoupon, CustomerActivity
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile_and_loyalty(sender, instance, created, **kwargs):
    """新用戶自動創建Profile和忠誠度記錄"""
    if created:
        try:
            # 創建Profile
            Profile.objects.get_or_create(user=instance)
            logger.info(f"為新用戶 {instance.username} 創建Profile")
            
            # 創建忠誠度記錄
            loyalty, loyalty_created = CustomerLoyalty.objects.get_or_create(
                user=instance
            )
            if loyalty_created:
                logger.info(f"為新用戶 {instance.username} 創建忠誠度記錄")
            
            # 創建歡迎優惠券
            try:
                coupon = CustomerCoupon.create_welcome_coupon(instance)
                logger.info(
                    f"為新用戶 {instance.username} 創建歡迎優惠券: {coupon.code}"
                )
                
                # 記錄活動
                CustomerActivity.record_order_placed(instance, 0, 0)
                
            except Exception as e:
                logger.error(f"創建歡迎優惠券失敗: {str(e)}")
                
        except Exception as e:
            logger.error(f"創建用戶相關記錄失敗: {str(e)}")


@receiver(post_save, sender=OrderModel)
def update_loyalty_on_order_paid(sender, instance, created, **kwargs):
    """訂單支付完成後更新忠誠度"""
    # 只處理已支付的訂單
    if instance.payment_status == 'paid' and instance.user:
        try:
            # 檢查是否已經處理過這個訂單（防止重複計算）
            # 通過檢查活動記錄來避免重複
            existing_activities = CustomerActivity.objects.filter(
                user=instance.user,
                activity_type='points_earned',
                metadata__contains={'order_id': instance.id}
            )
            
            if existing_activities.exists():
                logger.warning(
                    f"訂單 #{instance.id} 已經處理過，跳過重複計算"
                )
                return
            
            # 獲取或創建忠誠度記錄
            loyalty, _ = CustomerLoyalty.objects.get_or_create(
                user=instance.user
            )
            
            # 添加積分
            points_earned = loyalty.add_points_from_order(instance)
            
            if points_earned > 0:
                # 記錄獲得積分活動
                CustomerActivity.record_points_earned(
                    instance.user,
                    instance.id,
                    points_earned,
                    instance.total_price
                )
                
                logger.info(
                    f"用戶 {instance.user.username} "
                    f"訂單 #{instance.id} 獲得 {points_earned} 積分"
                )
            
            # 檢查並分配會員編號（如果符合條件）
            membership_number = loyalty.check_and_assign_membership_number()
            if membership_number and membership_number != '未分配':
                logger.info(
                    f"用戶 {instance.user.username} "
                    f"獲得會員編號: {membership_number}"
                )
            
        except Exception as e:
            logger.error(f"更新忠誠度失敗: {str(e)}")


@receiver(post_save, sender=CustomerLoyalty)
def create_birthday_coupon_on_join_anniversary(sender, instance, created, **kwargs):
    """在加入周年或生日時創建優惠券"""
    if not created:
        return
    
    try:
        # 檢查是否是加入周年（每年一次）
        join_date = instance.join_date
        now = timezone.now()
        
        # 如果是加入周年（每年同月同日）
        if (join_date.month == now.month and 
                join_date.day == now.day and
                join_date.year != now.year):
            
            coupon = CustomerCoupon.create_birthday_coupon(instance.user)
            logger.info(
                f"為用戶 {instance.user.username} "
                f"加入周年創建優惠券: {coupon.code}"
            )
            
    except Exception as e:
        logger.error(f"創建周年優惠券失敗: {str(e)}")


@receiver(post_save, sender=CustomerCoupon)
def record_coupon_creation(sender, instance, created, **kwargs):
    """記錄優惠券創建"""
    if created:
        try:
            # 可以記錄優惠券創建活動
            logger.info(
                f"創建優惠券: {instance.code} 給用戶 {instance.user.username}"
            )
        except Exception as e:
            logger.error(f"記錄優惠券創建失敗: {str(e)}")


@receiver(post_save, sender=CustomerActivity)
def log_activity_creation(sender, instance, created, **kwargs):
    """記錄活動創建（用於調試）"""
    if created:
        logger.debug(
            f"記錄活動: {instance.user.username} - {instance.activity_type}"
        )


def connect_signals():
    """手動連接信號（在應用啟動時調用）"""
    # 這些信號會在應用啟動時自動連接
    # 但我們可以在這裡確保它們被正確連接
    logger.info("會員系統信號已連接")


def disconnect_signals():
    """斷開信號連接（用於測試）"""
    # 斷開所有信號
    post_save.disconnect(create_user_profile_and_loyalty, sender=User)
    post_save.disconnect(update_loyalty_on_order_paid, sender=OrderModel)
    post_save.disconnect(
        create_birthday_coupon_on_join_anniversary, sender=CustomerLoyalty
    )
    post_save.disconnect(record_coupon_creation, sender=CustomerCoupon)
    post_save.disconnect(log_activity_creation, sender=CustomerActivity)
    
    logger.info("會員系統信號已斷開")
