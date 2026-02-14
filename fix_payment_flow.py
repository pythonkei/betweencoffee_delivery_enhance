#!/usr/bin/env python
"""
修復支付流程問題
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_order_status_manager():
    """修復 OrderStatusManager.process_payment_success 返回值問題"""
    file_path = "eshop/order_status_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 process_payment_success 方法
    import_pattern = "def process_payment_success(cls, order_id, request=None):"
    if import_pattern in content:
        # 替換返回值部分
        old_return = "        logger.info(f\"✅ 订单 {order_id} 支付成功处理完成（購物車已清空）\")\n        return True"
        new_return = '''        logger.info(f"✅ 订单 {order_id} 支付成功处理完成")
        
        # ✅ 修改：返回字典格式，包含成功狀態和訂單信息
        return {
            'success': True,
            'order_id': order_id,
            'order': order,
            'queue_item': queue_item,
            'message': '支付成功處理完成',
            'time_recalculated': time_result.get('success', False)
        }'''
        
        if old_return in content:
            content = content.replace(old_return, new_return)
            logger.info("✅ 已修復 OrderStatusManager.process_payment_success 返回值")
        else:
            logger.warning("⚠️  未找到舊的返回值格式，可能已修復")
        
        # 修改異常處理的返回值
        old_exception_return = "        return False"
        new_exception_return = '''        return {'success': False, 'message': f'處理失敗: {str(e)}', 'error': str(e)}'''
        
        if old_exception_return in content:
            content = content.replace(old_exception_return, new_exception_return)
            logger.info("✅ 已修復異常處理返回值")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def test_payment_flow():
    """測試支付流程"""
    from django.test import TestCase
    from eshop.models import OrderModel
    from eshop.order_status_manager import OrderStatusManager
    
    print("🧪 測試支付流程...")
    
    try:
        # 創建測試訂單
        order = OrderModel.objects.create(
            status='pending',
            payment_status='pending',
            items=[],
            total_price=100.00,
            payment_method='alipay'
        )
        
        print(f"📝 創建測試訂單 #{order.id}")
        
        # 測試支付成功處理
        result = OrderStatusManager.process_payment_success(order.id)
        
        if result.get('success'):
            print(f"✅ 支付成功處理返回正確格式: {result}")
        else:
            print(f"❌ 支付成功處理失敗: {result.get('message')}")
        
        order.refresh_from_db()
        print(f"📊 訂單狀態: status={order.status}, payment_status={order.payment_status}")
        
        # 清理
        order.delete()
        print("🧹 清理測試訂單")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

if __name__ == "__main__":
    # 添加項目路徑
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 設置 Django 環境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
    
    try:
        import django
        django.setup()
        
        # 執行修復
        fix_order_status_manager()
        
        print("\n🎯 修復完成！請測試以下功能：")
        print("1. 下單並使用支付寶付款")
        print("2. 查看訂單確認頁面是否正確顯示")
        print("3. 檢查訂單狀態是否正確更新")
        
    except Exception as e:
        print(f"❌ 設置 Django 環境失敗: {str(e)}")