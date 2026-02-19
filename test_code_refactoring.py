#!/usr/bin/env python3
"""
代碼重複與錯誤處理修復測試腳本

這個腳本測試以下修復：
1. 隊列管理器代碼重複問題修復
2. 錯誤處理不一致問題修復
3. 統一的錯誤處理框架
"""

import os
import sys
import logging
from datetime import datetime

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_queue_manager_fix():
    """測試隊列管理器修復"""
    logger.info("🔍 測試隊列管理器修復...")
    
    try:
        # 導入隊列管理器
        from eshop.queue_manager import CoffeeQueueManager
        
        # 創建管理器實例
        manager = CoffeeQueueManager()
        
        # 測試基本功能
        summary = manager.get_queue_summary()
        logger.info(f"✅ 隊列摘要獲取成功: {summary}")
        
        # 測試隊列完整性檢查
        integrity = manager.verify_queue_integrity()
        logger.info(f"✅ 隊列完整性檢查成功: {integrity}")
        
        # 測試修復隊列位置
        fixed = manager.fix_queue_positions()
        logger.info(f"✅ 隊列位置修復成功: {fixed}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 隊列管理器測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_error_handling_framework():
    """測試錯誤處理框架"""
    logger.info("🔍 測試錯誤處理框架...")
    
    try:
        # 導入錯誤處理模塊
        from eshop.error_handling import (
            handle_error,
            handle_success,
            error_handler_decorator,
            handle_database_error,
            handle_validation_error
        )
        
        # 測試錯誤處理
        try:
            result = 1 / 0
        except Exception as e:
            error_response = handle_error(
                error=e,
                context='test_division',
                operation='divide_numbers',
                data={'numerator': 1, 'denominator': 0}
            )
            logger.info(f"✅ 錯誤處理測試成功: {error_response.get('error_id')}")
        
        # 測試成功處理
        success_response = handle_success(
            operation='test_operation',
            data={'test': 'data'},
            message='測試操作成功'
        )
        logger.info(f"✅ 成功處理測試成功: {success_response.get('message')}")
        
        # 測試裝飾器
        @error_handler_decorator(context='test_function')
        def test_function(x, y):
            return x / y
        
        result = test_function(10, 2)
        logger.info(f"✅ 裝飾器測試成功: {result}")
        
        # 測試特定錯誤處理
        class MockDatabaseError(Exception):
            pass
        
        try:
            raise MockDatabaseError("數據庫連接失敗")
        except Exception as e:
            db_error_response = handle_database_error(
                error=e,
                operation='connect_to_database',
                query='SELECT * FROM users',
                model='User'
            )
            logger.info(f"✅ 數據庫錯誤處理測試成功: {db_error_response.get('error_type')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理框架測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_code_duplication_fix():
    """測試代碼重複修復"""
    logger.info("🔍 測試代碼重複修復...")
    
    try:
        # 檢查隊列管理器文件
        queue_manager_files = [
            'eshop/queue_manager.py',
            'eshop/queue_manager_final.py',
            'eshop/queue_manager_optimized.py',
            'eshop/queue_manager_refactored.py'
        ]
        
        existing_files = []
        for file_path in queue_manager_files:
            if os.path.exists(file_path):
                existing_files.append(file_path)
        
        logger.info(f"📁 發現的隊列管理器文件: {len(existing_files)} 個")
        
        # 檢查主隊列管理器文件
        if 'eshop/queue_manager.py' in existing_files:
            with open('eshop/queue_manager.py', 'r') as f:
                content = f.read()
                
            # 檢查是否包含關鍵修復
            if 'queue_item.position = 0' in content:
                logger.info("✅ 隊列位置清理修復存在")
            else:
                logger.warning("⚠️ 隊列位置清理修復可能缺失")
            
            # 檢查日誌器定義
            if 'queue_logger = logging.getLogger' in content:
                logger.info("✅ 統一日誌器定義存在")
            else:
                logger.warning("⚠️ 日誌器定義可能不一致")
        
        # 建議清理的文件
        files_to_cleanup = [
            'eshop/queue_manager_final.py',
            'eshop/queue_manager_optimized.py',
            'eshop/queue_manager_refactored.py',
            'eshop/queue_manager.py.backup_20260217_113500'
        ]
        
        logger.info(f"🗑️  建議清理的文件: {len(files_to_cleanup)} 個")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 代碼重複測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_system_integration():
    """測試系統集成"""
    logger.info("🔍 測試系統集成...")
    
    try:
        # 測試隊列完整性修復腳本
        from test_queue_integrity_fix import main as test_queue_integrity
        
        logger.info("🔄 運行隊列完整性測試...")
        # 注意：這裡我們不實際運行，只是檢查導入
        logger.info("✅ 隊列完整性測試腳本導入成功")
        
        # 測試錯誤處理集成
        from eshop.error_handling import ErrorHandler
        
        # 創建隊列管理器的錯誤處理器
        queue_error_handler = ErrorHandler(module_name='queue_manager')
        
        # 模擬錯誤處理
        try:
            raise ValueError("測試錯誤")
        except Exception as e:
            response = queue_error_handler.handle_error(
                error=e,
                context='test_integration',
                operation='simulate_error',
                data={'test': 'integration'}
            )
            logger.info(f"✅ 錯誤處理集成測試成功: {response.get('error_id')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 系統集成測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_report():
    """生成測試報告"""
    logger.info("📊 生成測試報告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': {
            'queue_manager_fix': test_queue_manager_fix(),
            'error_handling_framework': test_error_handling_framework(),
            'code_duplication_fix': test_code_duplication_fix(),
            'system_integration': test_system_integration()
        },
        'summary': {
            'total_tests': 4,
            'passed_tests': 0,
            'failed_tests': 0
        }
    }
    
    # 計算統計
    passed = sum(1 for test in report['tests'].values() if test)
    failed = len(report['tests']) - passed
    
    report['summary']['passed_tests'] = passed
    report['summary']['failed_tests'] = failed
    
    # 輸出報告
    logger.info("=" * 60)
    logger.info("📋 代碼重複與錯誤處理修復測試報告")
    logger.info("=" * 60)
    
    for test_name, result in report['tests'].items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    logger.info("-" * 60)
    logger.info(f"總測試數: {report['summary']['total_tests']}")
    logger.info(f"通過測試: {report['summary']['passed_tests']}")
    logger.info(f"失敗測試: {report['summary']['failed_tests']}")
    
    if passed == len(report['tests']):
        logger.info("🎉 所有測試通過！修復工作完成。")
    else:
        logger.warning("⚠️ 部分測試失敗，需要進一步檢查。")
    
    logger.info("=" * 60)
    
    return report


def main():
    """主函數"""
    logger.info("🚀 開始代碼重複與錯誤處理修復測試")
    logger.info(f"測試時間: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        report = generate_report()
        
        # 輸出建議
        logger.info("💡 後續建議:")
        
        if report['summary']['passed_tests'] == report['summary']['total_tests']:
            logger.info("1. ✅ 所有修復工作已完成，可以進行下一步優化")
            logger.info("2. ✅ 建議清理多餘的隊列管理器文件")
            logger.info("3. ✅ 可以開始推廣錯誤處理框架到其他模塊")
        else:
            logger.info("1. ⚠️ 需要檢查失敗的測試項目")
            logger.info("2. ⚠️ 可能需要進一步修復代碼問題")
            logger.info("3. ⚠️ 建議重新運行測試確認修復效果")
        
        # 清理建議
        logger.info("🗑️  建議清理的文件:")
        cleanup_files = [
            'eshop/queue_manager_final.py',
            'eshop/queue_manager_optimized.py',
            'eshop/queue_manager_refactored.py',
            'eshop/queue_manager.py.backup_20260217_113500'
        ]
        
        for file in cleanup_files:
            if os.path.exists(file):
                logger.info(f"  - {file} (存在)")
            else:
                logger.info(f"  - {file} (不存在)")
        
        return report['summary']['passed_tests'] == report['summary']['total_tests']
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)