# socialuser/views.py
import os
from .forms import ProfileForm, PhoneForm, EmailForm, UsernameForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone

from eshop.models import OrderModel
from allauth.account.models import EmailAddress
from django.core.mail import send_mail, EmailMultiAlternatives
from allauth.socialaccount.views import LoginCancelledView as AllAuthLoginCancelledView

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp



def social_login_status(request):
    """检查社交登录状态"""
    current_site = Site.objects.get_current()
    
    context = {
        'site': current_site,
        'social_apps': SocialApp.objects.all(),
        'user_social_accounts': SocialAccount.objects.filter(user=request.user) if request.user.is_authenticated else None,
        'callback_urls': {
            'google': f"https://{current_site.domain}/accounts/google/login/callback/",
            'facebook': f"https://{current_site.domain}/accounts/facebook/login/callback/",
        }
    }
    return render(request, 'socialuser/social_status.html', context)


def social_login_debug(request):
    """社交登录调试页面"""
    current_site = Site.objects.get_current()
    
    # 获取社交应用配置
    try:
        google_app = SocialApp.objects.get(provider='google')
        google_configured = True
    except SocialApp.DoesNotExist:
        google_app = None
        google_configured = False
        
    try:
        facebook_app = SocialApp.objects.get(provider='facebook')
        facebook_configured = True
    except SocialApp.DoesNotExist:
        facebook_app = None
        facebook_configured = False
    
    # 构建回调URL
    if settings.IS_RAILWAY:
        base_url = f"https://{current_site.domain}"
    else:
        base_url = f"http://{current_site.domain}"
    
    context = {
        'current_site': current_site,
        'is_railway': settings.IS_RAILWAY,
        'debug': settings.DEBUG,
        'google_configured': google_configured,
        'facebook_configured': facebook_configured,
        'google_app': google_app,
        'facebook_app': facebook_app,
        'callback_urls': {
            'google': f"{base_url}/accounts/google/login/callback/",
            'facebook': f"{base_url}/accounts/facebook/login/callback/",
        },
        'environment_vars': {
            'OAUTH_GOOGLE_CLIENT_ID': 'Set' if settings.SOCIALACCOUNT_PROVIDERS.get('google') else 'Not Set',
            'OAUTH_GOOGLE_SECRET': 'Set' if settings.SOCIALACCOUNT_PROVIDERS.get('google') else 'Not Set',
            'OAUTH_FACEBOOK_CLIENT_ID': 'Set' if settings.SOCIALACCOUNT_PROVIDERS.get('facebook') else 'Not Set',
            'OAUTH_FACEBOOK_SECRET': 'Set' if settings.SOCIALACCOUNT_PROVIDERS.get('facebook') else 'Not Set',
            'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'Not Set'),
        }
    }
    
    return render(request, 'socialuser/debug.html', context)





def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username).profile
    else:
        try:
            profile = request.user.profile
        except:
            return redirect_to_login(request.get_full_path())
    return render(request, 'socialuser/profile.html', {'profile':profile})


@login_required
def profile_settings_view(request):
    return render(request, 'socialuser/profile_settings.html')



@login_required
def profile_edit_view(request):
    profile = request.user.profile
    
    if request.path == reverse('socialuser:profile-onboarding'):
        onboarding = True
    else:
        onboarding = False
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Handle phone separately since it's not in form fields
            phone = form.cleaned_data.get('phone')
            if phone:
                profile.phone = phone
            form.save()
            if onboarding:
                return redirect('index')
            return redirect('socialuser:profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'socialuser/profile_edit.html', {
        'form': form,
        'onboarding': onboarding
    })



# htmx : profile_settings.html
@login_required
def profile_emailchange(request):
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'socialuser/email_form.html', {'form': form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, f'{email} is already in use.')
                return redirect('socialuser:profile-settings')
            
            form.save()
            send_email_confirmation(request, request.user)
            messages.success(request, 'Email updated successfully. Verification email sent.')
            return redirect('socialuser:profile-settings')
        
        # If form is invalid
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'socialuser/email_form.html', {'form': form})
    
    return redirect('socialuser:profile-settings')



@login_required
def profile_emailverify(request):
    try:
        user = request.user
        if not user.email:
            messages.error(request, "No email address is set for your account")
            return redirect('socialuser:profile-settings')
        
        # Force create email address record if doesn't exist
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={
                'primary': True,
                'verified': False
            }
        )
        
        # Resend confirmation if not verified
        if not email_address.verified:
            email_address.send_confirmation(request)
            messages.success(request, f"Verification email sent to {user.email}")
        else:
            messages.info(request, "Email is already verified")
            
        return redirect('socialuser:profile-settings')
    
    except Exception as e:
        messages.error(request, f"Email verification failed: {str(e)}")
        return redirect('socialuser:profile-settings')




# htmx : profile_settings.html
@login_required
def profile_usernamechange(request):
    if request.htmx:
        form = UsernameForm(instance=request.user)
        return render(request, 'socialuser/username_form.html', {'form':form})
    
    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully.')
            return redirect('socialuser:profile-settings')
        else:
            messages.warning(request, 'Username not valid or already in use')
            return redirect('socialuser:profile-settings')
    
    return redirect('socialuser:profile-settings')    


