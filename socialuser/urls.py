# socialuser/urls.py
from django.urls import path
from socialuser.views import *

urlpatterns = [
    path('', profile_view, name="profile"),
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
    path('accounts/3rdparty/login/cancelled/', CustomLoginCancelledView.as_view(), name='socialaccount_login_cancelled'),
]
