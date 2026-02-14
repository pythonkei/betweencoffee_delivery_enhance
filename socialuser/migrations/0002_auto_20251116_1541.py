# socialuser/migrations/0002_fix_site_domain.py
from django.db import migrations
from django.conf import settings
import os

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            'domain': os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8081'),
            'name': 'Between Coffee'
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('socialuser', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site_domain),
    ]