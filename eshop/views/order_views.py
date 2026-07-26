# eshop/views/order_views.py
import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from cart.cart import Cart

# ✅ 修復：使用絕對導入，避免相對導入問題
from eshop.models import BeanItem, CoffeeItem, CoffeeQueue, OrderModel
from eshop.order_status_manager import OrderStatusManager
from eshop.payment_utils import get_payment_tools
from eshop.view_utils import (
    find_existing_pending_order,
    handle_order_error,
    handle_payment_error,
    handle_validation_error,
    validate_and_format_phone,
)

# 设置日志
logger = logging.getLogger(__name__)

# 忠誠度系統導入
try:
    from socialuser.models_enhanced import CustomerLoyalty

    LOYALTY_SYSTEM_AVAILABLE = True
except ImportError:
    LOYALTY_SYSTEM_AVAILABLE = False
    logger.warning("忠誠度系統模組不可用，積分功能將被禁用")


# ==================== 優惠券和折扣處理函數 ====================


def apply_coupon_discounts(
    request, original_total_price, items, selected_reward_id=None
):
    """
    應用折扣到訂單（積分獎勵由用戶選擇）
    返回處理後的訂單數據

    參數:
        selected_reward_id: 用戶選擇的獎勵ID（如 'voucher_5', 'voucher_8', 'voucher_30'）
                           如果為 None，則不套用任何積分獎勵
    """
    final_total_price = original_total_price

    # 會員折扣已移除，所有用戶看到相同價格
    loyalty_discount_rate = Decimal("1.00")  # 無折扣
    loyalty_discount_amount = Decimal("0.00")

    # 處理積分獎勵（如果用戶已登入且選擇了獎勵）
    applied_reward_id = None
    applied_reward_name = None
    reward_discount_amount = Decimal("0.00")

    if request.user.is_authenticated and selected_reward_id:
        try:
            from socialuser.models_enhanced import RedeemedReward

            # 套用用戶選擇的獎勵
            success, discount, reward_name = RedeemedReward.apply_reward_at_checkout(
                request.user, selected_reward_id
            )
            if success and discount > 0:
                reward_discount_amount = discount
                applied_reward_id = selected_reward_id
                applied_reward_name = reward_name
                final_total_price = max(Decimal("0.00"), final_total_price - discount)
                logger.info(f"用戶選擇套用獎勵 {reward_name}，折扣: ${discount}")
        except Exception as e:
            logger.error(f"套用積分獎勵失敗: {str(e)}")

    return {
        "original_total_price": original_total_price,
        "final_total_price": final_total_price,
        "applied_coupon_code": None,
        "coupon_discount": Decimal("0.00"),
        "loyalty_discount_rate": loyalty_discount_rate,
        "loyalty_discount_amount": loyalty_discount_amount,
        "applied_reward_id": applied_reward_id,
        "applied_reward_name": applied_reward_name,
        "reward_discount_amount": reward_discount_amount,
        "total_discount": loyalty_discount_amount + reward_discount_amount,
    }


# ==================== 訂單確認視圖 ====================


