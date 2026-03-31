# socialuser/urls.py
from django.urls import path
from .views import (
    profile_view, profile_settings_view, profile_edit_view, 
    profile_emailchange, profile_usernamechange, profile_phonechange,
    profile_emailverify, profile_delete_view, order_history, 
    reactivate_account, test_email_view, social_login_status, 
    social_login_debug, CustomLoginCancelledView
)

# 導入強化會員系統視圖
from . import views_enhanced

urlpatterns = [
    path('', profile_view, name="profile"),
    path('debug/', social_login_debug, name='social-login-debug'),
    path('onboarding/', profile_edit_view, name="profile-onboarding"),
    path('edit/', profile_edit_view, name="profile-edit"),
    path('settings/', profile_settings_view, name="profile-settings"),
    path('emailchange/', profile_emailchange, name="profile-emailchange"),
    path('usernamechange/', profile_usernamechange, 
         name="profile-usernamechange"),
    path('phonechange/', profile_phonechange, name="profile-phonechange"),
    path('emailverify/', profile_emailverify, name="profile-emailverify"),
    path('delete/', profile_delete_view, name="profile-delete"),
    path('orders/', order_history, name="profile-orders"),
    path('test-email/', test_email_view, name='test-email'),
    path('reactivate/', reactivate_account, name='reactivate-account'),
    path('accounts/3rdparty/login/cancelled/', 
         CustomLoginCancelledView.as_view(), 
         name='socialaccount_login_cancelled'),
    
    # 调试路由
    path('social-status/', social_login_status, name='social-status'),
    path('social-debug/', social_login_debug, name='social-debug'),
    
    # 會員忠誠度系統（新增）
    path('loyalty/dashboard/', 
         views_enhanced.loyalty_dashboard, 
         name='loyalty_dashboard'),
    path('loyalty/rewards/', 
         views_enhanced.rewards_list, 
         name='rewards_list'),
    path('loyalty/redeem/', 
         views_enhanced.redeem_reward, 
         name='redeem_reward'),
    path('loyalty/coupons/', 
         views_enhanced.coupons_list, 
         name='coupons_list'),
    path('loyalty/apply-coupon/', 
         views_enhanced.apply_coupon, 
         name='apply_coupon'),
    path('loyalty/activities/', 
         views_enhanced.activity_history, 
         name='activity_history'),
    path('loyalty/tier-info/', 
         views_enhanced.tier_info, 
         name='tier_info'),
    
    # API端點
    path('api/loyalty-status/', 
         views_enhanced.api_loyalty_status, 
         name='api_loyalty_status'),
    path('api/recent-activities/', 
         views_enhanced.api_recent_activities, 
         name='api_recent_activities'),
    path('api/active-coupons/', 
         views_enhanced.api_active_coupons, 
         name='api_active_coupons'),
]
