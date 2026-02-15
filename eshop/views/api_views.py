# eshop/views/api_views.py

import json
import logging
from datetime import timedelta

from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from eshop.models import OrderModel, CoffeeQueue
from eshop.queue_manager import CoffeeQueueManager

from eshop.time_service import time_service   # ✅ 唯一時間服務
from eshop.order_status_manager import OrderStatusManager

# 導入新的序列化和工具
from eshop.serializers import OrderDataSerializer, ApiResponseFormatter
from eshop.api_utils import BaseApiView, OrderApiMixin, staff_api_required

logger = logging.getLogger(__name__)


# ==================== 統一的訂單API ====================

class UnifiedOrderAPI(BaseApiView, OrderApiMixin):
    """統一的訂單API - 替換所有分散的訂單API"""
    
    order_model = OrderModel
    decorators = [login_required]
    
    def get(self, request, order_id=None):
        """獲取訂單信息"""
        try:
            if order_id:
                # 獲取單個訂單
                order = self.get_order(order_id)
                include_queue_info = (request.GET.get('include_queue', 'true')
                                      .lower() == 'true')
                include_items = (request.GET.get('include_items', 'true')
                                 .lower() == 'true')
                
                order_data = self.serialize_order(
                    order, 
                    include_queue_info=include_queue_info,
                    include_items=include_items
                )
                
                return self.success_response(data=order_data)
            else:
                # 獲取訂單列表
                status_filter = request.GET.get('status', '')
                time_range = request.GET.get('time_range', 'today')
                page = int(request.GET.get('page', 1))
                page_size = int(request.GET.get('page_size', 20))
                
                # 構建查詢
                query = self.order_model.objects.all()
                
                # 權限過濾：員工查看所有，用戶只看自己的
                if not request.user.is_staff:
                    query = query.filter(user=request.user)
                
                # 狀態過濾
                if status_filter:
                    if status_filter == 'active':
                        query = query.filter(status__in=['preparing', 'ready'])
                    elif status_filter == 'pending_payment':
                        query = query.filter(payment_status="pending", 
                                             status='pending')
                    else:
                        query = query.filter(status=status_filter)
                
                # 時間範圍過濾
                if time_range == 'today':
                    today_start = timezone.now().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    query = query.filter(created_at__gte=today_start)
                elif time_range == 'week':
                    week_start = timezone.now() - timedelta(days=7)
                    query = query.filter(created_at__gte=week_start)
                elif time_range == 'month':
                    month_start = timezone.now() - timedelta(days=30)
                    query = query.filter(created_at__gte=month_start)
                
                # 分頁
                total = query.count()
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                orders = query.order_by('-created_at')[start_idx:end_idx]
                
                # 序列化
                orders_data = [
                    self.serialize_order(
                        order, include_queue_info=False, include_items=False
                    )
                    for order in orders
                ]
                
                return self.success_response(
                    data=orders_data,
                    total=total,
                    page=page,
                    page_size=page_size
                )
                
        except Exception as e:
            logger.error(f"獲取訂單失敗: {str(e)}")
            return self.error_response(f"獲取訂單失敗: {str(e)}", status=500)


