"""
生产环境准备检查
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from django.db import connection
from eshop.models import OrderModel

print("=== 生产环境准备检查 ===")

# 1. 检查数据库连接
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")

# 2. 检查 OrderModel 结构
order_fields = [f.name for f in OrderModel._meta.get_fields()]
removed_fields = ['is_paid', 'created_on', 'cup_size', 'pickup_time']

print(f"\n2. OrderModel 字段检查:")
for field in removed_fields:
    if field in order_fields:
        print(f"   ❌ {field} 仍然存在于模型中")
    else:
        print(f"   ✅ {field} 已成功移除")

# 3. 检查迁移状态
from django.db.migrations.recorder import MigrationRecorder
try:
    applied_migrations = MigrationRecorder(connection).applied_migrations()
    eshop_migrations = [m for m in applied_migrations if m[0] == 'eshop']
    print(f"\n3. 已应用的 eshop 迁移: {len(eshop_migrations)} 个")
    
    # 检查关键迁移
    key_migrations = ['0015_simplify_order_model']
    for migration in key_migrations:
        if ('eshop', migration) in applied_migrations:
            print(f"   ✅ {migration} 已应用")
        else:
            print(f"   ❌ {migration} 未应用")
except Exception as e:
    print(f"\n3. 检查迁移状态失败: {e}")

# 4. 功能快速检查
print("\n4. 功能快速检查:")
try:
    # 创建测试订单
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 尝试创建用户（如果不存在）
    user, created = User.objects.get_or_create(
        username='prod_check_user',
        defaults={'email': 'check@example.com'}
    )
    
    import json
    order = OrderModel.objects.create(
        user=user,
        name='生产检查订单',
        phone='00000000',
        items=json.dumps([{
            'type': 'coffee',
            'id': 1,
            'name': '生产检查咖啡',
            'price': 25.00,
            'quantity': 1
        }]),
        total_price=25.00,
        payment_status='pending',
        status='pending'
    )
    
    print(f"   ✅ 订单创建测试通过 (ID: {order.id})")
    
    # 测试支付状态更新
    order.payment_status = 'paid'
    order.status = 'waiting'
    order.save()
    print(f"   ✅ 支付状态更新测试通过")
    
    # 测试弃用字段访问
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = order.is_paid
        if w:
            print(f"   ✅ 弃用警告触发测试通过")
    
    # 清理测试数据
    order.delete()
    if created:
        user.delete()
        
except Exception as e:
    print(f"   ❌ 功能检查失败: {e}")

print("\n=== 检查完成 ===")
