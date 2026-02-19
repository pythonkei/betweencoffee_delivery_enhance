#!/usr/bin/env python3
"""
查询优化器模块迁移测试脚本

这个脚本测试以下内容：
1. 新的错误处理框架在查询优化器模块中的应用
2. 查询优化器模块的迁移效果
3. 标准化响应格式
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_error_handling_framework():
    """测试错误处理框架在查询优化器模块中的应用"""
    logger.info("🔍 测试错误处理框架在查询优化器模块中的应用...")
    
    try:
        # 导入迁移后的查询优化器模块
        from eshop.query_optimizer_refactored import (
            QueryOptimizer,
            example_query_function,
            get_queue_summary_cached_compatible,
            get_active_orders_cached_compatible
        )
        
        # 测试1: 错误处理 - 模拟错误
        logger.info("1. 测试错误处理 - 模拟错误")
        try:
            # 模拟一个错误
            raise ValueError("测试错误")
        except Exception as e:
            from eshop.error_handling import handle_error
            error_result = handle_error(
                error=e,
                context='test_error_handling',
                operation='test_error_handling',
                data={'test': 'data'}
            )
            
            if not error_result.get('success'):
                logger.info(f"✅ 错误处理测试通过: {error_result.get('error_id')}")
                logger.info(f"   错误类型: {error_result.get('error_type')}")
                logger.info(f"   错误消息: {error_result.get('message')}")
            else:
                logger.error("❌ 错误处理测试失败: 应该返回错误但返回了成功")
                return False
        
        # 测试2: 成功处理
        logger.info("\n2. 测试成功处理")
        from eshop.error_handling import handle_success
        success_result = handle_success(
            operation='test_success',
            data={'test': 'data'},
            message='测试成功'
        )
        
        if success_result.get('success'):
            logger.info(f"✅ 成功处理测试通过")
            logger.info(f"   消息: {success_result.get('message')}")
        else:
            logger.error(f"❌ 成功处理测试失败")
            return False
        
        # 测试3: 装饰器测试
        logger.info("\n3. 测试装饰器 - 示例查询函数")
        decorator_result = example_query_function([1, 2, 3])
        
        # 装饰器返回的是包装后的结果，包含 success 和 data
        if isinstance(decorator_result, dict):
            # 如果返回的是字典，检查是否包含预期字段
            if 'order_ids' in decorator_result and 'result_count' in decorator_result:
                logger.info("✅ 装饰器测试通过")
                logger.info(f"   订单ID: {decorator_result.get('order_ids', 'N/A')}")
                logger.info(f"   结果数量: {decorator_result.get('result_count', 'N/A')}")
            else:
                # 可能是错误响应格式
                if decorator_result.get('success'):
                    data = decorator_result.get('data', {})
                    if 'order_ids' in data and 'result_count' in data:
                        logger.info("✅ 装饰器测试通过（包装格式）")
                        logger.info(f"   订单ID: {data.get('order_ids', 'N/A')}")
                        logger.info(f"   结果数量: {data.get('result_count', 'N/A')}")
                    else:
                        logger.error("❌ 装饰器测试失败: 返回格式不正确")
                        return False
                else:
                    logger.error(f"❌ 装饰器测试失败: {decorator_result.get('error_id', 'N/A')}")
                    return False
        else:
            logger.error("❌ 装饰器测试失败: 返回类型不是字典")
            return False
        
        # 测试4: 兼容性包装器
        logger.info("\n4. 测试兼容性包装器")
        
        # 测试队列摘要兼容性包装器
        queue_summary = get_queue_summary_cached_compatible()
        if isinstance(queue_summary, dict):
            logger.info("✅ 队列摘要兼容性包装器测试通过")
            logger.info(f"   返回类型: {type(queue_summary).__name__}")
        else:
            logger.error("❌ 队列摘要兼容性包装器测试失败")
            return False
        
        # 测试活动订单兼容性包装器
        active_orders = get_active_orders_cached_compatible()
        if isinstance(active_orders, list):
            logger.info("✅ 活动订单兼容性包装器测试通过")
            logger.info(f"   返回类型: {type(active_orders).__name__}")
        else:
            logger.error("❌ 活动订单兼容性包装器测试失败")
            return False
        
        # 测试5: QueryOptimizer 类方法
        logger.info("\n5. 测试 QueryOptimizer 类方法")
        
        # 测试缓存统计
        cache_stats_result = QueryOptimizer.get_cache_stats()
        if cache_stats_result.get('success'):
            logger.info("✅ 缓存统计测试通过")
            data = cache_stats_result.get('data', {})
            logger.info(f"   总缓存键: {data.get('total_keys', 0)}")
            logger.info(f"   查询缓存键: {data.get('query_keys', 0)}")
        else:
            logger.error("❌ 缓存统计测试失败")
            return False
        
        # 测试缓存失效
        invalidate_result = QueryOptimizer.invalidate_cache('test_prefix')
        if invalidate_result.get('success'):
            logger.info("✅ 缓存失效测试通过")
            data = invalidate_result.get('data', {})
            logger.info(f"   删除的键数量: {data.get('count', 0)}")
        else:
            logger.error("❌ 缓存失效测试失败")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误处理框架测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_response_format_consistency():
    """测试响应格式一致性"""
    logger.info("🔍 测试响应格式一致性...")
    
    try:
        from eshop.query_optimizer_refactored import QueryOptimizer
        
        # 测试成功响应格式
        result = QueryOptimizer.get_cache_stats()
        
        required_keys = ['success', 'message', 'details', 'timestamp']
        if result.get('success'):
            required_keys.append('data')
        
        missing_keys = []
        for key in required_keys:
            if key not in result:
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"❌ 响应格式不一致，缺少键: {missing_keys}")
            logger.error(f"   实际响应键: {list(result.keys())}")
            return False
        
        logger.info("✅ 响应格式一致性测试通过")
        logger.info(f"   响应包含所有必要键: {required_keys}")
        
        # 检查错误响应格式（如果有错误ID）
        if 'error_id' in result:
            error_keys = ['error_id', 'error_type']
            for key in error_keys:
                if key not in result:
                    logger.error(f"❌ 错误响应缺少键: {key}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 响应格式测试失败: {str(e)}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    logger.info("🔍 测试向后兼容性...")
    
    try:
        # 检查原始模块和新模块的函数签名
        import inspect
        
        # 原始模块
        from eshop import query_optimizer as original_module
        # 新模块
        from eshop import query_optimizer_refactored as new_module
        
        # 检查关键函数是否存在
        key_functions = [
            'get_queue_summary_cached',
            'get_active_orders_cached',
            'get_quick_order_times_cached',
            'invalidate_cache',
            'prefetch_order_relations',
            'bulk_update_order_status'
        ]
        
        missing_functions = []
        for func_name in key_functions:
            if not hasattr(new_module.QueryOptimizer, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            logger.error(f"❌ 新模块缺少函数: {missing_functions}")
            return False
        
        logger.info("✅ 向后兼容性测试通过")
        logger.info(f"   所有 {len(key_functions)} 个关键函数都存在")
        
        # 检查兼容性包装器
        compatibility_wrappers = [
            'get_queue_summary_cached_compatible',
            'get_active_orders_cached_compatible'
        ]
        
        for wrapper_name in compatibility_wrappers:
            if not hasattr(new_module, wrapper_name):
                logger.error(f"❌ 缺少兼容性包装器: {wrapper_name}")
                return False
        
        logger.info(f"   所有 {len(compatibility_wrappers)} 个兼容性包装器都存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 向后兼容性测试失败: {str(e)}")
        return False


def generate_migration_report():
    """生成迁移报告"""
    logger.info("📊 生成迁移报告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': {
            'error_handling_framework': test_error_handling_framework(),
            'response_format_consistency': test_response_format_consistency(),
            'backward_compatibility': test_backward_compatibility()
        },
        'summary': {
            'total_tests': 3,
            'passed_tests': 0,
            'failed_tests': 0
        }
    }
    
    # 计算统计
    passed = sum(1 for test in report['tests'].values() if test)
    failed = len(report['tests']) - passed
    
    report['summary']['passed_tests'] = passed
    report['summary']['failed_tests'] = failed
    
    # 输出报告
    logger.info("=" * 60)
    logger.info("📋 查询优化器模块迁移测试报告")
    logger.info("=" * 60)
    
    for test_name, result in report['tests'].items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info("-" * 60)
    logger.info(f"总测试数: {report['summary']['total_tests']}")
    logger.info(f"通过测试: {report['summary']['passed_tests']}")
    logger.info(f"失败测试: {report['summary']['failed_tests']}")
    
    if passed == len(report['tests']):
        logger.info("🎉 所有测试通过！查询优化器模块迁移成功。")
    else:
        logger.warning("⚠️ 部分测试失败，需要进一步检查。")
    
    logger.info("=" * 60)
    
    return report


def main():
    """主函数"""
    logger.info("🚀 开始查询优化器模块迁移测试")
    logger.info(f"测试时间: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        report = generate_migration_report()
        
        # 输出建议
        logger.info("💡 迁移建议:")
        
        if report['summary']['passed_tests'] == report['summary']['total_tests']:
            logger.info("1. ✅ 查询优化器模块迁移成功，可以进入下一阶段")
            logger.info("2. ✅ 建议逐步替换原始模块的导入")
            logger.info("3. ✅ 可以开始迁移其他数据访问模块")
        else:
            logger.info("1. ⚠️ 需要检查失败的测试项目")
            logger.info("2. ⚠️ 可能需要修复迁移问题")
            logger.info("3. ⚠️ 建议重新测试确认迁移效果")
        
        # 迁移步骤
        logger.info("\n📋 迁移步骤:")
        logger.info("1. 备份原始 query_optimizer.py")
        logger.info("2. 将 query_optimizer_refactored.py 重命名为 query_optimizer.py")
        logger.info("3. 更新所有导入 query_optimizer 的模块")
        logger.info("4. 在 Django 环境中运行完整测试")
        logger.info("5. 监控生产环境错误日志")
        
        return report['summary']['passed_tests'] == report['summary']['total_tests']
        
    except Exception as e:
        logger.error(f"❌ 测试过程发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)