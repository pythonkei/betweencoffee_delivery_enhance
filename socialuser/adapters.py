from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.shortcuts import resolve_url
from django.urls import reverse


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Disable regular account signups, only allow social accounts
        """
        return False

    def save_user(self, request, user, form, commit=True):
        """
        Prevent saving users from regular signup forms
        """
        raise PermissionError("Regular account creation is disabled")

'''
# Disabled for regular accounts
class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Redirect to onboarding if profile is incomplete
        if (hasattr(request.user, 'profile') and 
            (not request.user.profile.phone or 
             not request.user.profile.displayname)):
            return reverse('profile-onboarding')
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        # Redirect to onboarding after signup
        return reverse('profile-onboarding')
'''

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Handle social login and connect to existing accounts if email matches
        """
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return

        try:
            existing_email = EmailAddress.objects.get(email=email)
            if existing_email.user != sociallogin.user:
                sociallogin.connect(request, existing_email.user)
        except EmailAddress.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Automatically verify emails from social providers
        """
        user = super().save_user(request, sociallogin, form)
        email = user.email
        
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={'verified': True, 'primary': True}
        )
        return user




# youtube tut: https://www.youtube.com/watch?v=dASjmItZcWE
'''
# OAuth - Social Logins with Django and Allauth - Google, Github, X and Facebook

# Linkup social and normal acc by same email auth and verify
class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin): # Auth process normal acc or social acc
        email = sociallogin.account.extra_data.get("email")

        if not email:
            return
        
        if sociallogin.is_existing: # if social acc exist link in database
            user = sociallogin.user
            email_address, created = EmailAddress.objects.get_or_create(user=user, email=email)
            if not email_address.verified:
                email_address.verified = True # Ture > Exist normal user sign in with social acc skip google side openID auth
                email_address.save()

    # Verified existing acc email compare social acc without use google open ID for auth
    def save_user(self, request, sociallogin, form = None):
        user = super().save_user(request, sociallogin, form)
        email = user.email
        email_address, created = EmailAddress.objects.get_or_create(user=user, email=email)
        if not email_address.verified:
            email_address.verified = True # Ture > Exist normal user sign in with social acc skip google side openID auth
            email_address.save()
    
        return user
'''