# eshop/management/commands/fix_orders_comprehensive.py
from django.core.management.base import BaseCommand
from eshop.models import OrderModel, CoffeeItem, BeanItem
import json

class Command(BaseCommand):
    help = '全面修复订单数据，包括格式问题和缺失字段'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制修复所有订单，即使没有发现问题',
        )

    def handle(self, *args, **options):
        self.stdout.write('开始全面修复订单数据...')
        
        orders = OrderModel.objects.all()
        total_orders = orders.count()
        fixed_count = 0
        
        self.stdout.write(f'找到 {total_orders} 个订单需要检查')
        
        for i, order in enumerate(orders, 1):
            try:
                self.stdout.write(f'处理订单 {i}/{total_orders}: ID={order.id}')
                
                # 获取订单项目
                items = self.get_order_items(order)
                
                if items is None:
                    self.stdout.write(f'  订单 {order.id} 的项目数据格式无效，尝试重置')
                    items = self.create_default_items()
                    needs_save = True
                else:
                    needs_save = False
                
                # 修复每个项目
                for item in items:
                    if not isinstance(item, dict):
                        self.stdout.write(f'  订单 {order.id} 的项目不是字典格式，跳过: {item}')
                        continue
                    
                    # 确保所有必要字段都存在
                    item_needs_fix = self.fix_item_fields(order.id, item)
                    if item_needs_fix:
                        needs_save = True
                
                # 如果需要保存，更新订单
                if needs_save or options['force']:
                    order.items = items
                    order.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  订单 {order.id} 已修复'))
                else:
                    self.stdout.write(f'  订单 {order.id} 无需修复')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  处理订单 {order.id} 时出错: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'修复完成！共处理 {total_orders} 个订单，修复了 {fixed_count} 个订单')
        )
    
    def get_order_items(self, order):
        """安全地获取订单项目，处理各种格式问题"""
        try:
            # 如果 items 是 None 或空字符串，返回空列表
            if order.items is None or order.items == "":
                return []
            
            # 如果 items 是字符串，尝试解析为 JSON
            if isinstance(order.items, str):
                try:
                    items = json.loads(order.items)
                except json.JSONDecodeError:
                    # 尝试处理可能的格式问题
                    cleaned_str = order.items.strip()
                    if cleaned_str.startswith('"') and cleaned_str.endswith('"'):
                        cleaned_str = cleaned_str[1:-1]
                    
                    try:
                        items = json.loads(cleaned_str)
                    except:
                        self.stdout.write(f'  订单 {order.id} 的 items 不是有效的 JSON: {order.items}')
                        return None
            
            # 如果 items 是字典，将其包装在列表中
            elif isinstance(order.items, dict):
                items = [order.items]
            
            # 如果 items 是列表，直接使用
            elif isinstance(order.items, list):
                items = order.items
            
            else:
                self.stdout.write(f'  订单 {order.id} 的 items 格式未知: {type(order.items)}')
                return None
            
            # 确保 items 是列表
            if not isinstance(items, list):
                items = [items]
            
            # 过滤掉非字典元素
            valid_items = []
            for item in items:
                if isinstance(item, dict):
                    valid_items.append(item)
                else:
                    self.stdout.write(f'  订单 {order.id} 的项目不是字典: {item}')
            
            return valid_items
            
        except Exception as e:
            self.stdout.write(f'  获取订单 {order.id} 的项目时出错: {e}')
            return None
    
    def fix_item_fields(self, order_id, item):
        """修复单个项目的字段"""
        needs_fix = False
        
        # 确保必要的字段存在
        required_fields = {
            'id': 0,
            'name': '未知产品',
            'type': 'coffee',
            'quantity': 1,
            'price': '0.00',
        }
        
        for field, default_value in required_fields.items():
            if field not in item:
                self.stdout.write(f'  订单 {order_id} 的项目缺少 {field} 字段')
                item[field] = default_value
                needs_fix = True
        
        # 确保 price 是字符串格式
        if 'price' in item and not isinstance(item['price'], str):
            try:
                item['price'] = str(float(item['price']))
                needs_fix = True
            except (ValueError, TypeError):
                item['price'] = '0.00'
                needs_fix = True
        
        # 计算总价
        if 'total_price' not in item:
            try:
                price = float(item['price'])
                quantity = int(item['quantity'])
                item['total_price'] = str(price * quantity)
                needs_fix = True
            except (ValueError, TypeError):
                item['total_price'] = '0.00'
                needs_fix = True
        
        # 确保图片 URL 存在
        if 'image' not in item:
            item['image'] = '/static/images/default-product.png'
            needs_fix = True
        
        return needs_fix
    
    def create_default_items(self):
        """创建默认的项目列表"""
        return [{
            'id': 0,
            'name': '未知产品',
            'type': 'coffee',
            'quantity': 1,
            'price': '0.00',
            'total_price': '0.00',
            'image': '/static/images/default-product.png',
        }]