class UnifiedQueueAPI(BaseApiView):
    """統一的隊列API"""
    
    decorators = [staff_api_required]
    
    def get(self, request):
        """獲取隊列信息"""
        try:
            status_filter = request.GET.get('status', '')
            queue_type = request.GET.get('type', 'waiting')  # waiting, preparing, ready
            
            # 構建查詢
            query = CoffeeQueue.objects.all().select_related('order')
            
            if status_filter:
                query = query.filter(status=status_filter)
            else:
                # 默認根據類型過濾
                if queue_type == 'waiting':
                    query = query.filter(status='waiting').order_by('position')
                elif queue_type == 'preparing':
                    query = query.filter(status='preparing').order_by('position')
                elif queue_type == 'ready':
                    query = query.filter(status='ready').order_by('position')
                elif queue_type == 'all':
                    query = query.order_by('position')
            
            queue_items = list(query)
            
            # 序列化隊列數據
            queue_data = OrderDataSerializer.serialize_queue_list(
                queue_items,
                include_order_info=True
            )
            
            # 統計信息
            stats = {
                'waiting_count': CoffeeQueue.objects.filter(status='waiting').count(),
                'preparing_count': CoffeeQueue.objects.filter(status='preparing').count(),
                'ready_count': CoffeeQueue.objects.filter(status='ready').count(),
                'total_count': CoffeeQueue.objects.count(),
            }
            
            return self.success_response(
                data={
                    'queue_items': queue_data,
                    'stats': stats,
                    'queue_type': queue_type,
                }
            )
            
        except Exception as e:
            logger.error(f"獲取隊列信息失敗: {str(e)}")
            return self.error_response(f"獲取隊列信息失敗: {str(e)}", status=500)
    
    def post(self, request, action=None, order_id=None):
        """隊列操作"""
        try:
            if not action and order_id:
                # 開始製作訂單
                return self.start_preparation(order_id, request.user.username)
            elif action == 'ready' and order_id:
                # 標記為就緒 - 改為使用 OrderStatusManager
                return self.mark_as_ready_using_manager(order_id, request.user.username)
            elif action == 'complete' and order_id:
                # 標記為完成 - 改為使用 OrderStatusManager
                return self.mark_as_complete_using_manager(order_id, request.user.username)
            elif action == 'reorder':
                # 重新排序隊列
                return self.reorder_queue(request)
            else:
                return self.error_response("無效的操作", status=400)
                
        except Exception as e:
            logger.error(f"隊列操作失敗: {str(e)}")
            return self.error_response(f"隊列操作失敗: {str(e)}", status=500)
    


    def start_preparation(self, order_id, barista_name):
        """開始製作訂單（統一使用 OrderStatusManager）"""
        try:
            from eshop.order_status_manager import OrderStatusManager
            
            # 使用 OrderStatusManager 處理狀態變更
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=order_id,
                barista_name=barista_name
            )
            
            if not result['success']:
                return self.error_response(result['message'], status=400)
            
            logger.info(f"訂單 {order_id} 已開始製作，咖啡師: {barista_name}")
            
            return self.success_response(
                data=self.serialize_order_with_queue(result['order']),
                message="已開始製作訂單"
            )
            
        except Exception as e:
            logger.error(f"開始製作失敗: {str(e)}")
            return self.error_response(f"開始製作失敗: {str(e)}", status=500)
    

    def mark_as_ready_using_manager(self, order_id, barista_name):
        """標記訂單為就緒 - 使用 OrderStatusManager"""
        try:
            logger.info(f"🔄 使用 OrderStatusManager 標記訂單 #{order_id} 為就緒")
            
            # 使用 OrderStatusManager
            result = OrderStatusManager.mark_as_ready_manually(order_id, barista_name)
            
            if result.get('success'):
                # 重新獲取訂單以序列化
                order = OrderModel.objects.get(id=order_id)
                order_data = self.serialize_order_with_queue(order)
                
                return self.success_response(
                    data=order_data,
                    message="訂單已標記為就緒"
                )
            else:
                error_msg = result.get('error', '標記就緒失敗')
                logger.error(f"標記就緒失敗: {error_msg}")
                return self.error_response(f"標記就緒失敗: {error_msg}", status=400)
            
        except Exception as e:
            logger.error(f"標記就緒失敗: {str(e)}")
            return self.error_response(f"標記就緒失敗: {str(e)}", status=500)
    
    def mark_as_complete_using_manager(self, order_id, staff_name):
        """標記訂單為完成 - 使用 OrderStatusManager"""
        try:
            logger.info(f"🔄 使用 OrderStatusManager 標記訂單 #{order_id} 為完成")
            
            # 使用 OrderStatusManager
            result = OrderStatusManager.mark_as_completed_manually(order_id, staff_name)
            
            if result.get('success'):
                # 重新獲取訂單以序列化
                order = OrderModel.objects.get(id=order_id)
                order_data = self.serialize_order_with_queue(order)
                
                return self.success_response(
                    data=order_data,
                    message="訂單已標記為完成"
                )
            else:
                error_msg = result.get('error', '標記完成失敗')
                logger.error(f"標記完成失敗: {error_msg}")
                return self.error_response(f"標記完成失敗: {error_msg}", status=400)
            
        except Exception as e:
            logger.error(f"標記完成失敗: {str(e)}")
            return self.error_response(f"標記完成失敗: {str(e)}", status=500)
    
    def reorder_queue(self, request):
        """重新排序隊列"""
        try:
            data = self.get_json_data(request)
            new_order = data.get('order', [])
            
            if not new_order:
                return self.error_response("無效的排序數據", status=400)
            
            queue_manager = CoffeeQueueManager()
            success = queue_manager.reorder_queue(new_order)
            
            if success:
                return self.success_response(message="隊列重新排序成功")
            else:
                return self.error_response("隊列重新排序失敗", status=500)
                
        except Exception as e:
            logger.error(f"重新排序隊列失敗: {str(e)}")
            return self.error_response(f"重新排序隊列失敗: {str(e)}", status=500)
    
    def serialize_order_with_queue(self, order):
        """序列化訂單及隊列信息"""
        order_data = OrderDataSerializer.serialize_order(
            order, 
            include_queue_info=True,
            include_items=True
        )
        return order_data


