# socialuser/urls.py
from django.urls import path
from .views import (
    profile_view, profile_settings_view, profile_edit_view, 
    profile_emailchange, profile_usernamechange, profile_phonechange,
    profile_emailverify, profile_delete_view, order_history, 
    reactivate_account, test_email_view, social_login_status, 
    social_login_debug, CustomLoginCancelledView
)

urlpatterns = [
    path('', profile_view, name="profile"),
    path('debug/', social_login_debug, name='social-login-debug'),
    path('onboarding/', profile_edit_view, name="profile-onboarding"),
    path('edit/', profile_edit_view, name="profile-edit"),
    path('settings/', profile_settings_view, name="profile-settings"),
    path('emailchange/', profile_emailchange, name="profile-emailchange"),
    path('usernamechange/', profile_usernamechange, name="profile-usernamechange"),
    path('phonechange/', profile_phonechange, name="profile-phonechange"),
    path('emailverify/', profile_emailverify, name="profile-emailverify"),
    path('delete/', profile_delete_view, name="profile-delete"),
    path('orders/', order_history, name="profile-orders"),
    path('test-email/', test_email_view, name='test-email'),
    path('reactivate/', reactivate_account, name='reactivate-account'),
    path('accounts/3rdparty/login/cancelled/', CustomLoginCancelledView.as_view(), name='socialaccount_login_cancelled'),
    
    # 调试路由
    path('social-status/', social_login_status, name='social-status'),
    path('social-debug/', social_login_debug, name='social-debug'),
]