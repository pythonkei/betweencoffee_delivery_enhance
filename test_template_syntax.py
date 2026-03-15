#!/usr/bin/env python3
"""
測試支付確認頁面模板語法修復
"""

import os
import sys
import django
from django.template import Template, TemplateSyntaxError

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django 設置失敗: {e}")
    sys.exit(1)

def test_template_syntax():
    """測試模板語法是否正確"""
    template_path = 'eshop/templates/eshop/order_payment_confirmation.html'
    
    print("🔍 測試支付確認頁面模板語法...")
    print(f"模板路徑: {template_path}")
    print("-" * 50)
    
    try:
        # 讀取模板文件
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        print("✅ 模板文件讀取成功")
        
        # 檢查關鍵語法
        issues = []
        
        # 檢查 {% with %} 和 {% endwith %} 配對
        with_count = template_content.count('{% with')
        endwith_count = template_content.count('{% endwith %}')
        
        if with_count != endwith_count:
            issues.append(f"❌ {{% with %}} 和 {{% endwith %}} 數量不匹配: with={with_count}, endwith={endwith_count}")
        else:
            print(f"✅ {{% with %}} 和 {{% endwith %}} 配對正確: {with_count} 對")
        
        # 檢查 {% block %} 和 {% endblock %} 配對
        block_count = template_content.count('{% block')
        endblock_count = template_content.count('{% endblock')
        
        if block_count != endblock_count:
            issues.append(f"❌ {{% block %}} 和 {{% endblock %}} 數量不匹配: block={block_count}, endblock={endblock_count}")
        else:
            print(f"✅ {{% block %}} 和 {{% endblock %}} 配對正確: {block_count} 對")
        
        # 檢查 {% if %} 和 {% endif %} 配對
        if_count = template_content.count('{% if')
        endif_count = template_content.count('{% endif')
        
        if if_count != endif_count:
            issues.append(f"❌ {{% if %}} 和 {{% endif %}} 數量不匹配: if={if_count}, endif={endif_count}")
        else:
            print(f"✅ {{% if %}} 和 {{% endif %}} 配對正確: {if_count} 對")
        
        # 檢查 {% for %} 和 {% endfor %} 配對
        for_count = template_content.count('{% for')
        endfor_count = template_content.count('{% endfor')
        
        if for_count != endfor_count:
            issues.append(f"❌ {{% for %}} 和 {{% endfor %}} 數量不匹配: for={for_count}, endfor={endfor_count}")
        else:
            print(f"✅ {{% for %}} 和 {{% endfor %}} 配對正確: {for_count} 對")
        
        # 嘗試編譯模板
        try:
            template = Template(template_content)
            print("✅ 模板編譯成功")
        except TemplateSyntaxError as e:
            issues.append(f"❌ 模板編譯錯誤: {e}")
        
        # 輸出結果
        print("-" * 50)
        if issues:
            print("❌ 發現模板語法問題:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ 模板語法檢查通過！")
            return True
            
    except FileNotFoundError:
        print(f"❌ 找不到模板文件: {template_path}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def check_specific_fix():
    """檢查特定的修復問題"""
    print("\n🔍 檢查特定修復...")
    print("-" * 50)
    
    template_path = 'eshop/templates/eshop/order_payment_confirmation.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 檢查第3行和第7行
        if len(lines) >= 7:
            line3 = lines[2].strip()  # 第3行（索引2）
            line7 = lines[6].strip()  # 第7行（索引6）
            
            print(f"第3行: {line3}")
            print(f"第7行: {line7}")
            
            if '{% with order_type=order.get_order_type_summary %}' in line3:
                print("✅ 第3行包含正確的 {% with %} 標籤")
            else:
                print("❌ 第3行沒有找到正確的 {% with %} 標籤")
            
            if '{% endwith %}' in line7:
                print("✅ 第7行包含正確的 {% endwith %} 標籤")
            else:
                print("❌ 第7行沒有找到正確的 {% endwith %} 標籤")
                
            # 檢查是否修復了原始問題
            if '{% with order_type=order.get_order_type_summary %}' in line3 and '{% endwith %}' in line7:
                print("\n✅ 特定修復已應用：{% with %} 標籤已正確關閉")
                return True
            else:
                print("\n❌ 特定修復未正確應用")
                return False
        else:
            print("❌ 模板文件行數不足")
            return False
            
    except Exception as e:
        print(f"❌ 檢查特定修復時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("=" * 60)
    print("支付確認頁面模板語法修復測試")
    print("=" * 60)
    
    # 測試模板語法
    syntax_ok = test_template_syntax()
    
    # 檢查特定修復
    fix_ok = check_specific_fix()
    
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    if syntax_ok and fix_ok:
        print("🎉 所有測試通過！")
        print("\n✅ 模板語法錯誤已修復")
        print("✅ {% with %} 標籤已正確關閉")
        print("✅ 支付確認頁面應該能正常顯示")
        print("\n📋 後續步驟:")
        print("1. 重啟 Django 開發服務器")
        print("2. 測試支付寶支付完整流程")
        print("3. 測試 PayPal 支付完整流程")
        print("4. 監控日誌確認無錯誤")
        return 0
    else:
        print("❌ 測試失敗，請檢查模板文件")
        return 1

if __name__ == '__main__':
    sys.exit(main())