# eshop/admin.py - 修正版
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import CoffeeItem, BeanItem, OrderModel, CoffeeQueue, Barista, CoffeePreparationTime
from eshop.order_status_manager import OrderStatusManager


# 員工訂單管理視圖
def staff_order_management(request):
    """員工訂單管理界面"""
    if not request.user.is_staff:
        messages.error(request, "無權訪問此頁面")
        return redirect('admin:index')
    
    # 獲取需要處理的訂單 - 員工管理頁面保持快速訂單優先排序
    preparing_orders = OrderModel.objects.filter(
        payment_status='paid', 
        status='preparing'
    ).order_by('-is_quick_order', 'created_at')  # 快速訂單優先
    
    ready_orders = OrderModel.objects.filter(
        payment_status='paid', 
        status='ready'
    ).order_by('-is_quick_order', 'created_at')  # 快速訂單優先
    
    recent_completed_orders = OrderModel.objects.filter(
        payment_status='paid',
        status='completed',
        picked_up_at__gte=timezone.now() - timezone.timedelta(hours=4)
    ).order_by('-picked_up_at')
    
    # 今日訂單統計
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_orders_today = OrderModel.objects.filter(
        created_at__gte=today_start,
        payment_status='paid'
    ).count()
    
    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'recent_completed_orders': recent_completed_orders,
        'total_orders_today': total_orders_today,
        'title': '訂單管理',
        'site_header': 'Between Coffee - 員工管理',
        'staff_user': request.user
    }
    
    return render(request, 'admin/staff_order_management.html', context)


def mark_order_ready(request, order_id):
    """標記訂單為已就緒 - 使用 OrderStatusManager"""
    if not request.user.is_staff:
        messages.error(request, "無權執行此操作")
        return redirect('admin:index')
    
    try:
        staff_name = request.user.get_full_name() or request.user.username
        result = OrderStatusManager.mark_as_ready_manually(
            order_id=order_id,
            staff_name=staff_name
        )
        
        if result['success']:
            messages.success(request, f'訂單 #{order_id} 已標記為已就緒')
        else:
            messages.error(request, f'操作失敗: {result["message"]}')
            
    except Exception as e:
        messages.error(request, f'系統錯誤: {str(e)}')
    
    # 使用正確的URL名稱
    return redirect('admin:staff_order_management')


def mark_order_completed(request, order_id):
    """標記訂單為已提取 - 使用 OrderStatusManager"""
    if not request.user.is_staff:
        messages.error(request, "無權執行此操作")
        return redirect('admin:index')
    
    try:
        staff_name = request.user.get_full_name() or request.user.username
        result = OrderStatusManager.mark_as_completed_manually(
            order_id=order_id,
            staff_name=staff_name
        )
        
        if result['success']:
            messages.success(request, f'訂單 #{order_id} 已標記為已提取')
        else:
            messages.error(request, f'操作失敗: {result["message"]}')
            
    except Exception as e:
        messages.error(request, f'系統錯誤: {str(e)}')
    
    # 使用正確的URL名稱
    return redirect('admin:staff_order_management')


# 管理動作 - 使用 OrderStatusManager
def mark_as_preparing(modeladmin, request, queryset): 
    """標記為制作中 - 使用 OrderStatusManager"""
    success_count = 0
    fail_count = 0
    staff_name = request.user.get_full_name() or request.user.username
    
    for order in queryset:
        if order.payment_status == 'paid' and order.status == 'pending':
            result = OrderStatusManager.mark_as_preparing_manually(
                order_id=order.id,
                staff_name=staff_name
            )
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                logger.error(f"標記訂單 {order.id} 為制作中失敗: {result['message']}")
    
    if success_count > 0:
        messages.success(request, f"已標記 {success_count} 個訂單為制作中")
    if fail_count > 0:
        messages.error(request, f"{fail_count} 個訂單標記失敗")

mark_as_preparing.short_description = "☕ 標記為制作中"

