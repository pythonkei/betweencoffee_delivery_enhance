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
    """會員忠誠度儀表板 - 簡化版（專注積分系統）"""
    try:
        # 獲取忠誠度記錄
        loyalty, created = CustomerLoyalty.objects.get_or_create(
            user=request.user
        )
        
        # 檢查積分有效期
        expired_points = loyalty.check_points_expiry()
        if expired_points > 0:
            messages.warning(
                request, 
                f"您的 {expired_points} 積分已過期，請及時使用積分"
            )
        
        # 獲取積分摘要信息
        points_summary = loyalty.get_points_summary()
        
        # 獲取會員基本信息
        membership_info = loyalty.get_membership_info()
        
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
        
        context = {
            'loyalty': loyalty,
            'points_summary': points_summary,
            'membership_info': membership_info,
            'active_coupons': active_coupons,
            'recent_activities': recent_activities,
            'available_rewards': available_rewards,
            'profile': getattr(request.user, 'profile', None),
        }
        
        return render(request, 'socialuser/loyalty_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"加載儀表板失敗: {str(e)}")
        return redirect('profile')


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
        
        # 先獲取獎勵信息，然後再兌換
        available_rewards = loyalty.get_available_rewards()
        reward_info = next((r for r in available_rewards if r['id'] == reward_id), None)
        
        if not reward_info:
            return JsonResponse({
                'success': False,
                'message': '獎勵不存在或不可兌換'
            })
        
        success, message = loyalty.redeem_reward(reward_id)
        
        if success:
            # 記錄活動
            CustomerActivity.record_reward_redeemed(
                request.user,
                reward_info['name'],
                reward_info['points_required']
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
        # 記錄錯誤但不顯示消息，避免消息中間件問題
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"加載優惠券列表失敗: {str(e)}")
        return redirect('socialuser:loyalty_dashboard')


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
def points_summary(request):
    """積分摘要信息頁面"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        
        # 獲取積分摘要信息
        points_summary = loyalty.get_points_summary()
        
        # 獲取積分獲取規則
        point_rules = [
            {
                'type': '消費積分',
                'description': '每消費 $10 可獲得 1 積分',
                'icon': 'fa-shopping-cart',
                'color': 'primary'
            },
            {
                'type': '推薦積分',
                'description': '成功推薦好友註冊可獲得 50 積分',
                'icon': 'fa-user-plus',
                'color': 'success'
            },
            {
                'type': '活動積分',
                'description': '參與店內活動可獲得額外積分',
                'icon': 'fa-gift',
                'color': 'warning'
            }
        ]
        
        # 獲取積分有效期信息
        expiry_info = None
        if points_summary['days_until_expiry'] is not None:
            if points_summary['days_until_expiry'] <= 7:
                expiry_status = 'danger'
                expiry_message = f"積分將在 {points_summary['days_until_expiry']} 天後過期"
            elif points_summary['days_until_expiry'] <= 30:
                expiry_status = 'warning'
                expiry_message = f"積分將在 {points_summary['days_until_expiry']} 天後過期"
            else:
                expiry_status = 'success'
                expiry_message = f"積分有效期剩餘 {points_summary['days_until_expiry']} 天"
            
            expiry_info = {
                'status': expiry_status,
                'message': expiry_message,
                'expiry_date': points_summary['points_expiry_date'],
                'days_remaining': points_summary['days_until_expiry']
            }
        
        context = {
            'loyalty': loyalty,
            'points_summary': points_summary,
            'point_rules': point_rules,
            'expiry_info': expiry_info,
        }
        
        return render(request, 'socialuser/points_summary.html', context)
        
    except Exception as e:
        messages.error(request, f"加載積分信息失敗: {str(e)}")
        return redirect('loyalty_dashboard')


@login_required
def api_loyalty_status(request):
    """API: 獲取忠誠度狀態（用於AJAX更新）"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)
        
        # 獲取積分摘要信息
        points_summary = loyalty.get_points_summary()
        
        return JsonResponse({
            'success': True,
            'points': loyalty.points,
            'total_spent': float(loyalty.total_spent),
            'total_orders': loyalty.total_orders,
            'available_rewards': loyalty.get_available_rewards(),
            'points_summary': points_summary,
            'membership_info': loyalty.get_membership_info(),
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