@method_decorator(login_required, name="dispatch")
class OrderConfirm(View):
    """訂單確認與付款頁面 - 修改後版本使用統一支付工具"""

    template_name = "eshop/order_confirm.html"

    def get(self, request, *args, **kwargs):
        try:
            # ✅ 修正：從購物車 session 同步 pending_order
            from django.conf import settings

            cart_session = request.session.get(settings.CART_SESSION_ID, {})
            pending_order = request.session.get("pending_order")

            # 如果購物車有商品，但 pending_order 不存在或內容不一致，自動重建
            if cart_session:
                pending_items = pending_order.get("items", {}) if pending_order else {}
                cart_keys = set(cart_session.keys())
                pending_keys = set(pending_items.keys())
                if cart_keys != pending_keys:
                    logger.info(
                        f"購物車內容已變更，自動同步 pending_order（購物車:{len(cart_session)}項, pending:{len(pending_items)}項）"
                    )
                    request.session["pending_order"] = {
                        "items": cart_session,
                        "total_price": str(
                            sum(
                                float(d.get("price", 0)) * int(d.get("quantity", 1))
                                for d in cart_session.values()
                            )
                        ),
                        "cart_item_count": len(cart_session),
                    }
                    request.session.modified = True

            # 优先检查购物车数据
            cart_data = request.session.get("pending_order")
            quick_order_data = request.session.get("quick_order_data")

            # ✅ 修正：普通訂單固定為5分鐘（隱藏）
            _ = "5"

            if cart_data and quick_order_data:
                logger.info(
                    "检测到购物车数据和快速订单数据同时存在，优先使用购物车数据"
                )
                if "quick_order_data" in request.session:
                    del request.session["quick_order_data"]
                    request.session.modified = True

            if cart_data:
                items = []
                total_price = 0

                for item_key, item_data in cart_data.get("items", {}).items():
                    parts = item_key.split("_")
                    if len(parts) < 2:
                        continue

                    item_type = parts[0]
                    item_id = parts[1]

                    try:
                        if item_type == "coffee":
                            item = CoffeeItem.objects.get(id=item_id)
                        elif item_type == "bean":
                            item = BeanItem.objects.get(id=item_id)
                        else:
                            continue

                        if item_type == "bean":
                            weight = item_data.get("weight", "200g")
                            price = float(item.get_price(weight))
                        else:
                            price = float(item.price)

                        item_total = price * item_data.get("quantity", 1)
                        total_price += item_total

                        items.append(
                            {
                                "name": item.name,
                                "quantity": item_data.get("quantity", 1),
                                "total_price": item_total,
                                "type": item_type,
                                "image": item_data.get("image", ""),
                                "cup_level": item_data.get("cup_level"),
                                "milk_level": item_data.get("milk_level"),
                                "strength_level": item_data.get("strength_level"),
                                "grinding_level": item_data.get("grinding_level"),
                                "weight": item_data.get("weight"),
                            }
                        )
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
                        price = float(item_data.get("price", 0))
                        quantity = item_data.get("quantity", 1)
                        item_total = price * quantity
                        total_price += item_total

                        items.append(
                            {
                                "name": item_data.get("name", "商品"),
                                "quantity": quantity,
                                "total_price": item_total,
                                "type": item_type,
                                "image": item_data.get("image", ""),
                                "cup_level": item_data.get("cup_level"),
                                "milk_level": item_data.get("milk_level"),
                                "strength_level": item_data.get("strength_level"),
                                "grinding_level": item_data.get("grinding_level"),
                                "weight": item_data.get("weight"),
                            }
                        )

                # 從購物車 session 讀取聯絡資訊
                customer_name = cart_data.get("customer_name", "")
                customer_phone = cart_data.get("customer_phone", "")
                customer_email = cart_data.get("customer_email", "")

                if not customer_name and request.user.is_authenticated:
                    customer_name = (
                        request.user.get_full_name() or request.user.username or ""
                    )
                if not customer_phone and request.user.is_authenticated:
                    try:
                        customer_phone = getattr(request.user, "phone", "")
                    except BaseException:
                        pass
                if not customer_email and request.user.is_authenticated:
                    customer_email = request.user.email or ""

                initial_data = {
                    "contact_name": customer_name,
                    "phone": customer_phone,
                    "email": customer_email,
                    "pickup_time": "5",
                }
                is_quick_order = False

            elif quick_order_data:
                items = quick_order_data.get("items", [])
                total_price = quick_order_data.get("total_price", 0)

                pickup_time_from_session = quick_order_data.get("pickup_time", "5")

                if (
                    isinstance(pickup_time_from_session, str)
                    and "分鐘" in pickup_time_from_session
                ):
                    import re
                    match = re.search(r"(\d+)", pickup_time_from_session)
                    if match:
                        pickup_time_from_session = match.group(1)

                initial_data = {
                    "contact_name": quick_order_data.get("name", ""),
                    "phone": quick_order_data.get("phone", ""),
                    "email": quick_order_data.get("email", ""),
                    "pickup_time": pickup_time_from_session,
                }
                is_quick_order = True
            else:
                messages.error(request, "没有待处理的订单")
                return redirect("cart:cart_detail")

            # 查詢可用獎勵
            available_rewards = []
            best_reward = None
            if request.user.is_authenticated:
                try:
                    from socialuser.models_enhanced import RedeemedReward

                    available_rewards = (
                        RedeemedReward.get_available_rewards_for_checkout(request.user)
                    )
                    if available_rewards:
                        best_reward = max(
                            available_rewards, key=lambda r: r["discount"]
                        )
                        available_rewards = sorted(
                            available_rewards,
                            key=lambda r: r["reward_id"] == best_reward["reward_id"],
                            reverse=True,
                        )
                except Exception as e:
                    logger.error(f"查詢可用獎勵失敗: {str(e)}")

            discounted_total = total_price
            if best_reward:
                discounted_total = total_price - best_reward["discount"]

            context = {
                "items": items,
                "total_price": total_price,
                "discounted_total": discounted_total,
                "user": request.user,
                "initial_data": initial_data,
                "is_quick_order": is_quick_order,
                "available_rewards": available_rewards,
                "best_reward": best_reward,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"OrderConfirm.get() 發生錯誤: {str(e)}")
            return handle_order_error(
                request, e, redirect_url="cart:cart_detail", error_type="order"
            )

    def post(self, request, *args, **kwargs):
        logger.info("=== OrderConfirm POST 方法开始执行 ===")

        try:
            quick_order_data = request.session.get("quick_order_data")

            if quick_order_data:
                pickup_time_choice = request.POST.get("pickup_time", "5")
                request.session["selected_pickup_time"] = pickup_time_choice
                request.session.modified = True

                items = quick_order_data.get("items", [])
                total_price = quick_order_data.get("total_price", 0)
                is_quick_order = True

                for item in items:
                    if item.get("type") == "coffee" and item.get("id"):
                        try:
                            coffee_item = CoffeeItem.objects.get(id=item["id"])
                            item["image"] = (
                                coffee_item.image.url
                                if coffee_item.image
                                else "/static/images/default-coffee.png"
                            )
                        except CoffeeItem.DoesNotExist:
                            item["image"] = "/static/images/default-coffee.png"
            else:
                pickup_time_choice = "5"
                cart_data = request.session.get("pending_order", {})
                if not cart_data:
                    messages.error(request, "您的購物車是空的")
                    return redirect("cart:cart_detail")

                items = []
                for item_key, item_data in cart_data.get("items", {}).items():
                    parts = item_key.split("_")
                    if len(parts) < 2:
                        continue

                    item_type = parts[0]
                    item_id = parts[1]

                    try:
                        if item_type == "coffee":
                            db_item = CoffeeItem.objects.get(id=item_id)
                        elif item_type == "bean":
                            db_item = BeanItem.objects.get(id=item_id)
                        else:
                            continue

                        image_url = (
                            db_item.image.url
                            if db_item.image
                            else "/static/images/default-product.png"
                        )

                        if item_type == "bean":
                            weight = item_data.get("weight", "200g")
                            price = float(db_item.get_price(weight))
                        else:
                            price = float(db_item.price)

                        items.append(
                            {
                                "type": item_type,
                                "id": int(item_id),
                                "name": db_item.name,
                                "price": price,
                                "quantity": item_data.get("quantity", 1),
                                "cup_level": item_data.get("cup_level"),
                                "milk_level": item_data.get("milk_level"),
                                "strength_level": item_data.get("strength_level"),
                                "grinding_level": item_data.get("grinding_level"),
                                "weight": item_data.get("weight"),
                                "image": image_url,
                            }
                        )
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
                        items.append(
                            {
                                "type": item_type,
                                "id": int(item_id),
                                "name": item_data.get("name", "商品"),
                                "price": float(item_data.get("price", 0)),
                                "quantity": item_data.get("quantity", 1),
                                "cup_level": item_data.get("cup_level"),
                                "milk_level": item_data.get("milk_level"),
                                "strength_level": item_data.get("strength_level"),
                                "grinding_level": item_data.get("grinding_level"),
                                "weight": item_data.get("weight"),
                                "image": item_data.get(
                                    "image", "/static/images/default-product.png"
                                ),
                            }
                        )

                total_price = float(cart_data.get("total_price", 0))
                is_quick_order = False

            if is_quick_order:
                valid_choices = ["5", "10", "15", "20", "30"]
                if pickup_time_choice not in valid_choices:
                    pickup_time_choice = "5"
            else:
                pickup_time_choice = "5"

            phone = request.POST.get("phone", "")
            formatted_phone = validate_and_format_phone(phone)
            if not formatted_phone:
                field_errors = {"phone": "電話號碼格式不正確"}
                return handle_validation_error(request, field_errors)

            selected_reward = request.POST.get("selected_reward", "")
            if selected_reward == "":
                selected_reward = None

            discount_data = apply_coupon_discounts(
                request,
                Decimal(str(total_price)),
                items,
                selected_reward_id=selected_reward if selected_reward else None,
            )

            final_total_price = float(discount_data["final_total_price"])
            original_total_price = float(discount_data["original_total_price"])

            existing_order = find_existing_pending_order(
                request.user, items, final_total_price
            )

            if existing_order:
                existing_order.contact_name = request.POST.get("name", "")
                existing_order.email = request.POST.get("email", "")
                existing_order.phone = formatted_phone
                existing_order.pickup_time_choice = pickup_time_choice
                existing_order.payment_method = request.POST.get(
                    "payment_method", "alipay"
                )
                try:
                    existing_order.calculate_times_based_on_pickup_choice()
                    existing_order.set_payment_timeout(minutes=5)
                    existing_order.save()
                except Exception as e:
                    logger.error(f"更新现有订单失败: {str(e)}")
                    existing_order = None

            if not existing_order:
                try:
                    order = OrderModel.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        total_price=final_total_price,
                        original_total_price=original_total_price,
                        contact_name=request.POST.get("name", ""),
                        email=request.POST.get("email", ""),
                        phone=formatted_phone,
                        items=items,
                        order_type="quick" if is_quick_order else "normal",
                        is_quick_order=is_quick_order,
                        pickup_time_choice=pickup_time_choice,
                        status="pending",
                        payment_method=request.POST.get("payment_method", "alipay"),
                        payment_status="pending",
                        applied_coupon_code=discount_data["applied_coupon_code"],
                        coupon_discount=float(discount_data["coupon_discount"]),
                        loyalty_discount_rate=float(
                            discount_data["loyalty_discount_rate"]
                        ),
                        loyalty_discount_amount=float(
                            discount_data["loyalty_discount_amount"]
                        ),
                        applied_reward_id=discount_data["applied_reward_id"],
                        applied_reward_name=discount_data["applied_reward_name"],
                        reward_discount_amount=float(
                            discount_data["reward_discount_amount"]
                        ),
                    )
                    if (
                        discount_data["applied_reward_id"]
                        and request.user.is_authenticated
                    ):
                        try:
                            from socialuser.models_enhanced import RedeemedReward
                            unused_rewards = RedeemedReward.get_unused_rewards(
                                request.user
                            )
                            for reward in unused_rewards:
                                if (
                                    reward.reward_id
                                    == discount_data["applied_reward_id"]
                                ):
                                    reward.mark_as_used(order_id=order.id)
                        except Exception as e:
                            logger.error(f"標記獎勵為已使用失敗: {str(e)}")

                    order.refresh_from_db()
                    order.calculate_times_based_on_pickup_choice()
                    order.set_payment_timeout(minutes=5)
                except Exception as e:
                    logger.error(f"订单创建失败: {str(e)}")
                    messages.error(request, "创建订单失败，请稍后重试")
                    return redirect("cart:cart_detail")
            else:
                order = existing_order

            if "pending_order" in request.session:
                del request.session["pending_order"]
            if "quick_order_data" in request.session:
                del request.session["quick_order_data"]
            request.session.modified = True

            request.session["last_order_id"] = order.id
            request.session.modified = True

            try:
                cart = Cart(request)
                cart.clear()
                logger.info(f"訂單 #{order.id} 創建成功，購物車已清空")
            except Exception as e:
                logger.warning(f"清空購物車時出錯（不影響訂單）: {e}")

            payment_method = request.POST.get("payment_method", "alipay")
            return self.handle_payment(request, order, payment_method)

        except Exception as e:
            logger.error(f"订单创建失败: {str(e)}")
            return handle_order_error(
                request, e, redirect_url="cart:cart_detail", error_type="order"
            )

    def handle_payment(self, request, order, payment_method):
        """统一处理付款"""
        try:
            logger.info(f"处理支付方式: {payment_method}, 订单: {order.id}")
            payment_tools = get_payment_tools(payment_method)

            if not payment_tools:
                logger.error(f"无效的支付方式: {payment_method}")
                messages.error(request, "请选择有效的付款方式")
                return redirect("eshop:order_confirm")

            if payment_method == "alipay":
                if "create" not in payment_tools:
                    messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                    return redirect(
                        reverse("eshop:order_payment_confirmation")
                        + f"?order_id={order.id}&payment_status=error"
                    )
                try:
                    payment_url = payment_tools["create"](order, request)
                    if payment_url:
                        order.increment_payment_attempts()
                        return redirect(payment_url)
                    else:
                        messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                        return redirect(
                            reverse(
                                "eshop:order_payment_confirmation_with_id",
                                kwargs={"order_id": order.id},
                            )
                            + "?payment_status=error"
                        )
                except Exception as e:
                    logger.error(f"支付宝支付处理异常: {str(e)}")
                    messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                    return redirect(
                        reverse(
                            "eshop:order_payment_confirmation_with_id",
                            kwargs={"order_id": order.id},
                        )
                        + "?payment_status=error"
                    )

            elif payment_method == "paypal":
                try:
                    if "create" not in payment_tools:
                        messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                        return redirect(
                            reverse(
                                "eshop:order_payment_confirmation_with_id",
                                kwargs={"order_id": order.id},
                            )
                            + "?payment_status=error"
                        )
                    paypal_url = payment_tools["create"](order, request)
                    if paypal_url:
                        request.session["pending_paypal_order_id"] = order.id
                        request.session.modified = True
                        return redirect(paypal_url)
                    else:
                        messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                        return redirect(
                            reverse(
                                "eshop:order_payment_confirmation_with_id",
                                kwargs={"order_id": order.id},
                            )
                            + "?payment_status=error"
                        )
                except Exception as e:
                    logger.error(f"PayPal支付处理异常: {str(e)}")
                    messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                    return redirect(
                        reverse(
                            "eshop:order_payment_confirmation_with_id",
                            kwargs={"order_id": order.id},
                        )
                        + "?payment_status=error"
                    )

            elif payment_method == "fps":
                return self.handle_fps_payment(request, order)
            elif payment_method == "cash":
                return self.handle_cash_payment(request, order)
            else:
                logger.error(f"无效的支付方式: {payment_method}")
                messages.error(request, "请选择有效的付款方式")
                return redirect("eshop:order_confirm")

        except Exception as e:
            return handle_payment_error(request, e, order.id)

    def handle_fps_payment(self, request, order):
        try:
            payment_tools = get_payment_tools("fps")
            if not payment_tools or "create_reference" not in payment_tools:
                messages.error(request, "FPS支付系统暂时不可用")
                return redirect("eshop:order_confirm")
            fps_reference = payment_tools["create_reference"](order.id)
            order.fps_reference = fps_reference
            order.save()
            request.session["pending_fps_order_id"] = order.id
            request.session.modified = True
            return redirect("eshop:fps_payment", order_id=order.id)
        except Exception as e:
            logger.error(f"FPS支付處理失敗: {str(e)}")
            messages.error(request, "FPS支付處理失敗，請稍後重試")
            return redirect("eshop:order_confirm")

    def handle_cash_payment(self, request, order):
        try:
            from eshop.order_status_manager import OrderStatusManager
            result = OrderStatusManager.process_order_status_change(
                order_id=order.id,
                new_status="pending",
                staff_name=(
                    request.user.username if hasattr(request, "user") else "system"
                ),
            )
            if not result.get("success"):
                logger.error(
                    f"標記訂單 {order.id} 為 pending 失敗: {result.get('message')}"
                )
            order.payment_status = "pending"
            order.save()
            request.session["pending_cash_order_id"] = order.id
            request.session.modified = True
            return redirect("eshop:cash_payment", order_id=order.id)
        except Exception as e:
            logger.error(f"現金支付處理失敗: {str(e)}")
            messages.error(request, "現金支付處理失敗，請稍後重試")
            return redirect("eshop:order_confirm")