def mark_as_ready(modeladmin, request, queryset):
    """標記為已就緒 - 使用 OrderStatusManager"""
    success_count = 0
    fail_count = 0
    staff_name = request.user.get_full_name() or request.user.username
    
    for order in queryset:
        if order.payment_status == 'paid' and order.status == 'preparing':
            result = OrderStatusManager.mark_as_ready_manually(
                order_id=order.id,
                staff_name=staff_name
            )
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                logger.error(f"標記訂單 {order.id} 為就緒失敗: {result['message']}")
    
    if success_count > 0:
        messages.success(request, f"已標記 {success_count} 個訂單為已就緒")
    if fail_count > 0:
        messages.error(request, f"{fail_count} 個訂單標記失敗")

mark_as_ready.short_description = "✅ 標記為已就緒"

def mark_as_completed(modeladmin, request, queryset):
    """標記為已提取 - 使用 OrderStatusManager"""
    success_count = 0
    fail_count = 0
    staff_name = request.user.get_full_name() or request.user.username
    
    for order in queryset:
        if order.payment_status == 'paid' and order.status == 'ready':
            result = OrderStatusManager.mark_as_completed_manually(
                order_id=order.id,
                staff_name=staff_name
            )
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                logger.error(f"標記訂單 {order.id} 為已提取失敗: {result['message']}")
    
    if success_count > 0:
        messages.success(request, f"已標記 {success_count} 個訂單為已提取")
    if fail_count > 0:
        messages.error(request, f"{fail_count} 個訂單標記失敗")

mark_as_completed.short_description = "📦 標記為已提取"

def mark_as_quick(modeladmin, request, queryset):
    """標記為快速訂單"""
    queryset.update(is_quick_order=True)
    messages.success(request, f"已標記 {queryset.count()} 個訂單為快速訂單")

mark_as_quick.short_description = "🟢 標記為快速訂單"


# OrderModel Admin
class OrderModelAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)  # 只按创建时间倒序排列
    
    actions = [mark_as_quick, mark_as_preparing, mark_as_ready, mark_as_completed]

    # 快速订单颜色标识
    def colored_quick_order(self, obj):
        color = '#4CAF50' if obj.is_quick_order else '#9E9E9E'
        return format_html(
            '<span style="color: {}; font-size: 1.5em;">⬤</span>',
            color
        )
    colored_quick_order.short_description = 'Quick'
    
    # 支付状态带徽章显示
    def payment_status_with_badge(self, obj):
        status_map = {
            'pending': ('warning', '待支付'),
            'paid': ('success', '已支付'),
            'cancelled': ('danger', '已取消'),
            'expired': ('secondary', '已过期')
        }
        
        color, text = status_map.get(obj.payment_status, ('secondary', obj.payment_status))
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, text
        )
    payment_status_with_badge.short_description = '支付状态'
    payment_status_with_badge.admin_order_field = 'payment_status'
    
    list_display = (
        'id', 'user', 'name', 'phone', 'payment_method', 
        'payment_status_with_badge', 'status_with_badge', 'created_at', 
        'total_price', 'colored_quick_order', 'picked_up_at'
    )
    
    list_filter = ('payment_method', 'is_quick_order', 'payment_status', 'status')
    search_fields = ('name', 'phone', 'email', 'user__username', 'pickup_code')
    
    readonly_fields = ('created_at', 'display_items', 'picked_up_at', 'picked_up_by')
    # 在ModelAdmin中也保持一致，不优先排序快速订单
    ordering = ('-created_at',)

    # 自定义状态显示带徽章
    def status_with_badge(self, obj):
        status_map = {
            'pending': ('secondary', '待處理'),
            'waiting': ('info', '等待制作'),
            'preparing': ('warning', '製作中'),
            'ready': ('success', '已就緒'),
            'completed': ('info', '已提取')
        }
        
        color, text = status_map.get(obj.status, ('secondary', obj.status))
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, text
        )
    status_with_badge.short_description = '狀態'
    
    # 自定义方法显示订单项目
    def display_items(self, obj):
        items = obj.get_items_with_chinese_options()
        html = '<div style="margin-left: 20px;">'
        for item in items:
            html += '<div style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">'
            html += f'<p><strong>{item["name"]}</strong> × {item["quantity"]}</p>'
            html += f'<p style="margin: 0; color: #666;">價格: ${item["total_price"]}</p>'
            
            # 显示选项
            options = []
            if item.get('cup_level_cn'):
                options.append(f'杯型: {item["cup_level_cn"]}')
            if item.get('milk_level_cn'):
                options.append(f'牛奶: {item["milk_level_cn"]}')
            if item.get('grinding_level_cn'):
                options.append(f'研磨: {item["grinding_level_cn"]}')
            if item.get('weight'):
                options.append(f'重量: {item["weight"]}')
                
            if options:
                html += f'<p style="margin: 0; color: #888; font-size: 0.9em;">{", ".join(options)}</p>'
                
            html += '</div>'
        html += '</div>'
        return format_html(html)
    display_items.short_description = '訂單項目'

    # 使用字段集组织显示
    fieldsets = (
        ('訂單信息', {
            'fields': (
                ('name', 'phone'), 'email', 'user', 
                'is_quick_order', 'total_price', 'payment_method',
                'payment_status', 'status', 'pickup_code'
            ),
        }),
        ('時間信息', {
            'fields': ('created_at', 'estimated_ready_time', 'picked_up_at', 'picked_up_by'),
        }),
        ('訂單項目', {
            'fields': ('display_items',),
        }),
    )
    
    # 添加自定义URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('staff-management/', self.admin_site.admin_view(staff_order_management), name='staff_order_management'),
            path('mark-ready/<int:order_id>/', self.admin_site.admin_view(mark_order_ready), name='mark_order_ready'),
            path('mark-completed/<int:order_id>/', self.admin_site.admin_view(mark_order_completed), name='mark_order_completed'),
        ]
        return custom_urls + urls

