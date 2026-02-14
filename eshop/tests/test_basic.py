"""
基础功能测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicTestCase(TestCase):
    """基础测试用例"""
    
    def test_environment(self):
        """测试环境设置"""
        self.assertTrue(True)
        print("✅ 环境测试通过")
    
    def test_models_import(self):
        """测试模型导入"""
        try:
            from eshop.models import OrderModel, CoffeeItem, BeanItem
            self.assertIsNotNone(OrderModel)
            self.assertIsNotNone(CoffeeItem)
            self.assertIsNotNone(BeanItem)
            print("✅ 模型导入测试通过")
        except ImportError as e:
            self.fail(f"模型导入失败: {e}")
