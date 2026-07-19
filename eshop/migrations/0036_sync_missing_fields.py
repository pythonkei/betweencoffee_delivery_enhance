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
        # Use RunSQL only - no state_operations since model already has 'phone' not 'contact_phone'
        migrations.RunSQL(
            sql="ALTER TABLE eshop_ordermodel RENAME COLUMN contact_phone TO phone;",
            reverse_sql="ALTER TABLE eshop_ordermodel RENAME COLUMN phone TO contact_phone;",
        ),
    ]
