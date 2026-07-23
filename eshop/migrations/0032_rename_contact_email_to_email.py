# Generated manually: Rename contact_email to email in OrderModel (database level)
# 資料庫中的欄位名稱是 contact_email，但 model 中定義的是 email
# 使用原始 SQL 直接修改資料庫欄位名稱
# 注意：如果 contact_email 欄位不存在（例如已經被重新命名過），則跳過此操作

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0031_add_cartitem_strength_level"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='eshop_ordermodel' AND column_name='contact_email'
                    ) THEN
                        ALTER TABLE eshop_ordermodel RENAME COLUMN contact_email TO email;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='eshop_ordermodel' AND column_name='email'
                    ) THEN
                        ALTER TABLE eshop_ordermodel RENAME COLUMN email TO contact_email;
                    END IF;
                END $$;
            """,
        ),
    ]
