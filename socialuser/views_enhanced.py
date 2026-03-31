# socialuser/views_enhanced.py
# 會員系統強化 - 視圖
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .models_enhanced import (
    CustomerLoyalty, CustomerCoupon, CustomerActivity
)


@login_required
def loyalty_dashboard(request):
    """會員忠誠度儀表板"""
    try:
        # 獲取忠誠度記錄
        loyalty, created = CustomerLoyalty.objects.get_or_create(
            user=request.user
        )
        
        # 獲取可用優惠券
        active_coupons = CustomerCoupon.objects.filter(
            user=request.user,
            is_used=False,
            valid_to__gte=timezone.now()
        ).order_by('-created_at')[:10]
        
        # 獲取近期活動
        recent_activities = CustomerActivity.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        # 獲取可兌換獎勵
        available_rewards = loyalty.get_available_rewards()
        
        # 獲取等級信息
        tier_info = loyalty.get_tier_info()
        
        context = {
            'loyalty': loyalty,
            'active_coupons': active_coupons,
            'recent_activities': recent_activities,
            'available_rewards': available_rewards,
            'tier_info': tier_info,
            'profile': getattr(request.user, 'profile', None),
        }
        
        return render(request, 'socialuser/loyalty_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"加載儀表板失敗: {str(e)}")
        return redirect('profile')


@login_required
def rewards_list(request):
    """獎勵列表頁面"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        available_rewards = loyalty.get_available_rewards()
        
        # 所有可能的獎勵（包括不可兌換的）
        all_rewards = [
            {
                'id': 'free_coffee',
                'name': '免費咖啡一杯',
                'points_required': 10,
                'description': '兌換任意標準杯型咖啡一杯',
                'icon': 'fa-mug-hot',
                'color': 'success',
                'available': loyalty.points >= 10
            },
            {
                'id': 'free_upgrade',
                'name': '免費升級大杯',
                'points_required': 20,
                'description': '免費升級任意咖啡至大杯',
                'icon': 'fa-arrow-up',
                'color': 'warning',
                'available': loyalty.points >= 20
            },
            {
                'id': 'birthday_gift',
                'name': '生日驚喜禮包',
                'points_required': 50,
                'description': '生日當月免費咖啡+甜點',
                'icon': 'fa-gift',
                'color': 'danger',
                'available': loyalty.points >= 50
            },
        ]
        
        context = {
            'loyalty': loyalty,
            'available_rewards': available_rewards,
            'all_rewards': all_rewards,
        }
        
        return render(request, 'socialuser/rewards_list.html', context)
        
    except Exception as e:
        messages.error(request, f"加載獎勵列表失敗: {str(e)}")
        return redirect('loyalty_dashboard')


@login_required
@require_http_methods(["POST"])
def redeem_reward(request):
    """兌換獎勵"""
    try:
        data = json.loads(request.body)
        reward_id = data.get('reward_id')
        
        if not reward_id:
            return JsonResponse({
                'success': False,
                'message': '請選擇要兌換的獎勵'
            })
        
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        success, message = loyalty.redeem_reward(reward_id)
        
        if success:
            # 記錄活動
            reward_name = next(
                (r['name'] for r in loyalty.get_available_rewards() 
                 if r['id'] == reward_id),
                reward_id
            )
            CustomerActivity.record_reward_redeemed(
                request.user,
                reward_name,
                next(r['points_required'] for r in loyalty.get_available_rewards() 
                     if r['id'] == reward_id)
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'points': loyalty.points
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'兌換失敗: {str(e)}'
        })


@login_required
def coupons_list(request):
    """優惠券列表"""
    try:
        # 獲取所有優惠券（包括已使用和過期的）
        all_coupons = CustomerCoupon.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        # 分離有效和無效的優惠券
        active_coupons = []
        expired_coupons = []
        used_coupons = []
        
        now = timezone.now()
        for coupon in all_coupons:
            if coupon.is_used:
                used_coupons.append(coupon)
            elif coupon.valid_to < now:
                expired_coupons.append(coupon)
            else:
                active_coupons.append(coupon)
        
        context = {
            'active_coupons': active_coupons,
            'expired_coupons': expired_coupons[:10],  # 只顯示最近10個過期的
            'used_coupons': used_coupons[:10],  # 只顯示最近10個已使用的
        }
        
        return render(request, 'socialuser/coupons_list.html', context)
        
    except Exception as e:
        messages.error(request, f"加載優惠券列表失敗: {str(e)}")
        return redirect('loyalty_dashboard')


@login_required
@require_http_methods(["POST"])
def apply_coupon(request):
    """應用優惠券（在購物車或結賬時）"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')
        order_amount = Decimal(data.get('order_amount', 0))
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': '請輸入優惠碼'
            })
        
        # 查找優惠券
        try:
            coupon = CustomerCoupon.objects.get(
                code=coupon_code,
                user=request.user
            )
        except CustomerCoupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '優惠碼不存在'
            })
        
        # 應用折扣
        discount, message = coupon.apply_discount(order_amount)
        
        if discount > 0:
            # 標記為已使用
            coupon.mark_as_used()
            
            # 記錄活動
            CustomerActivity.record_coupon_used(
                request.user,
                coupon_code,
                discount
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'discount': float(discount),
                'final_amount': float(order_amount - discount)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'應用優惠券失敗: {str(e)}'
        })


