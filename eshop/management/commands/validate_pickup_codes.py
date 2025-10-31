# eshop/management/commands/validate_pickup_codes.py
from django.core.management.base import BaseCommand
from eshop.models import OrderModel
from collections import Counter


class Command(BaseCommand):
    help = '验证所有订单的取餐码是否唯一'
    
    def handle(self, *args, **options):
        # 获取所有订单的取餐码
        pickup_codes = OrderModel.objects.values_list('pickup_code', flat=True)
        
        # 统计每个取餐码的出现次数
        code_counts = Counter(pickup_codes)
        
        # 找出重复的取餐码
        duplicate_codes = {code: count for code, count in code_counts.items() if count > 1}
        
        if duplicate_codes:
            self.stdout.write(
                self.style.ERROR("发现重复的取餐码:")
            )
            for code, count in duplicate_codes.items():
                self.stdout.write(
                    self.style.ERROR(f"  取餐码 '{code}' 出现了 {count} 次")
                )
            
            # 显示使用这些取餐码的订单
            for code in duplicate_codes:
                orders = OrderModel.objects.filter(pickup_code=code)
                self.stdout.write(f"  使用取餐码 '{code}' 的订单ID:")
                for order in orders:
                    self.stdout.write(f"    - {order.id} (创建于: {order.created_at})")
        else:
            self.stdout.write(
                self.style.SUCCESS("所有取餐码都是唯一的!")
            )
        
        # 显示统计信息
        total_codes = len(pickup_codes)
        unique_codes = len(code_counts)
        self.stdout.write(f"\n统计信息:")
        self.stdout.write(f"  总订单数: {total_codes}")
        self.stdout.write(f"  唯一取餐码数: {unique_codes}")
        self.stdout.write(f"  重复取餐码数: {len(duplicate_codes)}")


'''
理命令来修复取餐码问题, 比直接操作数据库更安全，并且可以轻松重复使用。
# 使用管理命令修复取餐码
python manage.py validate_pickup_codes
# 如果发现重复，自动修复
python manage.py fix_pickup_codes
'''比直接操作数据库更安全，并且可以轻松重复使用。