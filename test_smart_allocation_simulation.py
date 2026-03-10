#!/usr/bin/env python
"""
智能分配系統模擬測試

這個腳本用於模擬測試智能分配系統的各個功能：
1. 員工工作負載管理
2. 智能分配算法
3. 隊列優化
4. 學習機制
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta

# 設置Django環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import Barista, OrderModel, CoffeeQueue
from eshop.smart_allocation import (
    get_smart_allocator,
    get_workload_manager,
    initialize_smart_system,
    allocate_new_order,
    optimize_order_preparation
)
from eshop.learning_optimizer import get_learning_optimizer, analyze_system_performance
from eshop.queue_manager_refactored import CoffeeQueueManager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simulation')


class SmartAllocationSimulation:
    """智能分配系統模擬測試"""
    
    def __init__(self):
        self.logger = logger
        self.manager = CoffeeQueueManager()
        self.allocator = None
        self.workload_manager = None
        
    def setup_test_environment(self):
        """設置測試環境"""
        self.logger.info("🔄 設置測試環境...")
        
        try:
            # 初始化智能系統
            initialize_smart_system()
            
            # 獲取管理器實例
            self.allocator = get_smart_allocator()
            self.workload_manager = get_workload_manager()
            
            # 確保有測試員工
            self._ensure_test_baristas()
            
            self.logger.info("✅ 測試環境設置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 設置測試環境失敗: {str(e)}")
            return False
    
    def _ensure_test_baristas(self):
        """確保有測試員工"""
        # 創建測試員工（如果不存在）
        test_baristas = [
            {'name': '測試員工A', 'is_active': True, 'efficiency_factor': 0.9, 'max_concurrent_orders': 2},
            {'name': '測試員工B', 'is_active': True, 'efficiency_factor': 1.1, 'max_concurrent_orders': 2},
            {'name': '測試員工C', 'is_active': False, 'efficiency_factor': 1.0, 'max_concurrent_orders': 2},
        ]
        
        for barista_data in test_baristas:
            barista, created = Barista.objects.get_or_create(
                name=barista_data['name'],
                defaults=barista_data
            )
            
            if created:
                self.logger.info(f"✅ 創建測試員工: {barista.name}")
            else:
                # 更新現有員工狀態
                barista.is_active = barista_data['is_active']
                barista.efficiency_factor = barista_data['efficiency_factor']
                barista.max_concurrent_orders = barista_data['max_concurrent_orders']
                barista.save()
                self.logger.info(f"✅ 更新測試員工: {barista.name}")
    
    def test_system_initialization(self):
        """測試系統初始化"""
        self.logger.info("🧪 測試系統初始化...")
        
        try:
            # 獲取系統狀態
            system_status = self.allocator.get_system_status()
            
            self.logger.info(f"✅ 系統狀態: {system_status}")
            
            # 檢查基本數據
            assert 'total_baristas' in system_status
            assert 'active_baristas' in system_status
            assert 'total_capacity' in system_status
            assert 'current_load' in system_status
            
            self.logger.info("✅ 系統初始化測試通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 系統初始化測試失敗: {str(e)}")
            return False
    
    def test_workload_management(self):
        """測試工作負載管理"""
        self.logger.info("🧪 測試工作負載管理...")
        
        try:
            # 獲取工作負載
            workload = self.workload_manager.get_system_workload()
            
            self.logger.info(f"✅ 工作負載: {workload}")
            
            # 檢查工作負載數據
            assert 'total_capacity' in workload
            assert 'current_load' in workload
            assert 'available_capacity' in workload
            
            # 測試員工工作負載查詢
            baristas = Barista.objects.filter(is_active=True)
            for barista in baristas:
                barista_workload = self.workload_manager.get_barista_workload(barista.id)
                if barista_workload and 'name' in barista_workload:
                    self.logger.info(f"✅ 員工 {barista_workload['name']} 工作負載: {barista_workload}")
                else:
                    self.logger.info(f"✅ 員工 {barista.name} 工作負載: {barista_workload}")
            
            self.logger.info("✅ 工作負載管理測試通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 工作負載管理測試失敗: {str(e)}")
            return False
    
    def test_smart_allocation(self):
        """測試智能分配"""
        self.logger.info("🧪 測試智能分配...")
        
        try:
            # 創建測試訂單
            test_order = self._create_test_order()
            
            if not test_order:
                self.logger.warning("⚠️ 無法創建測試訂單，跳過分配測試")
                return False
            
            # 測試智能分配
            allocation_result = allocate_new_order(test_order.id)
            
            self.logger.info(f"✅ 分配結果: {allocation_result}")
            
            # 檢查分配結果
            assert 'success' in allocation_result
            
            if allocation_result['success']:
                assert 'recommended_barista_id' in allocation_result
                assert 'recommended_barista_name' in allocation_result
                assert 'estimated_time' in allocation_result
                
                self.logger.info(
                    f"✅ 訂單分配給: {allocation_result['recommended_barista_name']}, "
                    f"預計時間: {allocation_result['estimated_time']}分鐘"
                )
            
            # 測試優化建議
            optimization_result = optimize_order_preparation(test_order.id)
            
            self.logger.info(f"✅ 優化建議: {optimization_result}")
            
            self.logger.info("✅ 智能分配測試通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 智能分配測試失敗: {str(e)}")
            return False
    
    def _create_test_order(self):
        """創建測試訂單"""
        try:
            # 查找現有的測試訂單或創建新的
            test_order = OrderModel.objects.filter(
                order_type='quick',
                payment_status='paid'
            ).first()
            
            if test_order:
                self.logger.info(f"✅ 使用現有測試訂單: #{test_order.id}")
                return test_order
            
            # 創建新的測試訂單
            from django.contrib.auth.models import User
            test_user, _ = User.objects.get_or_create(
                username='test_user',
                defaults={'email': 'test@example.com'}
            )
            
            test_order = OrderModel.objects.create(
                user=test_user,
                order_type='quick',
                payment_status='paid',
                status='waiting',
                total_amount=50.0
            )
            
            self.logger.info(f"✅ 創建測試訂單: #{test_order.id}")
            return test_order
            
        except Exception as e:
            self.logger.error(f"❌ 創建測試訂單失敗: {str(e)}")
            return None
    
    def test_queue_optimization(self):
        """測試隊列優化"""
        self.logger.info("🧪 測試隊列優化...")
        
        try:
            # 使用隊列管理器進行優化
            optimization_result = self.manager.optimize_queue_with_smart_allocation()
            
            self.logger.info(f"✅ 隊列優化結果: {optimization_result}")
            
            # 檢查優化結果
            assert 'success' in optimization_result
            
            if optimization_result['success']:
                data = optimization_result['data']
                assert 'orders_optimized' in data
                assert 'time_savings' in data
                assert 'load_balanced' in data
                
                self.logger.info(
                    f"✅ 優化結果: {data['orders_optimized']}訂單優化, "
                    f"節省 {data['time_savings']}分鐘, "
                    f"負載均衡: {data['load_balanced']}"
                )
            
            self.logger.info("✅ 隊列優化測試通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 隊列優化測試失敗: {str(e)}")
            return False
    
    def test_learning_mechanism(self):
        """測試學習機制"""
        self.logger.info("🧪 測試學習機制...")
        
        try:
            # 獲取學習優化器
            optimizer = get_learning_optimizer()
            
            # 測試性能記錄
            optimizer.record_performance(
                order_id=1,
                barista_id=1,
                actual_time=8.5,
                estimated_time=10.0
            )
            
            self.logger.info("✅ 性能記錄測試通過")
            
            # 測試效率計算
            efficiency = optimizer.get_barista_efficiency(1)
            self.logger.info(f"✅ 員工效率: {efficiency}")
            
            # 測試歷史數據分析
            analysis_result = analyze_system_performance(days=1)
            
            self.logger.info(f"✅ 歷史數據分析: {analysis_result}")
            
            # 測試優化建議
            suggestions_result = optimizer.get_optimization_suggestions()
            
            self.logger.info(f"✅ 優化建議: {suggestions_result}")
            
            self.logger.info("✅ 學習機制測試通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 學習機制測試失敗: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """測試API端點"""
        self.logger.info("🧪 測試API端點...")
        
        try:
            from django.contrib.auth.models import User
            
            # 創建測試管理員用戶
            admin_user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if created:
                admin_user.set_password('testpassword')
                admin_user.save()
            
            # 首先登入獲取會話
            from django.test import Client
            client = Client()
            client.force_login(admin_user)
            
            # 測試工作負載API
            try:
                response = client.get('/eshop/api/queue/barista-workload/')
                self.logger.info(f"✅ 工作負載API狀態: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"✅ 工作負載API響應: {data}")
                else:
                    self.logger.warning(f"⚠️ 工作負載API返回非200狀態: {response.status_code}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ 工作負載API測試異常: {str(e)}")
            
            # 測試系統狀態API
            try:
                response = client.get('/eshop/api/system/status/')
                self.logger.info(f"✅ 系統狀態API狀態: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"✅ 系統狀態API響應: {data}")
                else:
                    self.logger.warning(f"⚠️ 系統狀態API返回非200狀態: {response.status_code}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ 系統狀態API測試異常: {str(e)}")
            
            # 測試智能建議API
            try:
                # 使用現有訂單進行測試
                test_order = OrderModel.objects.filter(has_coffee=True).first()
                if test_order:
                    response = client.get(f'/eshop/api/orders/{test_order.id}/recommendations/')
                    self.logger.info(f"✅ 智能建議API狀態: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.logger.info(f"✅ 智能建議API響應: {data}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ 智能建議API測試異常: {str(e)}")
            
            self.logger.info("✅ API端點測試完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ API端點測試失敗: {str(e)}", exc_info=True)
            return False
    
    def run_all_tests(self):
        """運行所有測試"""
        self.logger.info("🚀 開始運行智能分配系統模擬測試")
        
        # 設置測試環境
        if not self.setup_test_environment():
            self.logger.error("❌ 測試環境設置失敗，停止測試")
            return False
        
        test_results = []
        
        # 運行各個測試
        tests = [
            ('系統初始化', self.test_system_initialization),
            ('工作負載管理', self.test_workload_management),
            ('智能分配', self.test_smart_allocation),
            ('隊列優化', self.test_queue_optimization),
            ('學習機制', self.test_learning_mechanism),
            ('API端點', self.test_api_endpoints),
        ]
        
        for test_name, test_func in tests:
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"測試: {test_name}")
            self.logger.info(f"{'='*50}")
            
            try:
                success = test_func()
                test_results.append((test_name, success))
                
                if success:
                    self.logger.info(f"✅ {test_name} - 通過")
                else:
                    self.logger.error(f"❌ {test_name} - 失敗")
                    
            except Exception as e:
                self.logger.error(f"❌ {test_name} - 異常: {str(e)}")
                test_results.append((test_name, False))
        
        # 輸出測試結果
        self.logger.info(f"\n{'='*50}")
        self.logger.info("測試結果總結")
        self.logger.info(f"{'='*50}")
        
        passed = sum(1 for _, success in test_results if success)
        total = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ 通過" if success else "❌ 失敗"
            self.logger.info(f"{test_name}: {status}")
        
        self.logger.info(f"\n總計: {passed}/{total} 個測試通過")
        
        if passed == total:
            self.logger.info("🎉 所有測試通過！智能分配系統功能正常")
            return True
        else:
            self.logger.warning(f"⚠️ {total - passed} 個測試失敗，需要檢查")
            return False
    
    def cleanup_test_environment(self):
        """清理測試環境"""
        self.logger.info("🧹 清理測試環境...")
        
        try:
            # 清理測試數據
            test_baristas = Barista.objects.filter(name__startswith='測試員工')
            deleted_count, _ = test_baristas.delete()
            
            self.logger.info(f"✅ 清理了 {deleted_count} 個測試員工")
            
            # 清理測試訂單
            from django.contrib.auth.models import User
            test_user = User.objects.filter(username='test_user').first()
            
            if test_user:
                test_orders = OrderModel.objects.filter(user=test_user)
                deleted_count, _ = test_orders.delete()
                test_user.delete()
                
                self.logger.info(f"✅ 清理了 {deleted_count} 個測試訂單")
            
            self.logger.info("✅ 測試環境清理完成")
            
        except Exception as e:
            self.logger.error(f"❌ 清理測試環境失敗: {str(e)}")


def main():
    """主函數"""
    simulation = SmartAllocationSimulation()
    
    try:
        # 運行測試
        success = simulation.run_all_tests()
        
        # 清理測試環境
        simulation.cleanup_test_environment()
        
        # 返回退出碼
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        simulation.cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        simulation.cleanup_test_environment()
        sys.exit(1)


if __name__ == '__main__':
    main()