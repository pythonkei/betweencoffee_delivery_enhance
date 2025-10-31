# eshop/migrations/0030_fix_duplicate_pickup_codes.py
from django.db import migrations
import random
import string

def generate_unique_pickup_code():
    """生成4位唯一数字取餐码"""
    return ''.join(random.choices(string.digits, k=4))

def fix_duplicate_pickup_codes(apps, schema_editor):
    OrderModel = apps.get_model('eshop', 'OrderModel')
    
    # 查找所有取餐码为"0000"的订单
    orders_with_0000 = OrderModel.objects.filter(pickup_code='0000')
    
    # 为每个订单生成唯一的取餐码
    for order in orders_with_0000:
        while True:
            new_code = generate_unique_pickup_code()
            # 确保新码是唯一的
            if not OrderModel.objects.filter(pickup_code=new_code).exists():
                order.pickup_code = new_code
                order.save()
                break

class Migration(migrations.Migration):
    dependencies = [
        ('eshop', '0030_alter_ordermodel_pickup_code'),  # 替换为实际的上一迁移
    ]

    operations = [
        migrations.RunPython(fix_duplicate_pickup_codes),
    ]