# ==================== 快速訂單相關函式 ====================


@require_POST
def quick_order(request):
    """快速订单"""
    name = request.POST.get("name", "")
    phone = request.POST.get("phone", "")
    email = request.POST.get("email", "")
    pickup_time_raw = request.POST.get("pickup_time", "5")

    try:
        minutes_to_add = int(pickup_time_raw)
        if minutes_to_add not in (5, 10, 15, 20, 30):
            minutes_to_add = 5
    except (ValueError, TypeError):
        minutes_to_add = 5

    pickup_time_choice = str(minutes_to_add)
    pickup_time_display = f"{minutes_to_add}分鐘後"

    from django.conf import settings
    CART_SESSION_ID = settings.CART_SESSION_ID
    if CART_SESSION_ID in request.session:
        del request.session[CART_SESSION_ID]
    if "pending_order" in request.session:
        del request.session["pending_order"]

    try:
        wake_meup_coffee = CoffeeItem.objects.get(id=1)
        quick_order_item = {
            "type": "coffee",
            "id": 1,
            "name": wake_meup_coffee.name,
            "price": float(wake_meup_coffee.price),
            "quantity": 1,
            "cup_level": "Medium",
            "cup_level_cn": "中",
            "milk_level": "Medium",
            "milk_level_cn": "正常",
            "image": (
                wake_meup_coffee.image.url
                if wake_meup_coffee.image
                else "/static/images/default-coffee.png"
            ),
            "total_price": float(wake_meup_coffee.price),
        }
    except CoffeeItem.DoesNotExist:
        quick_order_item = {
            "type": "coffee",
            "id": 1,
            "name": "WakeMeup 醒神配方",
            "price": 38.0,
            "quantity": 1,
            "cup_level": "Medium",
            "cup_level_cn": "中",
            "milk_level": "Medium",
            "milk_level_cn": "正常",
            "image": "/static/images/default-coffee.png",
            "total_price": 38.0,
        }

    request.session["quick_order_data"] = {
        "items": [quick_order_item],
        "total_price": quick_order_item["total_price"],
        "name": name,
        "phone": phone,
        "email": email,
        "pickup_time": pickup_time_display,
        "pickup_time_choice": pickup_time_choice,
        "is_quick_order": True,
        "cup_level": "Medium",
    }
    request.session.modified = True
    return redirect("eshop:order_confirm")