# 其他 ModelAdmin 保持不变...

# CoffeeItem Admin
class CoffeeItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_published', 'is_shop_hot_item', 'image_preview', 'index_image_preview')
    list_filter = ('is_published', 'is_shop_hot_item', 'list_date')
    search_fields = ('name', 'introduction', 'description')
    list_editable = ('is_published', 'is_shop_hot_item')  # 允许直接编辑排序字段
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'introduction', 'description', 'price', 'origin', 'flavor')
        }),
        ('图片管理', {
            'fields': ('image', 'image_index'),
            'description': '详情页图片用于咖啡菜单和详情页，首页图片专门用于首页展示'
        }),
        ('选项设置', {
            'fields': ('cup_level', 'milk_level')
        }),
        ('状态管理', {
            'fields': ('is_published', 'is_shop_hot_item', 'list_date')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "-"
    image_preview.short_description = '详情页图片'

    def index_image_preview(self, obj):
        if obj.image_index:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image_index.url)
        elif obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; opacity: 0.5;" title="使用详情页图片" />', obj.image.url)
        return "-"
    index_image_preview.short_description = '首页图片'


# BeanItem Admin
class BeanItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_200g', 'price_500g', 'is_published', 'is_shop_hot_item', 'image_preview', 'index_image_preview')
    list_filter = ('is_published', 'is_shop_hot_item', 'list_date')
    search_fields = ('name', 'introduction', 'description')
    list_editable = ('is_published', 'is_shop_hot_item')  # 允许直接编辑排序字段
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'introduction', 'description', 'price_200g', 'price_500g', 'origin', 'flavor')
        }),
        ('图片管理', {
            'fields': ('image', 'image_index'),
            'description': '详情页图片用于咖啡豆菜单和详情页，首页图片专门用于首页展示'
        }),
        ('研磨选项', {
            'fields': ('grinding_level',)
        }),
        ('状态管理', {
            'fields': ('is_published', 'is_shop_hot_item', 'list_date')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "-"
    image_preview.short_description = '详情页图片'

    def index_image_preview(self, obj):
        if obj.image_index:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image_index.url)
        elif obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; opacity: 0.5;" title="使用详情页图片" />', obj.image.url)
        return "-"
    index_image_preview.short_description = '首页图片'


# 注册模型
admin.site.register(CoffeeItem, CoffeeItemAdmin)
admin.site.register(BeanItem, BeanItemAdmin)
admin.site.register(OrderModel, OrderModelAdmin)
admin.site.register(CoffeeQueue)
admin.site.register(Barista)
admin.site.register(CoffeePreparationTime)