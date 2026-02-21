#!/usr/bin/env python
"""
隊列管理器遷移監控儀表板
用於監控生產環境中的錯誤處理和系統狀態
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

try:
    import django
    django.setup()
    DJANGO_SETUP = True
except Exception as e:
    DJANGO_SETUP = False
    print(f"⚠️ Django 環境設置失敗: {str(e)}")
    print("將使用簡化模式運行監控")

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueueMigrationMonitor:
    """隊列管理器遷移監控器"""
    
    def __init__(self):
        self.monitoring_data = {
            'last_check': None,
            'errors': [],
            'warnings': [],
            'successes': [],
            'stats': {},
            'system_status': 'unknown'
        }
        
    def check_imports(self):
        """檢查導入是否正常"""
        try:
            from eshop.queue_manager_refactored import CoffeeQueueManager
            logger.info("✅ queue_manager_refactored 導入成功")
            self.monitoring_data['successes'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'import_check',
                'message': 'queue_manager_refactored 導入成功'
            })
            return True
        except ImportError as e:
            error_msg = f"❌ queue_manager_refactored 導入失敗: {str(e)}"
            logger.error(error_msg)
            self.monitoring_data['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'import_check',
                'error': str(e),
                'message': error_msg
            })
            return False
    
    def check_original_queue_manager(self):
        """檢查原始 queue_manager.py 是否已刪除"""
        original_path = Path(__file__).parent / 'eshop' / 'queue_manager.py'
        backup_path = Path(__file__).parent / 'archive' / 'queue_manager_backup' / 'queue_manager_original_backup.py'
        
        if original_path.exists():
            warning_msg = f"⚠️ 原始 queue_manager.py 仍然存在: {original_path}"
            logger.warning(warning_msg)
            self.monitoring_data['warnings'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'original_file_check',
                'message': warning_msg
            })
            return False
        else:
            logger.info("✅ 原始 queue_manager.py 已成功刪除")
            self.monitoring_data['successes'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'original_file_check',
                'message': '原始 queue_manager.py 已成功刪除'
            })
            
            # 檢查備份是否存在
            if backup_path.exists():
                logger.info(f"✅ 備份文件存在: {backup_path}")
            else:
                warning_msg = f"⚠️ 備份文件不存在: {backup_path}"
                logger.warning(warning_msg)
                self.monitoring_data['warnings'].append({
                    'timestamp': datetime.now().isoformat(),
                    'check': 'backup_check',
                    'message': warning_msg
                })
            
            return True
    
    def check_error_handling_framework(self):
        """檢查錯誤處理框架"""
        try:
            from eshop.error_handling import ErrorHandler
            handler = ErrorHandler(module_name='monitoring')
            
            # 測試成功處理
            result = handler.handle_success(
                operation='test_operation',
                message='錯誤處理框架測試成功',
                data={'test': 'data'}
            )
            
            if result.get('success'):
                logger.info("✅ 錯誤處理框架正常工作")
                self.monitoring_data['successes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'check': 'error_handling_check',
                    'message': '錯誤處理框架正常工作'
                })
                return True
            else:
                error_msg = "❌ 錯誤處理框架返回失敗"
                logger.error(error_msg)
                self.monitoring_data['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'check': 'error_handling_check',
                    'message': error_msg,
                    'data': result
                })
                return False
                
        except Exception as e:
            error_msg = f"❌ 錯誤處理框架檢查失敗: {str(e)}"
            logger.error(error_msg)
            self.monitoring_data['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'error_handling_check',
                'error': str(e),
                'message': error_msg
            })
            return False
    
    def check_queue_operations(self):
        """檢查隊列操作"""
        try:
            from eshop.queue_manager_refactored import CoffeeQueueManager
            from eshop.models import OrderModel, CoffeeQueue
            
            manager = CoffeeQueueManager()
            
            # 使用 verify_queue_integrity 來獲取隊列統計
            integrity_result = manager.verify_queue_integrity()
            
            if integrity_result.get('success'):
                stats = integrity_result.get('data', {})
                logger.info(f"✅ 隊列統計獲取成功: {stats}")
                
                self.monitoring_data['stats'] = {
                    'waiting_count': stats.get('waiting_count', 0),
                    'preparing_count': stats.get('preparing_count', 0),
                    'ready_count': stats.get('ready_count', 0),
                    'total_count': stats.get('total_count', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.monitoring_data['successes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'check': 'queue_operations_check',
                    'message': '隊列統計獲取成功',
                    'data': stats
                })
                return True
            else:
                error_msg = f"❌ 隊列統計獲取失敗: {integrity_result.get('message', '未知錯誤')}"
                logger.error(error_msg)
                self.monitoring_data['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'check': 'queue_operations_check',
                    'message': error_msg,
                    'data': integrity_result
                })
                return False
                
        except Exception as e:
            error_msg = f"❌ 隊列操作檢查失敗: {str(e)}"
            logger.error(error_msg)
            self.monitoring_data['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'check': 'queue_operations_check',
                'error': str(e),
                'message': error_msg
            })
            return False
    
    def check_system_integrity(self):
        """檢查系統完整性"""
        checks = [
            self.check_imports,
            self.check_original_queue_manager,
            self.check_error_handling_framework,
            self.check_queue_operations
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                logger.error(f"檢查失敗: {check.__name__}: {str(e)}")
                results.append(False)
        
        # 計算系統狀態
        total_checks = len(results)
        passed_checks = sum(results)
        
        if total_checks == passed_checks:
            self.monitoring_data['system_status'] = 'healthy'
            logger.info(f"✅ 系統完整性檢查通過: {passed_checks}/{total_checks}")
        elif passed_checks >= total_checks * 0.7:
            self.monitoring_data['system_status'] = 'degraded'
            logger.warning(f"⚠️ 系統完整性檢查部分通過: {passed_checks}/{total_checks}")
        else:
            self.monitoring_data['system_status'] = 'unhealthy'
            logger.error(f"❌ 系統完整性檢查失敗: {passed_checks}/{total_checks}")
        
        self.monitoring_data['last_check'] = datetime.now().isoformat()
        
        return all(results)
    
    def generate_report(self):
        """生成監控報告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_status': self.monitoring_data['system_status'],
            'summary': {
                'total_errors': len(self.monitoring_data['errors']),
                'total_warnings': len(self.monitoring_data['warnings']),
                'total_successes': len(self.monitoring_data['successes'])
            },
            'errors': self.monitoring_data['errors'],
            'warnings': self.monitoring_data['warnings'],
            'successes': self.monitoring_data['successes'],
            'stats': self.monitoring_data['stats'],
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self):
        """生成建議"""
        recommendations = []
        
        if self.monitoring_data['system_status'] == 'unhealthy':
            recommendations.append({
                'priority': 'high',
                'action': '立即檢查系統錯誤',
                'details': '系統完整性檢查失敗，需要立即修復'
            })
        
        if len(self.monitoring_data['errors']) > 0:
            recommendations.append({
                'priority': 'high',
                'action': '修復檢測到的錯誤',
                'details': f'發現 {len(self.monitoring_data["errors"])} 個錯誤需要處理'
            })
        
        if len(self.monitoring_data['warnings']) > 0:
            recommendations.append({
                'priority': 'medium',
                'action': '處理警告信息',
                'details': f'發現 {len(self.monitoring_data["warnings"])} 個警告需要關注'
            })
        
        if self.monitoring_data['system_status'] == 'healthy':
            recommendations.append({
                'priority': 'low',
                'action': '繼續監控系統狀態',
                'details': '系統運行正常，建議定期監控'
            })
        
        return recommendations
    
    def save_report(self, report):
        """保存報告到文件"""
        report_file = Path(__file__).parent / 'queue_monitoring_dashboard.json'
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 監控報告已保存到: {report_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存監控報告失敗: {str(e)}")
            return False
    
    def run_monitoring(self):
        """運行完整監控流程"""
        logger.info("=" * 60)
        logger.info("開始隊列管理器遷移監控檢查")
        logger.info("=" * 60)
        
        # 運行檢查
        integrity_check = self.check_system_integrity()
        
        # 生成報告
        report = self.generate_report()
        
        # 保存報告
        self.save_report(report)
        
        # 輸出摘要
        logger.info("=" * 60)
        logger.info("監控檢查完成")
        logger.info(f"系統狀態: {report['system_status']}")
        logger.info(f"錯誤數: {report['summary']['total_errors']}")
        logger.info(f"警告數: {report['summary']['total_warnings']}")
        logger.info(f"成功數: {report['summary']['total_successes']}")
        
        if report['stats']:
            logger.info(f"隊列統計: 等待中={report['stats'].get('waiting_count', 0)}, "
                       f"製作中={report['stats'].get('preparing_count', 0)}, "
                       f"已就緒={report['stats'].get('ready_count', 0)}")
        
        logger.info("=" * 60)
        
        return integrity_check, report


def main():
    """主函數"""
    try:
        # 初始化監控器
        monitor = QueueMigrationMonitor()
        
        # 運行監控
        integrity_check, report = monitor.run_monitoring()
        
        # 輸出報告文件位置
        report_file = Path(__file__).parent / 'queue_monitoring_dashboard.json'
        print(f"\n📊 詳細報告已保存到: {report_file}")
        
        # 根據檢查結果返回退出碼
        if integrity_check:
            print("✅ 監控檢查通過")
            return 0
        else:
            print("❌ 監控檢查發現問題，請查看報告")
            return 1
            
    except Exception as e:
        logger.error(f"監控程序運行失敗: {str(e)}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)