@login_required
def clear_quick_order(request):
    if "quick_order_data" in request.session:
        del request.session["quick_order_data"]
        request.session.modified = True
        messages.info(request, "已清除快速订单数据")
    if "pending_order" in request.session and request.session["pending_order"]:
        return redirect("cart:cart_detail")
    else:
        return redirect("/")


# ==================== 訂單詳情檢視 ====================


def order_detail(request, order_id):
    try:
        return redirect("eshop:order_payment_confirmation", order_id=order_id)
    except Exception as e:
        logger.error(f"订单详情页面重定向错误: {str(e)}")
        return handle_order_error(request, e, redirect_url="/", error_type="general")


@require_GET
def order_status_api(request, order_id):
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        if request.user.is_authenticated and order.user != request.user:
            return JsonResponse(
                {"success": False, "error": "無權查看此訂單"}, status=403
            )
        status_manager = OrderStatusManager(order)
        status_info = status_manager.get_display_status()
        response_data = {
            "success": True,
            "order_id": order.id,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": (
                order.updated_at.isoformat()
                if hasattr(order, "updated_at") and order.updated_at
                else None
            ),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "progress_percentage": status_info["progress_percentage"],
            "progress_display": status_info["progress_display"],
            "is_ready": status_info["is_ready"],
            "queue_info": status_info.get("queue_info"),
            "queue_display": status_info.get("queue_display", ""),
            "queue_message": status_info.get("queue_message", ""),
            "remaining_display": status_info.get("remaining_display", ""),
            "estimated_time": status_info.get("estimated_time", ""),
            "status_message": status_info.get("status_message", ""),
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"訂單狀態API錯誤: {str(e)}")
        from eshop.view_utils import OrderErrorHandler
        return OrderErrorHandler.handle_json_error(str(e), status=500, error_type="api")


