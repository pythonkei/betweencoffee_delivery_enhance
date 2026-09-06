# Phase 3E Step 2: 測試覆蓋缺口報告

> 生成時間: 2026-07-31 19:49
> 純分析報告，不修改任何程式碼

```

📄 eshop/models/order.py (50 定義)
   覆蓋率: 30/50 (60%)
   ❌ 未覆蓋 (20):
      - method OrderModel.__str__
      - method OrderModel.formatted_pickup_time
      - method OrderModel.should_display_pickup_time
      - method OrderModel._get_order_type_display_name
      - method OrderModel.get_payment_display_info
      - method OrderModel.qr_code_data_url
      - method OrderModel.order_summary_info
      - method OrderModel._add_chinese_options
      - method OrderModel.get_display_time
      - method OrderModel.calculate_times_based_on_pickup_choice
      - method OrderModel.get_total_preparation_minutes
      - method OrderModel.should_be_in_queue_by_now
      - method OrderModel.get_remaining_minutes
      - method OrderModel.generate_order_number
      - method OrderModel.generate_unique_pickup_code
      ... 還有 5 個

📄 eshop/models/queue_models.py (7 定義)
   覆蓋率: 3/7 (43%)
   ❌ 未覆蓋 (4):
      - class CoffeePreparationTime
      - method CoffeeQueue.__str__
      - method Barista.__str__
      - method CoffeePreparationTime.__str__

📄 eshop/models/base.py (2 定義)
   覆蓋率: 1/2 (50%)
   ❌ 未覆蓋 (1):
      - def get_image_url()

📄 eshop/models/shop_items.py (9 定義)
   覆蓋率: 7/9 (78%)
   ❌ 未覆蓋 (2):
      - method CoffeeItem.__str__
      - method BeanItem.__str__

📄 eshop/order_status/status_changer.py (9 定義)
   覆蓋率: 9/9 (100%)

📄 eshop/order_status/payment_handler.py (10 定義)
   覆蓋率: 3/10 (30%)
   ❌ 未覆蓋 (7):
      - class PaymentHandler
      - method PaymentHandler.clear_user_cart_and_session
      - method PaymentHandler.confirm_offline_payment
      - method PaymentHandler.confirm_fps_payment
      - method PaymentHandler.confirm_cash_payment
      - method PaymentHandler.process_payment_and_update_status
      - method PaymentHandler._trigger_payment_success_events

📄 eshop/order_status/order_type_analyzer.py (2 定義)
   覆蓋率: 1/2 (50%)
   ❌ 未覆蓋 (1):
      - class OrderTypeAnalyzer

📄 eshop/order_status/status_display.py (10 定義)
   覆蓋率: 2/10 (20%)
   ❌ 未覆蓋 (8):
      - class StatusDisplay
      - method StatusDisplay._get_beans_only_status
      - method StatusDisplay._get_coffee_order_status
      - method StatusDisplay._get_status_message
      - method StatusDisplay._get_queue_display_text
      - method StatusDisplay._get_queue_info
      - method StatusDisplay._calculate_progress
      - method StatusDisplay._get_remaining_minutes

📄 eshop/queue_manager_refactored.py (25 定義)
   覆蓋率: 14/25 (56%)
   ❌ 未覆蓋 (11):
      - def force_sync_queue_and_orders()
      - def repair_queue_data()
      - def get_hong_kong_time_now()
      - def sync_ready_s_timing()
      - method CoffeeQueueManager.add__to_queue
      - method CoffeeQueueManager.recalculate_all__times
      - method CoffeeQueueManager.sync__queue_status
      - method CoffeeQueueManager.add__to_queue_with_smart_allocation
      - method CoffeeQueueManager.start_preparation_with_smart_assignment
      - method CoffeeQueueManager.get_smart_recommendations
      - method CoffeeQueueManager.get_barista_workload_overview

📄 eshop/serializers.py (10 定義)
   覆蓋率: 4/10 (40%)
   ❌ 未覆蓋 (6):
      - class OrderDataSerializer
      - class ApiResponseFormatter
      - method OrderDataSerializer.serialize_order
      - method OrderDataSerializer.get_queue_info_for_order
      - method OrderDataSerializer.serialize_queue_list
      - method ApiResponseFormatter.paginated

📄 eshop/whatsapp_notifier.py (2 定義)
   覆蓋率: 2/2 (100%)

📄 eshop/audit_logger.py (3 定義)
   覆蓋率: 0/3 (0%)
   ❌ 未覆蓋 (3):
      - def _get_ip()
      - def _get_staff_name()
      - def log_audit()
```