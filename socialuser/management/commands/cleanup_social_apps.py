from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Clean up duplicate SocialApp configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        for provider in ['google', 'facebook']:
            self.stdout.write(f"Checking {provider}...")
            apps = SocialApp.objects.filter(provider=provider)
            
            if apps.count() <= 1:
                self.stdout.write(f"  ✓ Only {apps.count()} {provider} app(s) - no cleanup needed")
                continue
            
            # 保留第一个，删除其余的
            keep_app = apps.first()
            delete_apps = apps.exclude(id=keep_app.id)
            
            self.stdout.write(f"  ! Found {apps.count()} {provider} apps:")
            self.stdout.write(f"    → Keep: {keep_app.name} (ID: {keep_app.id})")
            
            for app in delete_apps:
                self.stdout.write(f"    × Delete: {app.name} (ID: {app.id})")
            
            if not dry_run and delete_apps.exists():
                count, _ = delete_apps.delete()
                self.stdout.write(f"  ✓ Deleted {count} duplicate {provider} app(s)")
        
        self.stdout.write("Cleanup completed!")