# ==================== 訂單支付確認頁面 ====================


def order_payment_confirmation(request, order_id=None):
    if order_id is None:
        order_id = request.GET.get("order_id") or request.session.get("last_order_id")

    if not order_id:
        context = {"payment_status": "error", "error_message": "未找到訂單信息"}
        return render(request, "eshop/order_payment_confirmation.html", context)

    try:
        order = get_object_or_404(OrderModel, id=order_id)

        if order.payment_status == "paid":
            payment_status_for_template = "paid"
        elif order.payment_status == "pending":
            payment_status_for_template = "pending"
        else:
            payment_status_for_template = "unknown"

        status_manager = OrderStatusManager(order)
        status_info = status_manager.get_display_status()
        order_type = order.get_order_type_summary()

        if not order.pickup_code:
            order.save()

        earned_points = 0
        loyalty_info = None

        if (
            payment_status_for_template == "paid"
            and request.user.is_authenticated
            and LOYALTY_SYSTEM_AVAILABLE
        ):
            try:
                earned_points = int(float(order.total_price) / 10)
                loyalty, created = CustomerLoyalty.objects.get_or_create(
                    user=request.user
                )
                loyalty_info = {
                    "earned_points": earned_points,
                    "total_points": loyalty.points,
                    "membership_number": loyalty.membership_number or "未分配",
                }
            except Exception as e:
                logger.error(f"讀取積分信息時發生錯誤: {str(e)}")

        context = {
            "order": order,
            "payment_status": payment_status_for_template,
            "order_type": order_type,
            "status_info": status_info,
            "earned_points": earned_points,
            "loyalty_info": loyalty_info,
        }

        return render(request, "eshop/order_payment_confirmation.html", context)

    except OrderModel.DoesNotExist:
        logger.error(f"訂單 #{order_id} 不存在")
        context = {
            "payment_status": "error",
            "error_message": f"訂單 #{order_id} 不存在或已被處理",
            "order_id": order_id,
        }
        return render(request, "eshop/order_payment_confirmation.html", context)
    except Exception as e:
        logger.error(f"訂單確認頁面錯誤: {e}", exc_info=True)
        try:
            order = OrderModel.objects.get(id=order_id)
            redirect_url = reverse("eshop:order_payment_confirmation", args=[order_id])
        except BaseException:
            redirect_url = "/"
        return handle_order_error(
            request, e, redirect_url=redirect_url, error_type="general"
        )


