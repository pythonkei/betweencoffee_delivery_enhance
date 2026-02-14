# socialuser/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from .models import Profile
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings
import os


@receiver(post_migrate)
def update_site_domain(sender, **kwargs):
    """在数据库迁移后更新站点域名"""
    if sender.name == 'socialuser':
        try:
            is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
            
            if is_railway:
                domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6a798.up.railway.app')
                name = 'Between Coffee - Railway'
            else:
                domain = 'localhost:8081'
                name = 'Between Coffee - Local'
            
            site, created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={'domain': domain, 'name': name}
            )
            
            if not created and (site.domain != domain or site.name != name):
                site.domain = domain
                site.name = name
                site.save()
                print(f"Site domain updated to: {domain}")
                
        except Exception as e:
            print(f"Error updating site domain: {e}")
            

@receiver(post_save, sender=User)       
def user_postsave(sender, instance, created, **kwargs):
    user = instance
    
    # add profile if user is created
    if created:
        Profile.objects.create(
            user = user,
        )
    else:
        # update allauth emailaddress if exists 
        try:
            email_address = EmailAddress.objects.get_primary(user)
            if email_address.email != user.email:
                email_address.email = user.email
                email_address.verified = False
                email_address.save()
        except:
            # if allauth emailaddress doesn't exist create one
            EmailAddress.objects.create(
                user = user,
                email = user.email, 
                primary = True,
                verified = False
            )


@receiver(pre_save, sender=User)
def user_presave(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.lower()


@receiver(pre_delete, sender=User)
def user_predelete(sender, instance, **kwargs):
    # Skip processing if user is already soft-deleted
    if hasattr(instance, 'profile') and instance.profile.is_deleted:
        return
        
    from eshop.models import OrderModel
    from cart.models import Cart, CartItem
    
    # Anonymize orders when user is deleted
    OrderModel.objects.filter(user=instance).update(
        user=None,
        email=f'deleted_user_{instance.id}@example.com'
    )
    
    # Delete cart items
    CartItem.objects.filter(user=instance).delete()
    
    # Handle Cart objects
    Cart.objects.filter(user=instance).delete()