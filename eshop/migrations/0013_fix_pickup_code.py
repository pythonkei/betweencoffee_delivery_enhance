

from django.db import migrations, models

def create_unique_pickup_codes(apps, schema_editor):
    OrderModel = apps.get_model('eshop', 'OrderModel')
    
    # 为所有没有取餐码的订单生成取餐码
    orders_without_code = OrderModel.objects.filter(pickup_code='')
    for order in orders_without_code:
        # 生成新的取餐码
        import secrets
        import string
        
        for attempt in range(100):
            code = ''.join(secrets.choice(string.digits + string.ascii_uppercase) 
                          for _ in range(6))
            code = code.replace('0', '1').replace('O', '1').replace('I', '1').replace('L', '1')
            
            if not OrderModel.objects.filter(pickup_code=code).exists():
                order.pickup_code = code
                order.save()
                break

class Migration(migrations.Migration):
    dependencies = [
        ('eshop', '0012_barista_coffeepreparationtime_coffeequeue'),  # 替换为实际的依赖迁移
    ]

    operations = [
        migrations.RunPython(create_unique_pickup_codes),
    ]