# ==================== 支付状态检查 ====================


def check_order_status(request, order_id):
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        if request.user.is_authenticated and order.user != request.user:
            return JsonResponse(
                {"success": False, "error": "无权查看此订单"}, status=403
            )
        queue_info = None
        try:
            queue_info = CoffeeQueue.objects.get(order=order)
        except CoffeeQueue.DoesNotExist:
            pass
        needs_retry = (
            order.payment_status == "pending"
            and order.created_at < timezone.now() - timedelta(minutes=5)
        )
        return JsonResponse(
            {
                "success": True,
                "order_id": order.id,
                "status": order.status,
                "payment_status": order.get_payment_status_display(),
                "queue_position": queue_info.position if queue_info else None,
                "estimated_time": (
                    queue_info.estimated_completion_time.isoformat()
                    if queue_info
                    else None
                ),
                "needs_retry": needs_retry,
                "redirect_url": (
                    f"/eshop/continue_payment/{order.id}/" if needs_retry else None
                ),
            }
        )
    except Exception as e:
        logger.error(f"检查订单状态错误: {str(e)}")
        from eshop.view_utils import OrderErrorHandler
        return OrderErrorHandler.handle_json_error(str(e), status=500, error_type="api")


def continue_payment(request, order_id):
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        if order.status != "pending":
            messages.warning(request, f"订单状态为 {order.status}，无需重新支付")
            return redirect("eshop:order_payment_confirmation", order_id=order.id)
        if order.payment_method == "alipay":
            return redirect("eshop:alipay_payment", order_id=order.id)
        elif order.payment_method == "fps":
            return redirect("eshop:fps_payment", order_id=order.id)
        elif order.payment_method == "cash":
            return redirect("eshop:cash_payment", order_id=order.id)
        elif order.payment_method == "paypal":
            try:
                from eshop.paypal_utils import create_paypal_payment
                paypal_url = create_paypal_payment(order, request)
                if paypal_url:
                    request.session["pending_paypal_order_id"] = order.id
                    return redirect(paypal_url)
                else:
                    messages.error(request, "PayPal支付暫時不可用，請稍後再試")
                    return redirect(
                        "eshop:order_payment_confirmation", order_id=order.id
                    )
            except Exception as e:
                logger.error(f"PayPal繼續支付異常: {str(e)}")
                messages.error(request, "PayPal支付暫時不可用，請稍後再試")
                return redirect("eshop:order_payment_confirmation", order_id=order.id)
        else:
            messages.error(request, "未知的支付方式")
            return redirect("eshop:order_payment_confirmation", order_id=order.id)
    except Exception as e:
        logger.error(f"继续支付错误: {str(e)}")
        return handle_order_error(request, e, redirect_url="/", error_type="payment")


