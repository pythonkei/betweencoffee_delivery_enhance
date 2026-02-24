"""
安全工具模塊演示

展示如何使用安全工具模塊來增強系統安全性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eshop.utils.security_utils import (
    validate_input, sanitize_input, check_password_strength,
    check_rate_limit, check_security_configuration
)
from eshop.security_config import (
    get_password_policy, get_validation_rules, get_security_headers,
    validate_security_configuration, generate_security_report
)


def demo_input_validation():
    """演示輸入驗證"""
    print("=== 輸入驗證演示 ===")
    
    # 測試數據
    user_data = {
        'email': 'user@example.com',
        'phone': '85212345678',
        'password': 'SecurePass123!',
        'name': 'John Doe',
        'address': '123 Main Street, Hong Kong'
    }
    
    # 驗證規則
    validation_rules = {
        'email': {'type': 'email', 'required': True},
        'phone': {'type': 'phone', 'required': True},
        'password': {'type': 'string', 'required': True, 'min_length': 8},
        'name': {'type': 'string', 'required': True, 'min_length': 2},
        'address': {'type': 'string', 'required': False, 'min_length': 5}
    }
    
    # 執行驗證
    errors = validate_input(user_data, validation_rules)
    
    if errors:
        print("❌ 輸入驗證失敗:")
        for field, field_errors in errors.items():
            print(f"  {field}: {', '.join(field_errors)}")
    else:
        print("✅ 輸入驗證通過")
    
    return len(errors) == 0


def demo_password_strength():
    """演示密碼強度檢查"""
    print("\n=== 密碼強度檢查演示 ===")
    
    passwords = [
        '123',  # 弱密碼
        'password',  # 常見密碼
        'Test1234',  # 中等密碼
        'SecurePass123!',  # 強密碼
        'VeryLongAndComplexPassword123!@#$%',  # 非常強密碼
    ]
    
    for password in passwords:
        result = check_password_strength(password)
        print(f"密碼: {password[:10]}...")
        print(f"  強度: {result['strength']}")
        print(f"  評分: {result['score']}/5")
        print(f"  有效: {result['valid']}")
        if result['issues']:
            print(f"  問題: {', '.join(result['issues'])}")
        print()


def demo_data_sanitization():
    """演示數據清理"""
    print("\n=== 數據清理演示 ===")
    
    # 測試惡意輸入
    malicious_inputs = [
        '<script>alert("XSS攻擊")</script>',
        "SELECT * FROM users WHERE username='admin' OR '1'='1'",
        '<img src="x" onerror="alert(1)">',
        'javascript:alert("XSS")',
        'admin\' OR \'1\'=\'1'
    ]
    
    for input_text in malicious_inputs:
        cleaned = sanitize_input(input_text)
        print(f"原始輸入: {input_text[:30]}...")
        print(f"清理後: {cleaned[:30]}...")
        print()


def demo_rate_limiting():
    """演示速率限制"""
    print("\n=== 速率限制演示 ===")
    
    user_id = 'demo_user_123'
    endpoint = '/api/orders'
    
    print(f"模擬用戶 {user_id} 訪問 {endpoint}:")
    
    for i in range(1, 6):
        result = check_rate_limit(user_id, endpoint, limit=3, window_minutes=1)
        status = "✅ 允許" if result['allowed'] else "❌ 拒絕"
        print(f"  請求 {i}: {status} (剩餘: {result['remaining']})")
    
    print("\n速率限制配置:")
    print("  - 限制: 3次/分鐘")
    print("  - 窗口: 1分鐘")
    print("  - 用途: 防止暴力攻擊")


def demo_security_configuration():
    """演示安全配置"""
    print("\n=== 安全配置演示 ===")
    
    # 獲取密碼策略
    password_policy = get_password_policy()
    print("密碼策略:")
    print(f"  - 最小長度: {password_policy['min_length']}")
    print(f"  - 最大長度: {password_policy['max_length']}")
    print(f"  - 要求大寫: {password_policy['require_uppercase']}")
    print(f"  - 要求小寫: {password_policy['require_lowercase']}")
    print(f"  - 要求數字: {password_policy['require_digits']}")
    print(f"  - 要求特殊字符: {password_policy['require_special']}")
    
    # 獲取驗證規則
    email_rules = get_validation_rules('email')
    print("\n電子郵件驗證規則:")
    print(f"  - 模式: {email_rules['pattern']}")
    print(f"  - 最小長度: {email_rules['min_length']}")
    print(f"  - 最大長度: {email_rules['max_length']}")
    
    # 獲取安全頭部
    security_headers = get_security_headers()
    print(f"\n安全頭部數量: {len(security_headers)}")
    print("主要安全頭部:")
    for header, value in list(security_headers.items())[:3]:
        print(f"  - {header}: {value[:50]}...")
    
    # 檢查安全配置
    config_check = check_security_configuration()
    print(f"\n安全配置檢查分數: {config_check['score']}%")
    
    # 生成安全報告
    security_report = generate_security_report()
    print(f"安全報告狀態: {security_report['status']}")
    print(f"總體評分: {security_report['overall_score']}%")


def demo_integration_example():
    """演示集成示例"""
    print("\n=== 集成示例 ===")
    
    # 示例1: 用戶註冊流程
    print("示例1: 用戶註冊流程")
    print("1. 接收用戶輸入")
    print("2. 驗證輸入數據")
    print("3. 檢查密碼強度")
    print("4. 清理敏感數據")
    print("5. 記錄安全事件")
    print("6. 應用速率限制")
    
    # 示例2: API端點保護
    print("\n示例2: API端點保護")
    print("1. 驗證請求簽名")
    print("2. 檢查速率限制")
    print("3. 驗證輸入參數")
    print("4. 清理輸出數據")
    print("5. 設置安全頭部")
    
    # 示例3: 支付流程安全
    print("\n示例3: 支付流程安全")
    print("1. 驗證支付金額")
    print("2. 檢查支付簽名")
    print("3. 應用交易限制")
    print("4. 記錄安全日誌")
    print("5. 加密敏感數據")


def main():
    """主函數"""
    print("🔒 安全工具模塊演示")
    print("=" * 50)
    
    try:
        # 運行所有演示
        demo_input_validation()
        demo_password_strength()
        demo_data_sanitization()
        demo_rate_limiting()
        demo_security_configuration()
        demo_integration_example()
        
        print("\n" + "=" * 50)
        print("✅ 安全工具模塊演示完成")
        print("\n主要功能總結:")
        print("1. 輸入驗證 - 防止無效或惡意輸入")
        print("2. 密碼安全 - 確保密碼強度")
        print("3. 數據清理 - 防止XSS和SQL注入")
        print("4. 速率限制 - 防止暴力攻擊")
        print("5. 安全配置 - 集中管理安全設置")
        print("6. 安全日誌 - 記錄安全事件")
        print("\n📋 下一步:")
        print("1. 將安全工具集成到現有視圖中")
        print("2. 更新API端點以使用速率限制")
        print("3. 在用戶註冊和登錄中添加密碼強度檢查")
        print("4. 在所有輸入點添加數據清理")
        print("5. 配置安全頭部以增強Web安全")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())