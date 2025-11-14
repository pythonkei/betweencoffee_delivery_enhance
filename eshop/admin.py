# eshop/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import CoffeeItem, BeanItem, OrderModel


# 在OrderModelAdmin类上方添加（约第5行）
def mark_as_quick(modeladmin, request, queryset):
    queryset.update(is_quick_order=True)
mark_as_quick.short_description = "🟢 标记为快速订单"


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
    list_display = ('name', 'price_200g', 'price_1kg', 'is_published', 'is_shop_hot_item', 'image_preview', 'index_image_preview')
    list_filter = ('is_published', 'is_shop_hot_item', 'list_date')
    search_fields = ('name', 'introduction', 'description')
    list_editable = ('is_published', 'is_shop_hot_item')  # 允许直接编辑排序字段
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'introduction', 'description', 'price_200g', 'price_1kg', 'origin', 'flavor')
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



# Customize the django backend admin interface to display the parsed JSON data.
class OrderModelAdmin(admin.ModelAdmin):
    ordering = ('-is_quick_order', '-created_at')  # ordering
    actions = [mark_as_quick]  # 批量动作

    # Quick order Color
    def colored_quick_order(self, obj):
        color = '#4CAF50' if obj.is_quick_order else '#9E9E9E'
        return format_html(
            '<span style="color: {}; font-size: 1.5em;">⬤</span>',
            color
        )
    colored_quick_order.short_description = 'Quick'
    
    list_display = ('id', 'user', 'name', 'phone', 'payment_method', 'is_paid', 'created_at', 'total_price', 'is_quick_order')
    list_filter = ('payment_method', 'is_quick_order', 'is_paid', 'is_delivery')
    search_fields = ('name', 'phone', 'email', 'user__username')

    readonly_fields = ('created_at',)  # Make 'created_at' read-only
    readonly_fields = ('display_items',)  # Make the custom field read-only
    ordering = ('-is_quick_order', '-created_at')  # 先按快速订单倒序，再按时间倒序

    list_filter = ('is_quick_order', 'is_paid', 'is_delivery')
    
    # Custom method to display items in a structured format
    def display_items(self, obj):
        items = obj.get_items()  # Parse the JSON data
        html = '<div style="margin-left: 20px;">'
        for item in items:
            html += '<div style="margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px;">'
            for key, value in item.items():
                html += f'<p><strong>{key}:</strong> {value}</p>'
            html += '</div>'
        html += '</div>'
        return format_html(html)
    display_items.short_description = 'Items'  # Set the column header name

    # Use fieldsets to organize the display
    fieldsets = (
        ('Order Information', {
            'fields': (('name', 'phone'), 'email', 'is_quick_order', 'total_price', 'is_paid', 'is_delivery'),
        }),
        ('Items', {
            'fields': ('display_items',),  # Display the custom field
        }),
    )


def mark_as_preparing(modeladmin, request, queryset):
    queryset.update(status='preparing')
    for order in queryset:
        order.send_order_notification("preparing")
mark_as_preparing.short_description = "标记为制作中"

def mark_as_ready(modeladmin, request, queryset):
    queryset.update(status='ready')
    for order in queryset:
        order.send_order_notification("ready")
mark_as_ready.short_description = "标记为已就绪"


# 在OrderModelAdmin中添加这些动作
OrderModelAdmin.actions = [mark_as_preparing, mark_as_ready, mark_as_quick]

# 注册模型
admin.site.register(CoffeeItem, CoffeeItemAdmin)
admin.site.register(BeanItem, BeanItemAdmin)
admin.site.register(OrderModel, OrderModelAdmin)