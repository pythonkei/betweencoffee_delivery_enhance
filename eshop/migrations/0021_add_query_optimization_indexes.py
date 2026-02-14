# eshop/migrations/0021_add_query_optimization_indexes.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        # 根據實際情況設置依賴
        ('eshop', '0020_convert_1kg_to_500g'),
    ]

    operations = [
        # 為 OrderModel 添加索引
        migrations.AddIndex(
            model_name='ordermodel',
            index=models.Index(fields=['is_quick_order', 'status'], name='idx_order_quick_status'),
        ),
        migrations.AddIndex(
            model_name='ordermodel',
            index=models.Index(fields=['payment_status', 'created_at'], name='idx_order_payment_created'),
        ),
        migrations.AddIndex(
            model_name='ordermodel',
            index=models.Index(fields=['pickup_time_choice'], name='idx_order_pickup_choice'),
        ),
        
        # 為 CoffeeQueue 添加索引
        migrations.AddIndex(
            model_name='coffeequeue',
            index=models.Index(fields=['status', 'position'], name='idx_queue_status_position'),
        ),
        migrations.AddIndex(
            model_name='coffeequeue',
            index=models.Index(fields=['estimated_start_time'], name='idx_queue_est_start'),
        ),
    ]