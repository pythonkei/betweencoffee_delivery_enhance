# socialuser/views.py
import os
from .forms import ProfileForm, PhoneForm, EmailForm, UsernameForm, AvatarForm
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
    
    # 準備行內編輯表單（用於 AJAX 原地編輯）
    from .forms import EmailForm, UsernameForm, PhoneForm, AvatarForm
    
    email_form = EmailForm(instance=request.user)
    username_form = UsernameForm(instance=request.user)
    initial_phone = profile.hk_phone() or ""
    phone_form = PhoneForm(instance=profile, initial={'phone': initial_phone})
    avatar_form = AvatarForm(instance=profile)
    
    return render(request, 'socialuser/profile.html', {
        'profile': profile,
        'email_form': email_form,
        'username_form': username_form,
        'phone_form': phone_form,
        'avatar_form': avatar_form,
    })





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



# htmx / AJAX : profile.html
@login_required
def profile_emailchange(request):
    from django.http import JsonResponse
    
    # AJAX 請求處理
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            form = EmailForm(request.POST, instance=request.user)
            if form.is_valid():
                email = form.cleaned_data['email']
                if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                    return JsonResponse({'success': False, 'message': '此電子郵件已被使用'})
                
                form.save()
                send_email_confirmation(request, request.user)
                return JsonResponse({
                    'success': True,
                    'message': '電子郵件更新成功，驗證郵件已發送',
                    'email': email
                })
            
            # 表單驗證失敗
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)
            return JsonResponse({'success': False, 'message': '; '.join(errors) if errors else '請輸入有效的電子郵件'})
        
        return JsonResponse({'success': False, 'message': '僅支援 POST 請求'})
    
    # htmx 處理（向後兼容）
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'socialuser/email_form.html', {'form': form})
    
    # 原始 POST 處理（向後兼容）
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, f'{email} is already in use.')
                return redirect('socialuser:profile')
            
            form.save()
            send_email_confirmation(request, request.user)
            messages.success(request, 'Email updated successfully. Verification email sent.')
            return redirect('socialuser:profile')
        
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'socialuser/email_form.html', {'form': form})
    
    return redirect('socialuser:profile')





@login_required
def profile_emailverify(request):
    import logging
    logger = logging.getLogger(__name__)
    
    # AJAX 請求處理
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        try:
            user = request.user
            if not user.email:
                return JsonResponse({'success': False, 'message': '請先設定電子郵件地址'})
            
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={'primary': True, 'verified': False}
            )
            
            if not email_address.verified:
                email_address.send_confirmation(request)
                return JsonResponse({'success': True, 'message': f'驗證郵件已發送至 {user.email}'})
            else:
                return JsonResponse({'success': True, 'message': '電子郵件已驗證'})
        except Exception as e:
            logger.error(f"Email verification AJAX error: {e}", exc_info=True)
            return JsonResponse({'success': False, 'message': f'發送失敗: {str(e)}'})
    
    # 原始 POST 處理（向後兼容）
    try:
        user = request.user
        logger.info(f"=== Email verify requested by user {user.id} ({user.email}) ===")
        
        if not user.email:
            logger.warning(f"User {user.id} has no email address")
            messages.error(request, "No email address is set for your account")
            return redirect('socialuser:profile')
        
        # Force create email address record if doesn't exist
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={
                'primary': True,
                'verified': False
            }
        )
        logger.info(f"EmailAddress record: {email_address.email}, verified={email_address.verified}, created={created}")
        
        # Resend confirmation if not verified
        if not email_address.verified:
            logger.info(f"Attempting to send confirmation email to {user.email}")
            try:
                email_address.send_confirmation(request)
                logger.info(f"Confirmation email sent successfully to {user.email}")
                messages.success(request, f"Verification email sent to {user.email}")
            except Exception as send_err:
                logger.error(f"Failed to send confirmation email: {send_err}", exc_info=True)
                messages.error(request, f"Failed to send email: {send_err}")
        else:
            logger.info(f"Email {user.email} is already verified")
            messages.info(request, "Email is already verified")
            
        return redirect('socialuser:profile')
    
    except Exception as e:
        logger.error(f"Email verification error: {e}", exc_info=True)
        messages.error(request, f"Email verification failed: {str(e)}")
        return redirect('socialuser:profile')





# AJAX / htmx : profile.html
@login_required
def profile_usernamechange(request):
    from django.http import JsonResponse
    
    # AJAX 請求處理
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            form = UsernameForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': '用戶名稱更新成功',
                    'username': request.user.username
                })
            return JsonResponse({'success': False, 'message': '用戶名稱無效或已被使用'})
        return JsonResponse({'success': False, 'message': '僅支援 POST 請求'})
    
    # htmx 處理（向後兼容）
    if request.htmx:
        form = UsernameForm(instance=request.user)
        return render(request, 'socialuser/username_form.html', {'form':form})
    
    # 原始 POST 處理（向後兼容）
    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully.')
            return redirect('socialuser:profile')
        else:
            messages.warning(request, 'Username not valid or already in use')
            return redirect('socialuser:profile')
    
    return redirect('socialuser:profile')    



# AJAX / htmx : profile.html
@login_required
def profile_phonechange(request):
    from django.http import JsonResponse
    
    # AJAX 請求處理
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            profile = request.user.profile
            form = PhoneForm(request.POST, instance=profile)
            if form.is_valid():
                profile.phone = form.cleaned_data['phone']
                profile.save()
                return JsonResponse({
                    'success': True,
                    'message': '電話號碼更新成功',
                    'phone': profile.hk_phone()
                })
            return JsonResponse({'success': False, 'message': '無效的電話號碼格式，請輸入8位數字'})
        return JsonResponse({'success': False, 'message': '僅支援 POST 請求'})
    
    # htmx 處理（向後兼容）
    if request.htmx:
        profile = request.user.profile
        initial_phone = profile.hk_phone() or ""
        form = PhoneForm(instance=profile, initial={'phone': initial_phone})
        return render(request, 'socialuser/phone_form.html', {'form': form})
    
    # 原始 POST 處理（向後兼容）
    if request.method == 'POST':
        profile = request.user.profile
        form = PhoneForm(request.POST, instance=profile)
        if form.is_valid():
            profile.phone = form.cleaned_data['phone']
            profile.save()
            messages.success(request, '電話號碼更新成功')
            return redirect('socialuser:profile')
        else:
            messages.warning(request, '無效的電話號碼格式')
            return redirect('socialuser:profile')
    
    return redirect('socialuser:profile')



@login_required
def profile_avatar_ajax(request):
    """AJAX 頭像上傳"""
    from django.http import JsonResponse
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        profile = request.user.profile
        form = AvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': '頭像更新成功',
                'avatar_url': profile.avatar
            })
        return JsonResponse({'success': False, 'message': '頭像上傳失敗，請確認檔案格式正確'})
    
    return JsonResponse({'success': False, 'message': '僅支援 AJAX POST 請求'})


@login_required
def profile_info_ajax(request):
    """AJAX 個人簡介更新"""
    from django.http import JsonResponse
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        profile = request.user.profile
        info = request.POST.get('info', '').strip()
        profile.info = info
        profile.save()
        return JsonResponse({
            'success': True,
            'message': '個人簡介更新成功',
            'info': info
        })
    
    return JsonResponse({'success': False, 'message': '僅支援 AJAX POST 請求'})


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
    
    return redirect('socialuser:profile')


# Login cancel route to localhost
class CustomLoginCancelledView(AllAuthLoginCancelledView):
    template_name = 'socialuser/login_cancelled.html'