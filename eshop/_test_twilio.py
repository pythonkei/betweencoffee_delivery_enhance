import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from twilio.rest import Client

def test_twilio_directly():
    try:
        print("=== Twilio 直接测试 ===")
        print(f"Account SID: {settings.TWILIO_ACCOUNT_SID}")
        print(f"Auth Token: {settings.TWILIO_AUTH_TOKEN[:10]}...")  # 只显示前10位
        print(f"Phone Number: {settings.TWILIO_PHONE_NUMBER}")
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # 测试获取账户信息
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ 账户验证成功: {account.friendly_name}")
        
        # 测试获取号码列表
        numbers = client.incoming_phone_numbers.list()
        print(f"✅ 找到 {len(numbers)} 个号码")
        
        # 检查配置的号码是否存在
        configured_number = settings.TWILIO_PHONE_NUMBER
        number_exists = any(num.phone_number == configured_number for num in numbers)
        
        if number_exists:
            print(f"✅ 号码 {configured_number} 存在")
        else:
            print(f"❌ 号码 {configured_number} 不存在于您的账户中")
            print("可用号码:")
            for num in numbers:
                print(f"  - {num.phone_number}")
                
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    test_twilio_directly()