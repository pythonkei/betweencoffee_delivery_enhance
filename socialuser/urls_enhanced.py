# socialuser/urls_enhanced.py
# 會員系統強化 - URL配置
from django.urls import path
from . import views_enhanced

app_name = 'socialuser_enhanced'

urlpatterns = [
    # 忠誠度儀表板
    path(
        'loyalty/dashboard/',
        views_enhanced.loyalty_dashboard,
        name='loyalty_dashboard'
    ),
    
    # 獎勵相關（已整合到loyalty_dashboard中）
    path(
        'loyalty/redeem/',
        views_enhanced.redeem_reward,
        name='redeem_reward'
    ),
    
    # 優惠券相關
    path(
        'loyalty/coupons/',
        views_enhanced.coupons_list,
        name='coupons_list'
    ),
    path(
        'loyalty/apply-coupon/',
        views_enhanced.apply_coupon,
        name='apply_coupon'
    ),
    
    # 活動歷史
    path(
        'loyalty/activities/',
        views_enhanced.activity_history,
        name='activity_history'
    ),
    
    # 等級信息（已移除，會員等級機制已不需要）
    
    # API端點
    path(
        'api/loyalty-status/',
        views_enhanced.api_loyalty_status,
        name='api_loyalty_status'
    ),
    path(
        'api/recent-activities/',
        views_enhanced.api_recent_activities,
        name='api_recent_activities'
    ),
    path(
        'api/active-coupons/',
        views_enhanced.api_active_coupons,
        name='api_active_coupons'
    ),
]