# ==================== 新的API端點 ====================

@csrf_exempt
@require_POST
@staff_api_required
def api_mark_order_as_ready(request, order_id):
    """API: 手動標記訂單為就緒（使用OrderStatusManager）"""
    try:
        logger.info(f"📋 API: 員工 {request.user.username} 請求標記訂單 #{order_id} 為就緒")
        
        # 使用 OrderStatusManager
        staff_name = request.user.username
        result = OrderStatusManager.mark_as_ready_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ API: 訂單 #{order_id} 已標記為就緒")
            return JsonResponse(result)
        else:
            logger.error(f"❌ API: 標記訂單 #{order_id} 為就緒失敗: {result.get('error')}")
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"❌ API: 標記訂單為就緒失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@staff_api_required
def api_mark_order_as_completed(request, order_id):
    """API: 手動標記訂單為已提取（使用OrderStatusManager）"""
    try:
        logger.info(f"📋 API: 員工 {request.user.username} 請求標記訂單 #{order_id} 為已提取")
        
        # 使用 OrderStatusManager
        staff_name = request.user.username
        result = OrderStatusManager.mark_as_completed_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ API: 訂單 #{order_id} 已標記為已提取")
            return JsonResponse(result)
        else:
            logger.error(f"❌ API: 標記訂單 #{order_id} 為已提取失敗: {result.get('error')}")
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"❌ API: 標記訂單為已提取失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


# ==================== 倒計時API（保持不變） ====================

@method_decorator(login_required, name='dispatch')
class CountdownAPI(View):
    """倒數計時API"""
    def get(self, request, order_id):
        try:
            order = OrderModel.objects.get(id=order_id)
            
            # 驗證訂單屬於當前用戶
            if request.user.is_authenticated and order.user != request.user:
                return JsonResponse({'error': '無權存取此訂單'}, status=403)
            
            if order.payment_status != "paid":
                return JsonResponse({'error': '訂單未支付'}, status=400)
            
            # 使用統一的序列化器
            order_data = OrderDataSerializer.serialize_order(
                order,
                include_queue_info=True,
                include_items=False
            )
            
            # 添加倒計時特定數據
            response_data = {
                'success': True,
                'data': order_data
            }
            
            return JsonResponse(response_data)
            
        except OrderModel.DoesNotExist:
            return JsonResponse({'error': '訂單不存在'}, status=404)
        except Exception as e:
            logger.error(f"倒數API錯誤: {str(e)}", exc_info=True)
            return JsonResponse({'error': '伺服器錯誤'}, status=500)


# ==================== 統計API ====================

@csrf_exempt
@require_GET
@staff_api_required
def get_dashboard_stats(request):
    """獲取儀表板統計數據"""
    try:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 今日訂單統計
        today_orders = OrderModel.objects.filter(created_at__gte=today_start)
        today_count = today_orders.count()
        today_revenue = sum(order.total_price for order in today_orders if order.payment_status == 'paid')
        
        # 隊列統計
        waiting_count = CoffeeQueue.objects.filter(status='waiting').count()
        preparing_count = CoffeeQueue.objects.filter(status='preparing').count()
        ready_count = CoffeeQueue.objects.filter(status='ready').count()
        
        # 支付統計
        pending_payment_count = OrderModel.objects.filter(
            payment_status="pending",
            status='pending',
            payment_timeout__gt=now
        ).count()
        
        stats = {
            'today': {
                'orders': today_count,
                'revenue': float(today_revenue),
            },
            'queue': {
                'waiting': waiting_count,
                'preparing': preparing_count,
                'ready': ready_count,
                'total': waiting_count + preparing_count + ready_count,
            },
            'payments': {
                'pending': pending_payment_count,
            },
            'timestamp': now.isoformat(),
        }
        
        return JsonResponse(ApiResponseFormatter.success(data=stats))
        
    except Exception as e:
        logger.error(f"獲取統計數據失敗: {str(e)}")
        return JsonResponse(
            ApiResponseFormatter.error(f"獲取統計數據失敗: {str(e)}"),
            status=500
        )


