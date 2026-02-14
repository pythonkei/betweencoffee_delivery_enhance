# eshop/migrations/0020_convert_1kg_to_500g.py
from django.db import migrations

def convert_weight_1kg_to_500g(apps, schema_editor):
    """將現有數據中的1kg重量轉換為500g"""
    # 更新 CartItem 模型中的重量數據
    CartItem = apps.get_model('eshop', 'CartItem')
    
    # 找到所有重量為1kg的記錄
    items_to_update = CartItem.objects.filter(weight='1kg')
    count = items_to_update.count()
    
    if count > 0:
        print(f"找到 {count} 個需要更新的購物車項目（1kg → 500g）")
        items_to_update.update(weight='500g')
        print(f"已更新 {count} 個購物車項目的重量")

def reverse_convert_weight(apps, schema_editor):
    """回滾遷移（如果需要）"""
    CartItem = apps.get_model('eshop', 'CartItem')
    CartItem.objects.filter(weight='500g').update(weight='1kg')

class Migration(migrations.Migration):
    dependencies = [
        # 根據實際情況設置依賴
        ('eshop', '0019_rename_price_1kg_beanitem_price_500g'),
    ]
    
    operations = [
        migrations.RunPython(convert_weight_1kg_to_500g, reverse_convert_weight),
    ]