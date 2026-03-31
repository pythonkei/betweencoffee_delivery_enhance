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
    
    # 獎勵相關
    path(
        'loyalty/rewards/',
        views_enhanced.rewards_list,
        name='rewards_list'
    ),
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
    
    # 等級信息
    path(
        'loyalty/tier-info/',
        views_enhanced.tier_info,
        name='tier_info'
    ),
    
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