# ==================== 簡化的舊API（兼容性） ====================

@csrf_exempt
@require_GET
def get_recent_orders(request):
    """獲取最近訂單（兼容舊API）"""
    try:
        # 使用統一的API
        unified_api = UnifiedOrderAPI()
        unified_api.request = request
        return unified_api.get(request)
        
    except Exception as e:
        logger.error(f"獲取最近訂單失敗: {str(e)}")
        return JsonResponse(ApiResponseFormatter.error(str(e)), status=500)


# 在适当的地方使用缓存查询
@csrf_exempt
@require_GET
def get_active_orders(request):
    """获取活动订单（使用缓存）"""
    try:
        from .query_optimizer import query_optimizer
        
        # 使用缓存的查询
        orders = query_optimizer.get_active_orders_cached(request.user if request.user.is_authenticated else None)
        
        # 序列化
        orders_data = [
            OrderDataSerializer.serialize_order(order, include_queue_info=True, include_items=False)
            for order in orders
        ]
        
        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data),
            'cached': True  # 指示是否来自缓存
        })
        
    except Exception as e:
        logger.error(f"获取活动订单失败: {str(e)}")
        return JsonResponse(ApiResponseFormatter.error(str(e)), status=500)
    

@csrf_exempt
@require_GET
def get_quick_order_times(request):
    """獲取快速訂單時間信息API"""
    try:
        result = time_service.calculate_all_quick_order_times()
        return JsonResponse(result)
    
    except Exception as e:
        logger.error(f"獲取快速訂單時間信息失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def update_order_pickup_times_api(request):
    """更新訂單取貨時間API"""
    try:
        data = json.loads(request.body)
        order_ids = data.get('order_ids', [])
        
        if not order_ids:
            return JsonResponse({
                'success': False,
                'error': '未提供訂單ID'
            }, status=400)
        
        result = time_service.update_order_pickup_times(order_ids)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的JSON數據'
        }, status=400)
    
    except Exception as e:
        logger.error(f"更新訂單取貨時間API失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 健康檢查API ====================

@csrf_exempt
@require_GET
def health_check(request):
    """系統健康檢查端點"""
    try:
        # 檢查資料庫連接
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = True
        
        # 檢查隊列系統
        queue_ok = True
        try:
            from eshop.queue_manager import CoffeeQueueManager
            manager = CoffeeQueueManager()
            stats = manager.get_queue_stats()
            queue_stats = stats
        except Exception:
            queue_ok = False
            queue_stats = None
        
        # 檢查時間服務
        time_ok = True
        try:
            from eshop.time_service import time_service
            current_time = time_service.get_current_hk_time()
        except Exception:
            time_ok = False
            current_time = None
        
        # 構建回應
        response_data = {
            'status': 'healthy' if db_ok and queue_ok and time_ok else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': {
                    'status': 'healthy' if db_ok else 'unhealthy',
                    'message': 'Database connection OK' if db_ok else 'Database connection failed'
                },
                'queue_system': {
                    'status': 'healthy' if queue_ok else 'unhealthy',
                    'message': 'Queue system OK' if queue_ok else 'Queue system failed',
                    'stats': queue_stats
                },
                'time_service': {
                    'status': 'healthy' if time_ok else 'unhealthy',
                    'message': 'Time service OK' if time_ok else 'Time service failed',
                    'current_time': current_time
                }
            },
            'version': '1.0.0',
            'message': 'BetweenCoffee Delivery System'
        }
        
        status_code = 200 if db_ok and queue_ok and time_ok else 503
        return JsonResponse(response_data, status=status_code)
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': f'Health check failed: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=503)
