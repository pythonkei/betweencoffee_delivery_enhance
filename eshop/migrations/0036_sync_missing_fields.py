# Generated manually to sync model fields with database
# Adds missing columns that were defined in models.py but not created in the database
# 注意：這些欄位在資料庫中已經存在，所以使用 SeparateDatabaseAndState 只更新 Django state

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eshop', '0035_remove_ordermodel_name'),
    ]

    operations = [
        # 1. Add updated_at to CartItem (already exists in DB, update state only)
        # 2. Add position to CoffeeQueue (already exists in DB, update state only)
        # 3. Rename contact_phone to phone in OrderModel (already done in DB, update state only)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='cartitem',
                    name='updated_at',
                    field=models.DateTimeField(auto_now=True, null=True),
                ),
                migrations.AddField(
                    model_name='coffeequeue',
                    name='position',
                    field=models.PositiveIntegerField(default=0, verbose_name='位置'),
                ),
            ],
            database_operations=[],
        ),
        # 注意：contact_phone → phone 的重新命名已在資料庫中完成
        # 此處不再需要 RunSQL，因為 Django state 中的欄位名稱已經是 phone
    ]