# htmx : profile_settings.html
# socialuser/views.py
@login_required
def profile_phonechange(request):
    if request.htmx:
        profile = request.user.profile
        # Convert to string for initial value (without country code)
        initial_phone = profile.hk_phone() or ""
        form = PhoneForm(instance=profile, initial={'phone': initial_phone})
        return render(request, 'socialuser/phone_form.html', {'form': form})
    
    if request.method == 'POST':
        profile = request.user.profile
        form = PhoneForm(request.POST, instance=profile)
        
        if form.is_valid():
            # No need to convert to string here as the form handles it
            profile.phone = form.cleaned_data['phone']
            profile.save()
            
            messages.success(request, '電話號碼更新成功')
            return redirect('socialuser:profile-settings')
        else:
            messages.warning(request, '無效的電話號碼格式')
            return redirect('socialuser:profile-settings')
    
    return redirect('socialuser:profile-settings')


@login_required
def profile_delete_view(request):
    if request.method == "POST":
        user = request.user
        
        # Add this to handle cart deletion before user deletion
        try:
            from cart.models import Cart
            Cart.objects.filter(user=user).delete()
        except ImportError:
            # Fallback if cart app is not available
            pass
        
        # Soft delete implementation
        user.profile.is_deleted = True
        user.profile.deleted_at = timezone.now()
        user.profile.save()
        
        logout(request)
        messages.success(request, 'Account deactivated')
        return redirect('index')
    
    return render(request, 'socialuser/profile_delete.html')


@login_required
def order_history(request):
    """顯示訂單歷史，支持分頁"""
    # 獲取分頁參數
    limit = int(request.GET.get('limit', 10))
    offset = int(request.GET.get('offset', 0))
    
    # 獲取訂單總數
    total_orders = OrderModel.objects.filter(user=request.user).count()
    
    # 獲取分頁訂單
    orders = OrderModel.objects.filter(user=request.user).order_by('-created_at')[offset:offset+limit]
    
    # 檢查是否還有更多訂單
    has_more = (offset + limit) < total_orders
    
    # 如果是AJAX請求，返回JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.core import serializers
        from django.http import JsonResponse
        
        orders_data = []
        for order in orders:
            # 確保所有值都是可序列化的
            order_data = {
                'id': order.id,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_price': float(order.total_price),
                'pickup_code': order.pickup_code,
                'payment_status': order.payment_status,
                'status': order.status,
                'status_display': str(order.get_status_display()),  # 轉換為字符串
                'payment_status_display': str(order.get_payment_status_display()),  # 轉換為字符串
                'is_payment_timeout': bool(order.is_payment_timeout),
                'is_quick_order': bool(order.is_quick_order),
                'items': []
            }
            
            # 獲取訂單項目
            for item in order.get_items_with_chinese_options():
                item_data = {
                    'name': str(item.get('name', '')),
                    'quantity': int(item.get('quantity', 0)),
                    'price': float(item.get('price', 0)),
                    'total_price': float(item.get('total_price', 0)),
                    'image': str(item.get('image', '')) if item.get('image') else None,
                    'cup_level_cn': str(item.get('cup_level_cn', '')),
                    'milk_level_cn': str(item.get('milk_level_cn', '')),
                    'grinding_level_cn': str(item.get('grinding_level_cn', '')),
                }
                order_data['items'].append(item_data)
            
            orders_data.append(order_data)
        
        return JsonResponse({
            'orders': orders_data,
            'has_more': bool(has_more),
            'total_orders': int(total_orders),
            'offset': int(offset),
            'limit': int(limit)
        })
    
    # 普通請求，渲染模板
    return render(request, 'socialuser/order_history.html', {
        'orders': orders,
        'has_more': has_more,
        'total_orders': total_orders
    })


def reactivate_account(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.profile.is_deleted:
                # Check if within reactivation period (e.g., 30 days)
                if (timezone.now() - user.profile.deleted_at).days <= 30:
                    user.profile.is_deleted = False
                    user.profile.deleted_at = None
                    user.profile.save()
                    # Optional: send reactivation confirmation email
                    messages.success(request, 'Account reactivated!')
                    return redirect('login')
                else:
                    messages.error(request, 'Reactivation period expired')
            else:
                messages.info(request, 'Account is already active')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email')
    
    return render(request, 'socialuser/reactivate.html')


@login_required
def test_email_view(request):
    context = {
        'email_backend': settings.EMAIL_BACKEND,
        'email_host': settings.EMAIL_HOST,
        'email_port': settings.EMAIL_PORT,
        'sent_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    try:
        # Send both HTML and plain text versions
        html_content = render_to_string('socialuser/email/email_confirmation.html', context)
        text_content = render_to_string('socialuser/email/email_confirmation.txt', context)
        
        msg = EmailMultiAlternatives(
            subject="Django Email Configuration Test",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[request.user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        messages.success(request, "Test email sent successfully! Check your inbox.")
    except Exception as e:
        messages.error(request, f"Failed to send test email: {str(e)}")
    
    return redirect('socialuser:profile-settings')


# Login cancel route to localhost
class CustomLoginCancelledView(AllAuthLoginCancelledView):
    template_name = 'socialuser/login_cancelled.html'