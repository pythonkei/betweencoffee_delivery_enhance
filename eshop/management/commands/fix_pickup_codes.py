from django.core.management.base import BaseCommand
from eshop.models import OrderModel
import random
import string
from django.db import transaction


class Command(BaseCommand):
    help = '修复重复的取餐码，确保所有订单都有唯一的取餐码'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际修改数据库',
        )
        parser.add_argument(
            '--code',
            type=str,
            help='指定要修复的特定取餐码（默认为"0000"）',
            default='0000',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_code = options['code']
        
        self.stdout.write(f"开始修复取餐码为 '{target_code}' 的订单...")
        
        # 查找所有取餐码为指定值的订单
        orders = OrderModel.objects.filter(pickup_code=target_code)
        order_count = orders.count()
        
        if order_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"没有找到取餐码为 '{target_code}' 的订单")
            )
            return
        
        self.stdout.write(f"找到 {order_count} 个取餐码为 '{target_code}' 的订单")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(" dry-run 模式: 不会实际修改数据库")
            )
        
        # 使用事务确保数据一致性
        with transaction.atomic():
            updated_count = 0
            for order in orders:
                # 生成唯一取餐码
                new_code = self.generate_unique_pickup_code(order.id)
                
                if dry_run:
                    self.stdout.write(
                        f"订单 {order.id} 的取餐码将从 '{target_code}' 改为 '{new_code}' (模拟)"
                    )
                else:
                    order.pickup_code = new_code
                    order.save()
                    self.stdout.write(
                        f"订单 {order.id} 的取餐码已从 '{target_code}' 改为 '{new_code}'"
                    )
                
                updated_count += 1
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"成功更新 {updated_count} 个订单的取餐码")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"模拟更新 {updated_count} 个订单的取餐码")
                )
    
    def generate_unique_pickup_code(self, exclude_order_id=None):
        """生成唯一的4位数字取餐码"""
        max_attempts = 100  # 防止无限循环
        attempts = 0
        
        while attempts < max_attempts:
            # 生成4位随机数字
            new_code = ''.join(random.choices(string.digits, k=4))
            
            # 检查取餐码是否已存在（排除当前订单）
            query = OrderModel.objects.filter(pickup_code=new_code)
            if exclude_order_id:
                query = query.exclude(id=exclude_order_id)
            
            if not query.exists():
                return new_code
            
            attempts += 1
        
        # 如果尝试多次后仍然找不到唯一码，使用更复杂的方法
        # 使用订单ID和时间戳的组合
        import time
        timestamp = int(time.time())
        unique_code = f"{timestamp % 10000:04d}"  # 使用时间戳的最后4位
        
        # 确保这个码也是唯一的
        query = OrderModel.objects.filter(pickup_code=unique_code)
        if exclude_order_id:
            query = query.exclude(id=exclude_order_id)
        
        if not query.exists():
            return unique_code
        
        # 如果还是冲突，使用更复杂的方法
        return f"{timestamp % 10000:03d}{random.randint(0, 9)}"
    


'''
理命令来修复取餐码问题, 比直接操作数据库更安全，并且可以轻松重复使用。
# 使用管理命令修复取餐码
python manage.py validate_pickup_codes
# 如果发现重复，自动修复
python manage.py fix_pickup_codes
'''