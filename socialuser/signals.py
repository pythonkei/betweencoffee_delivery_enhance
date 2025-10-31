# socialuser/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from .models import Profile


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