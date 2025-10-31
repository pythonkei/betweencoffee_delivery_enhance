# socialuser/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    # Set region to HK
    phone = PhoneNumberField(null=True, blank=True, region='HK')  
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.user)
    
    @property
    def name(self):
        if self.displayname:
            return self.displayname
        return self.user.username 
    
    @property
    def avatar(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}images/avatar.svg'
    
    def hk_phone(self):
        """Return phone number without country code"""
        if self.phone:
            try:
                # Handle PhoneNumber objects
                return str(self.phone.national_number)
            except AttributeError:
                # Handle string values
                if isinstance(self.phone, str) and self.phone.startswith('+852'):
                    return self.phone[4:]
                return self.phone
        return None
    
