#!/usr/bin/env python
"""
測試隊列修復 - 驗證開始制作按鈕功能
"""

import os
import sys
import logging

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.views.queue_views import start_preparation_api
from django.test import RequestFactory
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class QueueFixTest:
    """隊列修復測試"""
    
    def __init__(self):
        self.results = {}
    
    def test_order_status_manager(self):
        """測試 OrderStatusManager.mark_as_preparing_manually"""
        print("\n=== 測試 OrderStatusManager.mark_as_preparing_manually ===")
        
        try:
            # 查找一個等待中的訂單
            waiting_order = OrderModel.objects.filter(
                status='waiting',
                payment_status='paid'
            ).first()
            
            if not waiting_order:
                print("⚠️ 沒有找到等待中的訂單，創建一個測試訂單...")
                # 創建一個測試訂單
                waiting_order = OrderModel.objects.create(
                    status='waiting',
                    payment_status='paid',
                    total_price=50.0,
                    name='測試客戶',
                    phone='12345678',
                    pickup_code='TEST123'
                )
                print(f"✅ 創建測試訂單 #{waiting_order.id}")
            
            print(f"✅ 找到等待中訂單: #{waiting_order.id}")
            
            # 測試 mark_as_preparing_manually
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=waiting_order.id,
                barista_name='測試員工'
            )
            
            if result['success']:
                print(f"✅ mark_as_preparing_manually 成功: {result['message']}")
                
                # 檢查訂單狀態是否更新
                order = OrderModel.objects.get(id=waiting_order.id)
                if order.status == 'preparing':
                    print(f"✅ 訂單狀態已更新為 preparing")
                else:
                    print(f"❌ 訂單狀態未正確更新: {order.status}")
                
                # 檢查隊列項
                queue_item = CoffeeQueue.objects.filter(order=order).first()
                if queue_item and queue_item.status == 'preparing':
                    print(f"✅ 隊列項狀態已更新為 preparing")
                else:
                    print(f"⚠️ 隊列項未找到或狀態不正確")
                
                self.results['order_status_manager'] = {
                    'success': True,
                    'order_id': waiting_order.id,
                    'result': result
                }
            else:
                print(f"❌ mark_as_preparing_manually 失敗: {result['message']}")
                self.results['order_status_manager'] = {
                    'success': False,
                    'error': result['message']
                }
            
            return result
            
        except Exception as e:
            print(f"❌ 測試失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def test_start_preparation_api(self):
        """測試 start_preparation_api 視圖"""
        print("\n=== 測試 start_preparation_api 視圖 ===")
        
        try:
            # 創建測試用戶
            test_user, created = User.objects.get_or_create(
                username='test_staff',
                defaults={
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                test_user.set_password('test123')
                test_user.save()
                print(f"✅ 創建測試員工用戶: {test_user.username}")
            
            # 查找一個等待中的訂單
            waiting_order = OrderModel.objects.filter(
                status='waiting',
                payment_status='paid'
            ).first()
            
            if not waiting_order:
                print("⚠️ 沒有找到等待中的訂單，創建一個測試訂單...")
                waiting_order = OrderModel.objects.create(
                    status='waiting',
                    payment_status='paid',
                    total_price=60.0,
                    name='API測試客戶',
                    phone='87654321',
                    pickup_code='API123'
                )
                print(f"✅ 創建API測試訂單 #{waiting_order.id}")
            
            print(f"✅ 找到等待中訂單: #{waiting_order.id}")
            
            # 創建請求
            factory = RequestFactory()
            request = factory.post(f'/eshop/queue/start/{waiting_order.id}/')
            request.user = test_user
            
            # 測試API
            response = start_preparation_api(request, waiting_order.id)
            
            if response.status_code == 200:
                print(f"✅ API 響應成功: {response.status_code}")
                print(f"響應內容: {response.content}")
                
                # 檢查訂單狀態
                order = OrderModel.objects.get(id=waiting_order.id)
                if order.status == 'preparing':
                    print(f"✅ 訂單狀態已通過API更新為 preparing")
                else:
                    print(f"❌ 訂單狀態未正確更新: {order.status}")
                
                self.results['start_preparation_api'] = {
                    'success': True,
                    'status_code': response.status_code,
                    'order_id': waiting_order.id
                }
            else:
                print(f"❌ API 響應失敗: {response.status_code}")
                print(f"響應內容: {response.content}")
                self.results['start_preparation_api'] = {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.content.decode('utf-8')
                }
            
            return response
            
        except Exception as e:
            print(f"❌ API測試失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_error_cases(self):
        """測試錯誤情況"""
        print("\n=== 測試錯誤情況 ===")
        
        tests = []
        
        # 測試1: 訂單不存在
        try:
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=999999,
                barista_name='測試員工'
            )
            
            if not result['success'] and '訂單不存在' in result['message']:
                print(f"✅ 測試1通過: 訂單不存在錯誤處理正確")
                tests.append({'name': '訂單不存在', 'success': True})
            else:
                print(f"❌ 測試1失敗: {result}")
                tests.append({'name': '訂單不存在', 'success': False})
        except Exception as e:
            print(f"❌ 測試1異常: {str(e)}")
            tests.append({'name': '訂單不存在', 'success': False})
        
        # 測試2: 訂單未支付
        try:
            # 創建一個未支付的訂單
            unpaid_order = OrderModel.objects.create(
                status='pending',
                payment_status='pending',
                total_price=30.0,
                name='未支付客戶',
                phone='11111111',
                pickup_code='UNPAID1'
            )
            
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=unpaid_order.id,
                barista_name='測試員工'
            )
            
            if not result['success'] and '未支付' in result['message']:
                print(f"✅ 測試2通過: 未支付訂單錯誤處理正確")
                tests.append({'name': '訂單未支付', 'success': True})
            else:
                print(f"❌ 測試2失敗: {result}")
                tests.append({'name': '訂單未支付', 'success': False})
            
            # 清理測試訂單
            unpaid_order.delete()
            
        except Exception as e:
            print(f"❌ 測試2異常: {str(e)}")
            tests.append({'name': '訂單未支付', 'success': False})
        
        # 測試3: 訂單狀態不允許
        try:
            # 創建一個已完成的訂單
            completed_order = OrderModel.objects.create(
                status='completed',
                payment_status='paid',
                total_price=40.0,
                name='已完成客戶',
                phone='22222222',
                pickup_code='DONE123'
            )
            
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=completed_order.id,
                barista_name='測試員工'
            )
            
            if not result['success']:
                print(f"✅ 測試3通過: 已完成訂單錯誤處理正確")
                tests.append({'name': '訂單狀態不允許', 'success': True})
            else:
                print(f"❌ 測試3失敗: {result}")
                tests.append({'name': '訂單狀態不允許', 'success': False})
            
            # 清理測試訂單
            completed_order.delete()
            
        except Exception as e:
            print(f"❌ 測試3異常: {str(e)}")
            tests.append({'name': '訂單狀態不允許', 'success': False})
        
        self.results['error_cases'] = tests
        return tests
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "="*60)
        print("📊 隊列修復測試報告")
        print("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        # OrderStatusManager 測試結果
        if 'order_status_manager' in self.results:
            result = self.results['order_status_manager']
            if result.get('success'):
                print(f"\n✅ OrderStatusManager.mark_as_preparing_manually: 通過")
                passed_tests += 1
            else:
                print(f"\n❌ OrderStatusManager.mark_as_preparing_manually: 失敗")
                print(f"   錯誤: {result.get('error')}")
            total_tests += 1
        
        # API 測試結果
        if 'start_preparation_api' in self.results:
            result = self.results['start_preparation_api']
            if result.get('success'):
                print(f"\n✅ start_preparation_api: 通過")
                passed_tests += 1
            else:
                print(f"\n❌ start_preparation_api: 失敗")
                print(f"   狀態碼: {result.get('status_code')}")
                print(f"   錯誤: {result.get('error')}")
            total_tests += 1
        
        # 錯誤情況測試結果
        if 'error_cases' in self.results:
            tests = self.results['error_cases']
            error_passed = sum(1 for test in tests if test.get('success'))
            error_total = len(tests)
            
            print(f"\n🧪 錯誤情況測試: {error_passed}/{error_total} 通過")
            
            for test in tests:
                status = "✅" if test.get('success') else "❌"
                print(f"   {status} {test['name']}")
            
            passed_tests += error_passed
            total_tests += error_total
        
        # 總結
        print(f"\n📈 測試總結:")
        print(f"  總測試數: {total_tests}")
        print(f"  通過數: {passed_tests}")
        print(f"  失敗數: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 所有測試通過！隊列修復成功。")
        else:
            print(f"\n⚠️ 有 {total_tests - passed_tests} 個測試失敗，需要進一步檢查。")
        
        print("\n" + "="*60)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'all_passed': passed_tests == total_tests
        }


def main():
    """主測試函數"""
    print("🚀 開始隊列修復測試")
    print("="*60)
    
    tester = QueueFixTest()
    
    try:
        # 執行測試
        tester.test_order_status_manager()
        tester.test_start_preparation_api()
        tester.test_error_cases()
        
        # 生成報告
        report = tester.generate_report()
        
        if report['all_passed']:
            print("✅ 隊列修復測試完成 - 所有測試通過！")
            return 0
        else:
            print("⚠️ 隊列修復測試完成 - 有測試失敗")
            return 1
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)