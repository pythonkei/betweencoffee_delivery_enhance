# Generated manually to sync model fields with database
# Adds missing columns that were defined in models.py but not created in the database

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eshop', '0035_remove_ordermodel_name'),
    ]

    operations = [
        # 1. Add updated_at to CartItem (defined in model but missing in DB)
        migrations.AddField(
            model_name='cartitem',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        # 2. Add position to CoffeeQueue (defined in model but missing in DB)
        migrations.AddField(
            model_name='coffeequeue',
            name='position',
            field=models.PositiveIntegerField(default=0, verbose_name='位置'),
        ),
        # 3. Rename contact_phone to phone in OrderModel to match model definition
        # 注意：如果 contact_phone 欄位不存在（例如已經被重新命名過），則跳過此操作
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='eshop_ordermodel' AND column_name='contact_phone'
                    ) THEN
                        ALTER TABLE eshop_ordermodel RENAME COLUMN contact_phone TO phone;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='eshop_ordermodel' AND column_name='phone'
                    ) THEN
                        ALTER TABLE eshop_ordermodel RENAME COLUMN phone TO contact_phone;
                    END IF;
                END $$;
            """,
        ),
    ]