# ==================== 其他辅助函数 ====================


def get_order_summary(request):
    try:
        cart = Cart(request)
        total_amount = 0
        item_count = 0
        for item in cart:
            try:
                total_amount += float(item["price"]) * item["quantity"]
                item_count += item["quantity"]
            except (KeyError, ValueError):
                continue
        return JsonResponse(
            {
                "success": True,
                "item_count": item_count,
                "total_amount": total_amount,
                "formatted_total": f"${total_amount:.2f}",
            }
        )
    except Exception as e:
        logger.error(f"获取订单摘要错误: {str(e)}")
        return JsonResponse({"success": False, "message": str(e)})


@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        try:
            product_id = request.POST.get("product_id")
            quantity = int(request.POST.get("quantity", 1))
            product = get_object_or_404(CoffeeItem, id=product_id)
            cart = Cart(request)
            cart.add(
                product=product,
                product_type="coffee",
                quantity=quantity,
                cup_level=request.POST.get("cup_level", "Medium"),
                milk_level=request.POST.get("milk_level", "Medium"),
            )
            cart_data = {"items": cart.cart, "total_price": str(cart.get_total_price())}
            request.session["pending_order"] = cart_data
            request.session.modified = True
            messages.success(request, f"已添加 {product.name} 到购物车")
            return JsonResponse(
                {
                    "success": True,
                    "cart_count": len(cart),
                    "message": "商品已添加到购物车",
                }
            )
        except Exception as e:
            logger.error(f"添加到购物车错误: {str(e)}")
            return JsonResponse(
                {"success": False, "message": f"添加失败: {str(e)}"}, status=500
            )
    return JsonResponse({"success": False, "message": "无效的请求方法"}, status=400)


def remove_from_cart(request):
    if request.method == "POST":
        try:
            product_id = request.POST.get("product_id")
            cart = Cart(request)
            cart.remove(product_id)
            cart_data = {"items": cart.cart, "total_price": str(cart.get_total_price())}
            request.session["pending_order"] = cart_data
            request.session.modified = True
            messages.success(request, "已从购物车移除商品")
            return JsonResponse(
                {
                    "success": True,
                    "cart_count": len(cart),
                    "message": "商品已从购物车移除",
                }
            )
        except Exception as e:
            logger.error(f"从购物车移除错误: {str(e)}")
            return JsonResponse(
                {"success": False, "message": f"移除失败: {str(e)}"}, status=500
            )
    return JsonResponse({"success": False, "message": "无效的请求方法"}, status=400)