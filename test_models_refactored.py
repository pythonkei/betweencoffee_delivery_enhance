#!/usr/bin/env python3
"""
模型遷移版本測試腳本
"""

import os
import sys
import logging
import json

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_refactored_methods():
    """測試遷移後的方法"""
    logger.info("🔍 測試模型遷移版本...")
    
    try:
        # 導入遷移版本的模型
        from eshop.models_refactored import (
            OrderModel,
            get_product_image_url,
            get_product_image_url_compatible
        )
        
        logger.info("✅ 模塊導入成功")
        
        # 測試1: 錯誤處理框架基礎測試
        logger.info("\n1. 測試錯誤處理框架基礎...")
        
        from eshop.error_handling import handle_error, handle_success
        
        # 測試錯誤處理
        try:
            raise ValueError("測試錯誤")
        except Exception as e:
            error_result = handle_error(
                error=e,
                context='test_error_handling',
                operation='test_error_handling',
                data={'test': 'data'}
            )
            
            if error_result.get('success') is False and 'error_id' in error_result:
                logger.info("✅ 錯誤處理測試通過")
                logger.info(f"   錯誤ID: {error_result.get('error_id', 'N/A')}")
            else:
                logger.error("❌ 錯誤處理測試失敗")
                return False
        
        # 測試成功處理
        success_result = handle_success(
            operation='test_success',
            data={'test': 'data'},
            message='測試成功'
        )
        
        if success_result.get('success') and 'message' in success_result:
            logger.info("✅ 成功處理測試通過")
            logger.info(f"   消息: {success_result.get('message', 'N/A')}")
        else:
            logger.error("❌ 成功處理測試失敗")
            return False
        
        # 測試2: 圖片URL獲取函數
        logger.info("\n2. 測試圖片URL獲取函數...")
        
        # 測試帶有圖片的商品
        test_item_with_image = {
            'id': 1,
            'type': 'coffee',
            'name': '測試咖啡',
            'image': '/static/images/test-coffee.png'
        }
        
        image_result = get_product_image_url(test_item_with_image)
        
        if image_result.get('success'):
            data = image_result.get('data', {})
            logger.info("✅ 圖片URL獲取測試通過（帶圖片）")
            logger.info(f"   圖片URL: {data.get('image_url', 'N/A')}")
            logger.info(f"   來源: {data.get('source', 'N/A')}")
        else:
            logger.error("❌ 圖片URL獲取測試失敗（帶圖片）")
            return False
        
        # 測試兼容性包裝器
        compatible_url = get_product_image_url_compatible(test_item_with_image)
        if compatible_url:
            logger.info("✅ 兼容性包裝器測試通過")
            logger.info(f"   兼容性URL: {compatible_url}")
        else:
            logger.error("❌ 兼容性包裝器測試失敗")
            return False
        
        # 測試3: 創建測試訂單對象
        logger.info("\n3. 測試訂單對象方法...")
        
        # 創建一個測試訂單對象（不保存到數據庫）
        test_order = OrderModel()
        test_order.id = 999  # 測試ID
        test_order.payment_status = 'paid'
        test_order.status = 'waiting'
        
        # 設置測試商品數據
        test_items = [
            {
                'id': 1,
                'type': 'coffee',
                'name': '測試咖啡',
                'price': 35.0,
                'quantity': 2,
                'cup_level': 'Medium',
                'milk_level': 'Light'
            },
            {
                'id': 2,
                'type': 'bean',
                'name': '測試咖啡豆',
                'price': 120.0,
                'quantity': 1,
                'weight': '200g',
                'grinding_level': 'Medium'
            }
        ]
        
        test_order.items = json.dumps(test_items)
        
        # 測試 get_items 方法
        logger.info("   測試 get_items 方法...")
        items_result = test_order.get_items()
        
        if items_result.get('success'):
            data = items_result.get('data', {})
            logger.info("✅ get_items 方法測試通過")
            logger.info(f"   商品數量: {data.get('count', 0)}")
            logger.info(f"   有咖啡: {data.get('has_coffee', False)}")
            logger.info(f"   有咖啡豆: {data.get('has_beans', False)}")
            
            # 測試兼容性包裝器
            compatible_items = test_order.get_items_compatible()
            if isinstance(compatible_items, list):
                logger.info("✅ 兼容性包裝器測試通過")
                logger.info(f"   兼容性商品數量: {len(compatible_items)}")
            else:
                logger.error("❌ 兼容性包裝器測試失敗")
                return False
        else:
            logger.error("❌ get_items 方法測試失敗")
            return False
        
        # 測試 get_items_with_chinese_options 方法
        logger.info("   測試 get_items_with_chinese_options 方法...")
        chinese_result = test_order.get_items_with_chinese_options()
        
        if chinese_result.get('success'):
            data = chinese_result.get('data', {})
            logger.info("✅ get_items_with_chinese_options 方法測試通過")
            logger.info(f"   帶中文選項商品數量: {data.get('count', 0)}")
            logger.info(f"   有中文選項: {data.get('has_chinese_options', False)}")
            
            # 測試兼容性包裝器
            compatible_chinese_items = test_order.get_items_with_chinese_options_compatible()
            if isinstance(compatible_chinese_items, list):
                logger.info("✅ 中文選項兼容性包裝器測試通過")
                logger.info(f"   兼容性中文商品數量: {len(compatible_chinese_items)}")
            else:
                logger.error("❌ 中文選項兼容性包裝器測試失敗")
                return False
        else:
            logger.error("❌ get_items_with_chinese_options 方法測試失敗")
            return False
        
        # 測試 translate_option 靜態方法
        logger.info("   測試 translate_option 靜態方法...")
        cup_translation = OrderModel.translate_option('cup_level', 'Medium')
        milk_translation = OrderModel.translate_option('milk_level', 'Light')
        grinding_translation = OrderModel.translate_option('grinding_level', 'Medium')
        
        if cup_translation == '中' and milk_translation == '少' and grinding_translation == '中':
            logger.info("✅ translate_option 方法測試通過")
            logger.info(f"   杯型翻譯: {cup_translation}")
            logger.info(f"   牛奶翻譯: {milk_translation}")
            logger.info(f"   研磨翻譯: {grinding_translation}")
        else:
            logger.error("❌ translate_option 方法測試失敗")
            return False
        
        # 測試 translate_weight 靜態方法
        logger.info("   測試 translate_weight 靜態方法...")
        weight_translation_200g = OrderModel.translate_weight('200g')
        weight_translation_500g = OrderModel.translate_weight('500g')
        
        if weight_translation_200g == '200克' and weight_translation_500g == '500克':
            logger.info("✅ translate_weight 方法測試通過")
            logger.info(f"   200g翻譯: {weight_translation_200g}")
            logger.info(f"   500g翻譯: {weight_translation_500g}")
        else:
            logger.error("❌ translate_weight 方法測試失敗")
            return False
        
        # 測試4: 響應格式一致性
        logger.info("\n4. 測試響應格式一致性...")
        
        # 檢查所有方法的響應格式
        test_methods = [
            ('get_items', items_result),
            ('get_items_with_chinese_options', chinese_result),
            ('get_product_image_url', image_result)
        ]
        
        for method_name, result in test_methods:
            required_keys = ['success', 'message', 'details', 'timestamp']
            if result.get('success'):
                required_keys.append('data')
            
            missing_keys = []
            for key in required_keys:
                if key not in result:
                    missing_keys.append(key)
            
            if missing_keys:
                logger.error(f"❌ {method_name} 響應格式不一致，缺少鍵: {missing_keys}")
                return False
        
        logger.info("✅ 響應格式一致性測試通過")
        logger.info("   所有方法返回統一的響應格式")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型遷移測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函數"""
    logger.info("🚀 開始模型遷移版本測試")
    logger.info("=" * 60)
    
    try:
        # 測試遷移版本
        test_result = test_refactored_methods()
        
        # 輸出結果
        logger.info("=" * 60)
        logger.info("📋 測試結果")
        logger.info("=" * 60)
        
        logger.info(f"模型遷移版本測試: {'✅ 通過' if test_result else '❌ 失敗'}")
        
        if test_result:
            logger.info("🎉 遷移版本測試通過！")
            logger.info("💡 建議:")
            logger.info("   1. 可以在開發環境中測試實際數據庫操作")
            logger.info("   2. 可以將關鍵方法逐步遷移到生產環境")
            logger.info("   3. 使用兼容性包裝器確保現有代碼正常工作")
        else:
            logger.warning("⚠️ 遷移版本測試失敗，需要進一步檢查。")
        
        logger.info("=" * 60)
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)