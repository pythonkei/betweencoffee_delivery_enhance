# eshop/order_status/order_type_analyzer.py
"""
訂單類型分析子模組

拆分自 order_status_manager.py 的 analyze_order_type 方法
負責分析訂單的商品組成類型（咖啡/咖啡豆/混合）
"""

import logging

logger = logging.getLogger(__name__)


class OrderTypeAnalyzer:
    """訂單類型分析器"""

    @staticmethod
    def analyze_order_type(order):
        """
        分析訂單類型 - 確保返回完整字典

        Args:
            order: OrderModel 實例

        Returns:
            dict: {
                'has_coffee': bool,
                'has_beans': bool,
                'is_mixed_order': bool,
                'is_beans_only': bool,
                'is_coffee_only': bool,
            }
        """
        try:
            items = order.get_items()
            has_coffee = False
            has_beans = False

            for item in items:
                item_type = item.get('type', '')
                if item_type == 'coffee':
                    has_coffee = True
                elif item_type == 'bean':
                    has_beans = True

            return {
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': has_coffee and has_beans,
                'is_beans_only': has_beans and not has_coffee,
                'is_coffee_only': has_coffee and not has_beans,
            }
        except Exception as e:
            logger.error(f"分析訂單類型時出錯: {str(e)}")
            return {
                'has_coffee': False,
                'has_beans': False,
                'is_mixed_order': False,
                'is_beans_only': False,
                'is_coffee_only': False,
            }
