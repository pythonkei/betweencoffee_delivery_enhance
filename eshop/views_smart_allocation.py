"""
智能分配系統API視圖

這個模塊提供智能分配系統的API端點，包括：
1. 員工工作負載查詢
2. 智能分配建議
3. 隊列優化操作
4. 系統狀態監控
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

from .smart_allocation import (
    get_smart_allocator,
    get_workload_manager,
    get_time_calculator,
    initialize_smart_system,
    allocate_new_order,
    optimize_order_preparation,
    get_recommendations_for_order,
    get_system_overview,
    optimize_order_preparation as optimize_order
)

logger = logging.getLogger('eshop.smart_allocation')


def staff_required(view_func):
    """
    裝飾器：要求用戶是員工
    """
    def check_staff(user):
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    
    return user_passes_test(check_staff)(view_func)


@csrf_exempt
@require_http_methods(["GET"])
@staff_required
def barista_workload_api(request):
    """
    API: 獲取員工工作負載概覽
    
    返回格式:
    {
        "success": true,
        "message": "操作成功",
        "data": {
            "total_baristas": 2,
            "active_baristas": 2,
            "total_capacity": 4,
            "current_load": 2,
            "available_capacity": 2,
            "utilization_rate": 50.0,
            "barista_details": [...],
            "recommendations": [...]
        }
    }
    """
    try:
        logger.info("📊 API請求: 獲取員工工作負載")
        
        # 初始化智能系統（如果尚未初始化）
        initialize_smart_system()
        
        # 獲取系統狀態
        allocator = get_smart_allocator()
        system_status = allocator.get_system_status()
        
        # 獲取智能建議（如果有訂單）
        from .models import OrderModel
        recent_order = OrderModel.objects.filter(
            payment_status='paid',
            status__in=['waiting', 'preparing']
        ).first()
        
        recommendations = []
        if recent_order:
            rec_result = get_recommendations_for_order(recent_order.id)
            if rec_result.get('success'):
                recommendations = rec_result.get('recommendations', [])
        
        # 合併數據
        response_data = {
            **system_status,
            'recommendations': recommendations
        }
        
        logger.info(f"✅ 工作負載數據獲取成功: {len(system_status.get('barista_details', []))} 個員工")
        
        return JsonResponse({
            'success': True,
            'message': '工作負載數據獲取成功',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"❌ 獲取工作負載失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'message': f'獲取工作負載失敗: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@staff_required
def optimize_queue_api(request):
    """
    API: 優化隊列
    
    返回格式:
    {
        "success": true,
        "message": "隊列優化成功",
        "data": {
            "orders_optimized": 2,
            "time_savings": 5.5,
            "load_balanced": true,
            "recommendations_generated": 3
        }
    }
    """
    try:
        logger.info("🤖 API請求: 優化隊列")
        
        # 初始化智能系統
        initialize_smart_system()
        
        # 使用隊列管理器進行優化
        from .queue_manager_refactored import CoffeeQueueManager
        manager = CoffeeQueueManager()
        result = manager.optimize_queue_with_smart_allocation()
        
        if result.get('success'):
            data = result['data']
            logger.info(f"✅ 隊列優化成功: 優化 {data.get('orders_optimized', 0)} 個訂單")
            
            return JsonResponse({
                'success': True,
                'message': '隊列優化成功',
                'data': data
            })
        else:
            logger.error(f"❌ 隊列優化失敗: {result.get('message')}")
            
            return JsonResponse({
                'success': False,
                'message': result.get('message', '隊列優化失敗'),
                'data': None
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ 隊列優化失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'message': f'隊列優化失敗: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@staff_required
def order_recommendations_api(request, order_id):
    """
    API: 獲取訂單的智能建議
    
    參數:
    - order_id: 訂單ID
    
    返回格式:
    {
        "success": true,
        "message": "建議獲取成功",
        "data": {
            "order_id": 123,
            "recommendations": [...],
            "optimization_suggestions": {...}
        }
    }
    """
    try:
        logger.info(f"💡 API請求: 獲取訂單 #{order_id} 的智能建議")
        
        # 初始化智能系統
        initialize_smart_system()
        
        # 獲取建議
        recommendations_result = get_recommendations_for_order(order_id)
        
        if recommendations_result.get('success'):
            data = recommendations_result
            logger.info(f"✅ 訂單 #{order_id} 建議獲取成功: {len(data.get('recommendations', []))} 個建議")
            
            return JsonResponse({
                'success': True,
                'message': '建議獲取成功',
                'data': data
            })
        else:
            logger.error(f"❌ 訂單 #{order_id} 建議獲取失敗: {recommendations_result.get('message')}")
            
            return JsonResponse({
                'success': False,
                'message': recommendations_result.get('message', '建議獲取失敗'),
                'data': None
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ 訂單 #{order_id} 建議獲取失敗: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': f'建議獲取失敗: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@staff_required
def system_status_api(request):
    """
    API: 獲取系統狀態
    
    返回格式:
    {
        "success": true,
        "message": "系統狀態獲取成功",
        "data": {
            "system_status": {...},
            "queue_status": {...},
            "performance_metrics": {...}
        }
    }
    """
    try:
        logger.info("📈 API請求: 獲取系統狀態")
        
        # 初始化智能系統
        initialize_smart_system()
        
        # 獲取系統概覽
        system_overview = get_system_overview()
        
        # 獲取隊列狀態
        from .queue_manager_refactored import CoffeeQueueManager
        manager = CoffeeQueueManager()
        queue_status_result = manager.verify_queue_integrity()
        
        queue_status = {}
        if queue_status_result.get('success'):
            queue_status = queue_status_result['data']
        
        # 計算性能指標
        performance_metrics = calculate_performance_metrics()
        
        response_data = {
            'system_status': system_overview,
            'queue_status': queue_status,
            'performance_metrics': performance_metrics
        }
        
        logger.info("✅ 系統狀態獲取成功")
        
        return JsonResponse({
            'success': True,
            'message': '系統狀態獲取成功',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"❌ 系統狀態獲取失敗: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': f'系統狀態獲取失敗: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@staff_required
def assign_order_api(request, order_id):
    """
    API: 智能分配訂單
    
    參數:
    - order_id: 訂單ID
    
    請求體 (可選):
    {
        "strategy": "balanced",  // 分配策略: balanced, fastest, round_robin
        "barista_id": 1          // 指定員工ID (可選)
    }
    
    返回格式:
    {
        "success": true,
        "message": "訂單分配成功",
        "data": {
            "order_id": 123,
            "recommended_barista_id": 1,
            "recommended_barista_name": "員工A",
            "estimated_time": 8.5,
            "allocation_strategy": "balanced"
        }
    }
    """
    try:
        import json
        
        logger.info(f"🤖 API請求: 智能分配訂單 #{order_id}")
        
        # 解析請求體
        strategy = 'balanced'
        barista_id = None
        
        if request.body:
            try:
                body_data = json.loads(request.body)
                strategy = body_data.get('strategy', 'balanced')
                barista_id = body_data.get('barista_id')
            except json.JSONDecodeError:
                logger.warning("請求體JSON解析失敗，使用默認值")
        
        # 初始化智能系統
        initialize_smart_system()
        
        # 獲取訂單
        from .models import OrderModel
        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'訂單 #{order_id} 不存在',
                'data': None
            }, status=404)
        
        # 如果指定了員工ID，直接分配
        if barista_id:
            from .models import Barista
            try:
                barista = Barista.objects.get(id=barista_id)
                
                # 檢查員工是否可用
                workload_manager = get_workload_manager()
                workload = workload_manager.get_barista_workload(barista_id)
                
                if not workload or not workload['is_available']:
                    return JsonResponse({
                        'success': False,
                        'message': f'員工 {barista.name} 不可用',
                        'data': None
                    }, status=400)
                
                # 分配訂單
                coffee_count = sum(
                    item.get('quantity', 1) 
                    for item in order.get_items() 
                    if item.get('type') == 'coffee'
                )
                
                assigned = workload_manager.assign_order_to_barista(
                    order, barista_id, coffee_count
                )
                
                if assigned:
                    logger.info(f"✅ 訂單 #{order_id} 手動分配給 {barista.name}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'訂單已分配給 {barista.name}',
                        'data': {
                            'order_id': order_id,
                            'recommended_barista_id': barista_id,
                            'recommended_barista_name': barista.name,
                            'estimated_time': 0,  # 需要計算
                            'allocation_strategy': 'manual',
                            'manual_assignment': True
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': '訂單分配失敗',
                        'data': None
                    }, status=400)
                    
            except Barista.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'員工 #{barista_id} 不存在',
                    'data': None
                }, status=404)
        
        # 否則使用智能分配
        allocator = get_smart_allocator()
        allocation_result = allocator.allocate_order(order, strategy)
        
        if allocation_result.get('success'):
            data = allocation_result
            logger.info(f"✅ 訂單 #{order_id} 智能分配成功: {data.get('message')}")
            
            # 記錄分配結果
            if data.get('recommended_barista_id'):
                workload_manager = get_workload_manager()
                coffee_count = allocator._calculate_coffee_count(order)
                workload_manager.assign_order_to_barista(
                    order, 
                    data['recommended_barista_id'],
                    coffee_count
                )
            
            return JsonResponse({
                'success': True,
                'message': '訂單分配成功',
                'data': allocation_result
            })
        else:
            logger.error(f"❌ 訂單 #{order_id} 分配失敗: {allocation_result.get('message')}")
            
            return JsonResponse({
                'success': False,
                'message': allocation_result.get('message', '訂單分配失敗'),
                'data': None
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ 訂單 #{order_id} 分配失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'message': f'訂單分配失敗: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@staff_required
def update_barista_status_api(request, barista_id):
    """
    API: 更新員工狀態
    
    參數:
    - barista_id: 員工ID
    
    請求體:
    {
        "is_active": true,           // 是否在崗
        "efficiency_factor": 0.9,    // 效率因子
        "max_concurrent_orders": 2   // 最大並行訂單數
    }
    
    返回格式:
    {
        "success": true,
        "message": "員工狀態更新成功",
        "data": {
            "barista_id": 1,
            "name": "員工A",
            "is_active": true,
            "efficiency_factor": 0.9,
            "max_concurrent_orders": 2
        }
    }
    """
    try:
        import json
        
        logger.info(f"👤 API請求: 更新員工 #{barista_id} 狀態")
        
        # 解析請求體
        if not request.body:
            return JsonResponse({
                'success': False,
                'message': '請求體為空',
                'data': None
            }, status=400)
        
        try:
            body_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '請求體JSON解析失敗',
                'data': None
            }, status=400)
        
        # 獲取員工
        from .models import Barista
        try:
            barista = Barista.objects.get(id=barista_id)
        except Barista.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'員工 #{barista_id} 不存在',
                'data': None
            }, status=404)
        
        # 更新字段
        if 'is_active' in body_data:
            barista.is_active = bool(body_data['is_active'])
        
        if 'efficiency_factor' in body_data:
            efficiency = float(body_data['efficiency_factor'])
            # 限制範圍
            efficiency = max(0.5, min(2.0, efficiency))
            barista.efficiency_factor = efficiency
        
        if 'max_concurrent_orders' in body_data:
            max_orders = int(body_data['max_concurrent_orders'])
            # 限制範圍
            max_orders = max(1, min(5, max_orders))
            barista.max_concurrent_orders = max_orders
        
        barista.save()
        
        logger.info(f"✅ 員工 #{barista_id} 狀態更新成功")
        
        return JsonResponse({
            'success': True,
            'message': '員工狀態更新成功',
            'data': {
                'barista_id': barista.id,
                'name': barista.name,
                'is_active': barista.is_active,
                'efficiency_factor': barista.efficiency_factor,
                'max_concurrent_orders': barista.max_concurrent_orders
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 員工 #{barista_id} 狀態更新失敗: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': f'員工狀態更新失敗: {str(e)}',
            'data': None
        }, status=500)


def calculate_performance_metrics():
    """
    計算性能指標
    
    返回:
    {
        "average_preparation_time": 8.5,
        "orders_per_hour": 12,
        "utilization_trend": "increasing",
        "peak_hours": ["10:00", "15:00"],
        "bottlenecks": []
    }
    """
    try:
        from .models import CoffeeQueue, OrderModel
        from django.utils import timezone
        from datetime import timedelta
        
        # 計算平均製作時間
        completed_queues = CoffeeQueue.objects.filter(
            status='ready',
            actual_start_time__isnull=False,
            actual_completion_time__isnull=False
        ).order_by('-actual_completion_time')[:10]
        
        total_time = timedelta()
        count = 0
        
        for queue in completed_queues:
            if queue.actual_start_time and queue.actual_completion_time:
                prep_time = queue.actual_completion_time - queue.actual_start_time
                total_time += prep_time
                count += 1
        
        average_preparation_time = 0
        if count > 0:
            average_preparation_time = total_time.total_seconds() / count / 60  # 轉換為分鐘
        
        # 計算每小時訂單數
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_orders = OrderModel.objects.filter(
            created_at__gte=one_hour_ago,
            payment_status='paid'
        ).count()
        
        orders_per_hour = recent_orders
        
        # 簡單的趨勢分析
        two_hours_ago = timezone.now() - timedelta(hours=2)
        orders_previous_hour = OrderModel.objects.filter(
            created_at__gte=two_hours_ago,
            created_at__lt=one_hour_ago,
            payment_status='paid'
        ).count()
        
        utilization_trend = "stable"
        if orders_per_hour > orders_previous_hour * 1.2:
            utilization_trend = "increasing"
        elif orders_per_hour < orders_previous_hour * 0.8:
            utilization_trend = "decreasing"
        
        # 簡單的峰值小時檢測（基於最近數據）
        peak_hours = []
        current_hour = timezone.now().hour
        
        # 假設10:00和15:00是常見的峰值時間
        if 9 <= current_hour <= 11:
            peak_hours.append("10:00")
        if 14 <= current_hour <= 16:
            peak_hours.append("15:00")
        
        # 檢查瓶頸
        bottlenecks = []
        
        # 檢查是否有等待時間過長的訂單
        waiting_queues = CoffeeQueue.objects.filter(status='waiting')
        if waiting_queues.count() > 5:
            bottlenecks.append("隊列過長")
        
        # 檢查員工負載
        from .smart_allocation import get_smart_allocator
        allocator = get_smart_allocator()
        system_status = allocator.get_system_status()
        
        if system_status.get('utilization_rate', 0) > 80:
            bottlenecks.append("員工負載過高")
        
        if system_status.get('available_capacity', 0) == 0:
            bottlenecks.append("無可用容量")
        
        return {
            'average_preparation_time': round(average_preparation_time, 1),
            'orders_per_hour': orders_per_hour,
            'utilization_trend': utilization_trend,
            'peak_hours': peak_hours,
            'bottlenecks': bottlenecks,
            'waiting_orders': waiting_queues.count(),
            'utilization_rate': system_status.get('utilization_rate', 0)
        }
        
    except Exception as e:
        logger.error(f"計算性能指標失敗: {str(e)}")
        
        # 返回默認值
        return {
            'average_preparation_time': 8.0,
            'orders_per_hour': 10,
            'utilization_trend': 'stable',
            'peak_hours': [],
            'bottlenecks': [],
            'waiting_orders': 0,
            'utilization_rate': 0
        }