@login_required
def activity_history(request):
    """活動歷史記錄"""
    try:
        activities = CustomerActivity.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]  # 只顯示最近50條
        
        # 分組活動（按日期）
        grouped_activities = {}
        for activity in activities:
            date_key = activity.created_at.date().isoformat()
            if date_key not in grouped_activities:
                grouped_activities[date_key] = []
            grouped_activities[date_key].append(activity)
        
        context = {
            'grouped_activities': grouped_activities,
            'total_activities': activities.count(),
        }
        
        return render(request, 'socialuser/activity_history.html', context)
        
    except Exception as e:
        messages.error(request, f"加載活動歷史失敗: {str(e)}")
        return redirect('loyalty_dashboard')


@login_required
def tier_info(request):
    """會員等級詳細信息"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        tier_info = loyalty.get_tier_info()
        
        # 所有等級信息
        all_tiers = [
            {
                'id': 'bronze',
                'name': '銅級會員',
                'min_spent': 0,
                'discount': '無折扣',
                'benefits': ['積分累積'],
                'color': '#CD7F32',
                'icon': 'fa-star',
                'is_current': loyalty.tier == 'bronze'
            },
            {
                'id': 'silver',
                'name': '銀級會員',
                'min_spent': 500,
                'discount': '95折',
                'benefits': ['積分累積', '95折優惠'],
                'color': '#C0C0C0',
                'icon': 'fa-star-half-alt',
                'is_current': loyalty.tier == 'silver'
            },
            {
                'id': 'gold',
                'name': '金級會員',
                'min_spent': 1000,
                'discount': '9折',
                'benefits': ['積分累積', '9折優惠', '免費升級杯型'],
                'color': '#FFD700',
                'icon': 'fa-star',
                'is_current': loyalty.tier == 'gold'
            },
            {
                'id': 'platinum',
                'name': '白金會員',
                'min_spent': 2000,
                'discount': '85折',
                'benefits': ['積分累積', '85折優惠', '免費升級杯型', '優先服務'],
                'color': '#E5E4E2',
                'icon': 'fa-crown',
                'is_current': loyalty.tier == 'platinum'
            },
        ]
        
        context = {
            'loyalty': loyalty,
            'tier_info': tier_info,
            'all_tiers': all_tiers,
            'progress_percentage': tier_info['progress'],
        }
        
        return render(request, 'socialuser/tier_info.html', context)
        
    except Exception as e:
        messages.error(request, f"加載等級信息失敗: {str(e)}")
        return redirect('loyalty_dashboard')


@login_required
def api_loyalty_status(request):
    """API: 獲取忠誠度狀態（用於AJAX更新）"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        
        return JsonResponse({
            'success': True,
            'points': loyalty.points,
            'tier': loyalty.tier,
            'tier_display': loyalty.get_tier_display(),
            'total_spent': float(loyalty.total_spent),
            'total_orders': loyalty.total_orders,
            'discount_rate': float(loyalty.discount_rate),
            'available_rewards': loyalty.get_available_rewards(),
            'tier_info': loyalty.get_tier_info(),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_recent_activities(request):
    """API: 獲取近期活動"""
    try:
        activities = CustomerActivity.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'type': activity.activity_type,
                'type_display': activity.get_activity_type_display(),
                'points_change': activity.points_change,
                'description': activity.description,
                'created_at': activity.created_at.isoformat(),
                'time_ago': _time_ago(activity.created_at),
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'count': len(activities_data),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_active_coupons(request):
    """API: 獲取有效優惠券"""
    try:
        coupons = CustomerCoupon.objects.filter(
            user=request.user,
            is_used=False,
            valid_to__gte=timezone.now()
        ).order_by('-created_at')
        
        coupons_data = []
        for coupon in coupons:
            coupons_data.append({
                'code': coupon.code,
                'type': coupon.coupon_type,
                'type_display': coupon.get_coupon_type_display(),
                'value': float(coupon.value),
                'min_order_amount': float(coupon.min_order_amount),
                'valid_to': coupon.valid_to.isoformat(),
                'description': coupon.description,
                'days_remaining': (coupon.valid_to - timezone.now()).days,
            })
        
        return JsonResponse({
            'success': True,
            'coupons': coupons_data,
            'count': len(coupons_data),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def _time_ago(dt):
    """計算時間間隔的人性化顯示"""
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}年前"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}個月前"
    elif diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小時前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分鐘前"
    else:
        return "剛剛"