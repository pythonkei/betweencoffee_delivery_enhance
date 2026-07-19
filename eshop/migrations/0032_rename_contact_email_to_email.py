# Generated manually: Rename contact_email to email in OrderModel (database level)
# 資料庫中的欄位名稱是 contact_email，但 model 中定義的是 email
# 使用原始 SQL 直接修改資料庫欄位名稱

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eshop', '0031_add_cartitem_strength_level'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE eshop_ordermodel RENAME COLUMN contact_email TO email;',
            reverse_sql='ALTER TABLE eshop_ordermodel RENAME COLUMN email TO contact_email;',
        ),
    ]
