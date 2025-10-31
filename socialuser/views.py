# socialuser/views.py
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
from .forms import *
from eshop.models import OrderModel
from allauth.account.models import EmailAddress
from django.core.mail import send_mail, EmailMultiAlternatives
from allauth.socialaccount.views import LoginCancelledView as AllAuthLoginCancelledView



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
    
    if request.path == reverse('profile-onboarding'):
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
            return redirect('profile')
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
                return redirect('profile-settings')
            
            form.save()
            send_email_confirmation(request, request.user)
            messages.success(request, 'Email updated successfully. Verification email sent.')
            return redirect('profile-settings')
        
        # If form is invalid
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'socialuser/email_form.html', {'form': form})
    
    return redirect('profile-settings')



@login_required
def profile_emailverify(request):
    try:
        user = request.user
        if not user.email:
            messages.error(request, "No email address is set for your account")
            return redirect('profile-settings')
        
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
            
        return redirect('profile-settings')
    
    except Exception as e:
        messages.error(request, f"Email verification failed: {str(e)}")
        return redirect('profile-settings')




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
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Username not valid or already in use')
            return redirect('profile-settings')
    
    return redirect('profile-settings')    


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
            return redirect('profile-settings')
        else:
            messages.warning(request, '無效的電話號碼格式')
            return redirect('profile-settings')
    
    return redirect('profile-settings')


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
    orders = OrderModel.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'socialuser/order_history.html', {'orders': orders})


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
    
    return redirect('profile-settings')


# Login cancel route to localhost
class CustomLoginCancelledView(AllAuthLoginCancelledView):
    template_name = 'socialuser/login_cancelled.html'