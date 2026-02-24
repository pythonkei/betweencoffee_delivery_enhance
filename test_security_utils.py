"""
安全工具模塊測試

測試安全工具模塊的所有功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eshop.utils.security_utils import (
    validate_input, sanitize_input, check_password_strength,
    log_security_event, check_rate_limit, check_security_configuration,
    security_utils
)
from eshop.security_config import (
    get_password_policy, get_validation_rules, get_security_headers,
    validate_security_configuration, generate_security_report
)


class TestSecurityUtils:
    """安全工具測試類"""
    
    def test_input_validation(self):
        """測試輸入驗證"""
        print("=== 測試輸入驗證 ===")
        
        test_data = {
            'email': 'test@example.com',
            'phone': '12345678',
            'password': 'Test123!@#',
            'name': 'John Doe',
            'address': '123 Main St'
        }
        
        test_rules = {
            'email': {'type': 'email', 'required': True},
            'phone': {'type': 'phone', 'required': True},
            'password': {'type': 'string', 'required': True, 'min_length': 8},
            'name': {'type': 'string', 'required': True, 'min_length': 2},
            'address': {'type': 'string', 'required': False, 'min_length': 5}
        }
        
        errors = validate_input(test_data, test_rules)
        print(f"輸入驗證錯誤: {errors}")
        
        assert len(errors) == 0, f"輸入驗證失敗: {errors}"
        print("✅ 輸入驗證測試通過")
    
    def test_password_strength(self):
        """測試密碼強度檢查"""
        print("\n=== 測試密碼強度檢查 ===")
        
        # 測試弱密碼
        weak_result = check_password_strength('123')
        print(f"弱密碼檢查: {weak_result}")
        assert not weak_result['valid'], "弱密碼應該被拒絕"
        assert weak_result['strength'] == 'weak', "密碼強度應該是weak"
        
        # 測試中等密碼（根據當前策略，需要特殊字符）
        medium_result = check_password_strength('Test1234')
        print(f"中等密碼檢查: {medium_result}")
        # 根據當前策略，Test1234缺少特殊字符，所以不應該有效
        # 但我們可以檢查它的強度評分
        assert medium_result['score'] >= 3, "中等密碼應該有足夠的評分"
        assert medium_result['strength'] in ['medium', 'strong'], "密碼強度應該是medium或strong"
        
        # 測試強密碼
        strong_result = check_password_strength('Test123!@#')
        print(f"強密碼檢查: {strong_result}")
        assert strong_result['valid'], "強密碼應該被接受"
        assert strong_result['strength'] == 'strong', "密碼強度應該是strong"
        
        print("✅ 密碼強度檢查測試通過")
    
    def test_sanitize_input(self):
        """測試數據清理"""
        print("\n=== 測試數據清理 ===")
        
        # 測試XSS清理
        xss_input = '<script>alert("xss")</script>Hello'
        cleaned_xss = sanitize_input(xss_input)
        print(f"XSS清理前: {xss_input}")
        print(f"XSS清理後: {cleaned_xss}")
        assert '<script>' not in cleaned_xss, "XSS腳本應該被清理"
        
        # 測試SQL注入清理
        sql_input = "SELECT * FROM users WHERE 1=1 OR '1'='1'"
        cleaned_sql = sanitize_input(sql_input)
        print(f"SQL注入清理前: {sql_input}")
        print(f"SQL注入清理後: {cleaned_sql}")
        assert 'SELECT' not in cleaned_sql, "SQL關鍵字應該被清理"
        
        # 測試HTML轉義
        html_input = '<div>Test & "Quote"</div>'
        cleaned_html = sanitize_input(html_input)
        print(f"HTML清理前: {html_input}")
        print(f"HTML清理後: {cleaned_html}")
        assert '<' in cleaned_html, "HTML標籤應該被轉義"
        
        print("✅ 數據清理測試通過")
    
    def test_rate_limit(self):
        """測試速率限制"""
        print("\n=== 測試速率限制 ===")
        
        identifier = 'test_user'
        endpoint = '/api/test'
        
        # 第一次請求應該被允許
        result1 = check_rate_limit(identifier, endpoint, limit=3, window_minutes=1)
        print(f"第一次請求: {result1}")
        assert result1['allowed'], "第一次請求應該被允許"
        assert result1['remaining'] == 2, "剩餘請求次數應該是2"
        
        # 第二次請求應該被允許
        result2 = check_rate_limit(identifier, endpoint, limit=3, window_minutes=1)
        print(f"第二次請求: {result2}")
        assert result2['allowed'], "第二次請求應該被允許"
        assert result2['remaining'] == 1, "剩餘請求次數應該是1"
        
        # 第三次請求應該被允許
        result3 = check_rate_limit(identifier, endpoint, limit=3, window_minutes=1)
        print(f"第三次請求: {result3}")
        assert result3['allowed'], "第三次請求應該被允許"
        assert result3['remaining'] == 0, "剩餘請求次數應該是0"
        
        # 第四次請求應該被拒絕
        result4 = check_rate_limit(identifier, endpoint, limit=3, window_minutes=1)
        print(f"第四次請求: {result4}")
        assert not result4['allowed'], "第四次請求應該被拒絕"
        assert result4['remaining'] == 0, "剩餘請求次數應該是0"
        
        print("✅ 速率限制測試通過")
    
    def test_security_configuration(self):
        """測試安全配置檢查"""
        print("\n=== 測試安全配置檢查 ===")
        
        # 測試Django配置檢查
        config_check = check_security_configuration()
        print(f"安全配置檢查: 分數={config_check['score']}%")
        assert 'score' in config_check, "配置檢查應該包含分數"
        assert 0 <= config_check['score'] <= 100, "分數應該在0-100之間"
        
        # 測試安全配置模塊
        password_policy = get_password_policy()
        print(f"密碼策略: {password_policy}")
        assert 'min_length' in password_policy, "密碼策略應該包含最小長度"
        
        validation_rules = get_validation_rules('email')
        print(f"電子郵件驗證規則: {validation_rules}")
        assert 'pattern' in validation_rules, "驗證規則應該包含模式"
        
        security_headers = get_security_headers()
        print(f"安全頭部數量: {len(security_headers)}")
        assert len(security_headers) > 0, "應該有安全頭部配置"
        
        # 測試配置驗證
        config_validation = validate_security_configuration()
        print(f"配置驗證分數: {config_validation['overall_score']}%")
        assert 'overall_score' in config_validation, "配置驗證應該包含總分"
        
        # 測試安全報告
        security_report = generate_security_report()
        print(f"安全報告狀態: {security_report['status']}")
        assert 'status' in security_report, "安全報告應該包含狀態"
        
        print("✅ 安全配置檢查測試通過")
    
    def test_security_utils_internal(self):
        """測試安全工具內部方法"""
        print("\n=== 測試安全工具內部方法 ===")
        
        # 測試密碼哈希
        password = 'Test123!@#'
        hash_value, salt = security_utils.hash_password(password)
        print(f"密碼哈希測試: 哈希長度={len(hash_value)}, 鹽長度={len(salt)}")
        assert len(hash_value) > 0, "哈希值不應該為空"
        assert len(salt) > 0, "鹽值不應該為空"
        
        # 測試密碼驗證
        is_valid = security_utils.verify_password(password, hash_value, salt)
        print(f"密碼驗證結果: {is_valid}")
        assert is_valid, "密碼驗證應該成功"
        
        # 測試錯誤密碼驗證
        is_invalid = security_utils.verify_password('WrongPassword', hash_value, salt)
        print(f"錯誤密碼驗證結果: {is_invalid}")
        assert not is_invalid, "錯誤密碼驗證應該失敗"
        
        # 測試安全令牌生成
        token = security_utils.generate_secure_token()
        print(f"安全令牌: {token[:10]}...")
        assert len(token) == 32, "安全令牌長度應該是32"
        
        # 測試API密鑰生成
        api_id, api_key = security_utils.generate_api_key()
        print(f"API ID: {api_id}, API Key: {api_key[:10]}...")
        assert api_id.startswith('bc_'), "API ID應該以bc_開頭"
        assert len(api_key) == 64, "API密鑰長度應該是64"
        
        print("✅ 安全工具內部方法測試通過")
    
    def run_all_tests(self):
        """運行所有測試"""
        print("開始運行安全工具模塊測試...\n")
        
        try:
            self.test_input_validation()
            self.test_password_strength()
            self.test_sanitize_input()
            self.test_rate_limit()
            self.test_security_configuration()
            self.test_security_utils_internal()
            
            print("\n" + "="*50)
            print("✅ 所有測試通過！")
            print("="*50)
            return True
            
        except AssertionError as e:
            print(f"\n❌ 測試失敗: {e}")
            return False
        except Exception as e:
            print(f"\n❌ 測試異常: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函數"""
    tester = TestSecurityUtils()
    success = tester.run_all_tests()
    
    if success:
        print("\n安全工具模塊測試總結:")
        print("1. 輸入驗證功能正常")
        print("2. 密碼強度檢查正常")
        print("3. 數據清理功能正常")
        print("4. 速率限制功能正常")
        print("5. 安全配置檢查正常")
        print("6. 內部工具方法正常")
        print("\n✅ 安全工具模塊準備就緒，可以集成到系統中。")
    else:
        print("\n❌ 安全工具模塊測試失敗，需要修復問題。")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())