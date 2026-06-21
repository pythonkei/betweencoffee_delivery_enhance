"""
Migration: 為 CoffeeQueue 添加 added_at 字段
- 新增 added_at 字段（auto_now_add=True）
- 為現有記錄填充 added_at 值
- 更新索引：移除舊的 (status, position) 索引，新增 (status, estimated_start_time) 和 added_at 索引
"""

from django.db import migrations, models
from django.utils import timezone


def populate_added_at(apps, schema_editor):
    """為現有 CoffeeQueue 記錄填充 added_at 值"""
    CoffeeQueue = apps.get_model('eshop', 'CoffeeQueue')
    db_alias = schema_editor.connection.alias
    
    for queue in CoffeeQueue.objects.using(db_alias).all():
        if not queue.added_at:
            # 使用 created_at 作為 added_at
            queue.added_at = queue.created_at or timezone.now()
            queue.save(update_fields=['added_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('eshop', '0027_beanitem_roast_level'),
    ]

    operations = [
        # 1. 新增 added_at 字段（先設為可為空）
        migrations.AddField(
            model_name='coffeequeue',
            name='added_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='加入隊列時間'),
        ),
        
        # 2. 為現有記錄填充 added_at
        migrations.RunPython(
            populate_added_at,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # 3. 修改 added_at 為不可為空（填充後）
        migrations.AlterField(
            model_name='coffeequeue',
            name='added_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='加入隊列時間'),
        ),
        
        # 4. 移除舊的 (status, position) 索引（來自 migration 0012）
        migrations.RemoveIndex(
            model_name='coffeequeue',
            name='eshop_coffe_status_212322_idx',
        ),
        
        # 5. 新增新的 (status, estimated_start_time) 索引
        migrations.AddIndex(
            model_name='coffeequeue',
            index=models.Index(fields=['status', 'estimated_start_time'], name='eshop_coffe_status_est_start_idx'),
        ),
        
        # 6. 新增 added_at 索引
        migrations.AddIndex(
            model_name='coffeequeue',
            index=models.Index(fields=['added_at'], name='eshop_coffe_added_at_idx'),
        ),
    ]
