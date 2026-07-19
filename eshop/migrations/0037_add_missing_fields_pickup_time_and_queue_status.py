# Generated manually to add missing fields that exist in models.py but not in database
# Adds pickup_time_choice to OrderModel and status to CoffeeQueue
# 注意：這些欄位在資料庫中已經存在，使用 SeparateDatabaseAndState 只更新 Django state

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eshop', '0036_sync_missing_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # 1. Add pickup_time_choice to OrderModel (already exists in DB)
                migrations.AddField(
                    model_name='ordermodel',
                    name='pickup_time_choice',
                    field=models.CharField(
                        max_length=20,
                        choices=[
                            ('5', '5分鐘後'),
                            ('10', '10分鐘後'),
                            ('15', '15分鐘後'),
                            ('20', '20分鐘後'),
                            ('30', '30分鐘後'),
                        ],
                        default='5',
                        verbose_name='取貨時間選擇'
                    ),
                ),
                # 2. Add status to CoffeeQueue (already exists in DB)
                migrations.AddField(
                    model_name='coffeequeue',
                    name='status',
                    field=models.CharField(
                        max_length=20,
                        choices=[
                            ('waiting', '等待中'),
                            ('preparing', '制作中'),
                            ('ready', '已就緒'),
                            ('completed', '已完成'),
                        ],
                        default='waiting'
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
