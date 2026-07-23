# socialuser/views_enhanced.py
# 會員系統強化 - 視圖
import json
from decimal import Decimal

from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models_enhanced import CustomerActivity, CustomerLoyalty


@login_required
def loyalty_dashboard(request):
    """會員忠誠度儀表板 - 簡化版（專注積分系統）"""
    try:
        # 獲取忠誠度記錄
        loyalty, created = CustomerLoyalty.objects.get_or_create(user=request.user)

        # 檢查積分有效期
        expired_points = loyalty.check_points_expiry()
        if expired_points > 0:
            messages.warning(
                request, f"您的 {expired_points} 積分已過期，請及時使用積分"
            )

        # 獲取積分摘要信息
        points_summary = loyalty.get_points_summary()

        # 獲取會員基本信息
        membership_info = loyalty.get_membership_info()

        # 獲取近期活動
        recent_activities = CustomerActivity.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:20]

        # 獲取可兌換獎勵
        available_rewards = loyalty.get_available_rewards()

        context = {
            "loyalty": loyalty,
            "points_summary": points_summary,
            "membership_info": membership_info,
            "recent_activities": recent_activities,
            "available_rewards": available_rewards,
            "profile": getattr(request.user, "profile", None),
        }

        return render(request, "socialuser/loyalty_dashboard.html", context)

    except Exception as e:
        messages.error(request, f"加載儀表板失敗: {str(e)}")
        return redirect("profile")


@login_required
@require_http_methods(["POST"])
def redeem_reward(request):
    """兌換獎勵"""
    try:
        data = json.loads(request.body)
        reward_id = data.get("reward_id")

        if not reward_id:
            return JsonResponse({"success": False, "message": "請選擇要兌換的獎勵"})

        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)

        # 先獲取獎勵信息，然後再兌換
        available_rewards = loyalty.get_available_rewards()
        reward_info = next((r for r in available_rewards if r["id"] == reward_id), None)

        if not reward_info:
            return JsonResponse({"success": False, "message": "獎勵不存在或不可兌換"})

        success, message = loyalty.redeem_reward(reward_id)

        if success:
            # redeem_reward() 內部已自動記錄 CustomerActivity，此處不再重複記錄
            return JsonResponse(
                {"success": True, "message": message, "points": loyalty.points}
            )
        else:
            return JsonResponse({"success": False, "message": message})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"兌換失敗: {str(e)}"})


@login_required
def activity_history(request):
    """活動歷史記錄"""
    try:
        activities = CustomerActivity.objects.filter(user=request.user).order_by(
            "-created_at"
        )[
            :50
        ]  # 只顯示最近50條

        # 分組活動（按日期）
        grouped_activities = {}
        for activity in activities:
            date_key = activity.created_at.date().isoformat()
            if date_key not in grouped_activities:
                grouped_activities[date_key] = []
            grouped_activities[date_key].append(activity)

        context = {
            "grouped_activities": grouped_activities,
            "total_activities": activities.count(),
        }

        return render(request, "socialuser/activity_history.html", context)

    except Exception as e:
        messages.error(request, f"加載活動歷史失敗: {str(e)}")
        return redirect("loyalty_dashboard")


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
                "type": "消費積分",
                "description": "每消費 $10 可獲得 1 積分",
                "icon": "fa-shopping-cart",
                "color": "primary",
            },
            {
                "type": "推薦積分",
                "description": "成功推薦好友註冊可獲得 50 積分",
                "icon": "fa-user-plus",
                "color": "success",
            },
            {
                "type": "活動積分",
                "description": "參與店內活動可獲得額外積分",
                "icon": "fa-gift",
                "color": "warning",
            },
        ]

        # 獲取積分有效期信息
        expiry_info = None
        if points_summary["days_until_expiry"] is not None:
            if points_summary["days_until_expiry"] <= 7:
                expiry_status = "danger"
                expiry_message = (
                    f"積分將在 {points_summary['days_until_expiry']} 天後過期"
                )
            elif points_summary["days_until_expiry"] <= 30:
                expiry_status = "warning"
                expiry_message = (
                    f"積分將在 {points_summary['days_until_expiry']} 天後過期"
                )
            else:
                expiry_status = "success"
                expiry_message = (
                    f"積分有效期剩餘 {points_summary['days_until_expiry']} 天"
                )

            expiry_info = {
                "status": expiry_status,
                "message": expiry_message,
                "expiry_date": points_summary["points_expiry_date"],
                "days_remaining": points_summary["days_until_expiry"],
            }

        context = {
            "loyalty": loyalty,
            "points_summary": points_summary,
            "point_rules": point_rules,
            "expiry_info": expiry_info,
        }

        return render(request, "socialuser/points_summary.html", context)

    except Exception as e:
        messages.error(request, f"加載積分信息失敗: {str(e)}")
        return redirect("loyalty_dashboard")


@login_required
def api_loyalty_status(request):
    """API: 獲取忠誠度狀態（用於AJAX更新）"""
    try:
        loyalty, _ = CustomerLoyalty.objects.get_or_create(user=request.user)

        # 獲取積分摘要信息
        points_summary = loyalty.get_points_summary()

        return JsonResponse(
            {
                "success": True,
                "points": loyalty.points,
                "total_spent": float(loyalty.total_spent),
                "total_orders": loyalty.total_orders,
                "available_rewards": loyalty.get_available_rewards(),
                "points_summary": points_summary,
                "membership_info": loyalty.get_membership_info(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
def api_recent_activities(request):
    """API: 獲取近期活動"""
    try:
        activities = CustomerActivity.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:10]

        activities_data = []
        for activity in activities:
            activities_data.append(
                {
                    "type": activity.activity_type,
                    "type_display": activity.get_activity_type_display(),
                    "points_change": activity.points_change,
                    "description": activity.description,
                    "created_at": activity.created_at.isoformat(),
                    "time_ago": _time_ago(activity.created_at),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "activities": activities_data,
                "count": len(activities_data),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


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


@login_required
@require_http_methods(["POST"])
def social_disconnect(request, provider):
    """解除綁定社交帳號"""
    try:
        # 檢查用戶是否有密碼（如果沒有密碼，不能解除最後一個社交帳號）
        has_password = request.user.has_usable_password()
        social_accounts = SocialAccount.objects.filter(user=request.user)

        # 如果用戶沒有密碼且這是最後一個社交帳號，不允許解除綁定
        if not has_password and social_accounts.count() <= 1:
            messages.error(
                request,
                "您沒有設定密碼，無法解除最後一個社交帳號綁定。"
                "請先設定密碼後再操作。",
            )
            return redirect("socialuser:profile")

        # 查找並刪除指定的社交帳號
        account = SocialAccount.objects.filter(
            user=request.user, provider=provider
        ).first()

        if not account:
            messages.error(request, f"找不到已綁定的 {provider} 帳號")
            return redirect("socialuser:profile")

        # 記錄提供者名稱用於提示訊息
        provider_names = {
            "google": "Google",
            "facebook": "Facebook",
        }
        provider_name = provider_names.get(provider, provider)

        account.delete()
        messages.success(request, f"已成功解除 {provider_name} 帳號綁定")

    except Exception as e:
        messages.error(request, f"解除綁定失敗: {str(e)}")

    return redirect("socialuser:profile")
