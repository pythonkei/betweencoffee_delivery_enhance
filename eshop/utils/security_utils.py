"""
安全工具模塊 - 統一的安全功能實現

這個模塊提供統一的安全工具函數，包括：
1. 輸入驗證和數據清理
2. 密碼安全檢查
3. 加密解密功能
4. 安全日誌記錄
5. 速率限制檢查
6. 請求驗證

版本: 1.0.0
"""

import re
import hashlib
import hmac
import base64
import logging
import json
import time
import sys
from typing import Any, Dict, List, Union, Tuple

from django.conf import settings
from django.utils import timezone

# 導入統一的錯誤處理
from eshop.error_handling import ErrorHandler

# 創建安全日誌器
security_logger = logging.getLogger('eshop.security')


class SecurityUtils:
    """安全工具類"""
    
    # 安全常量
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    PASSWORD_HASH_ITERATIONS = 100000
    SALT_LENGTH = 32
    TOKEN_EXPIRY_HOURS = 24
    RATE_LIMIT_WINDOW_MINUTES = 60
    
    # 正則表達式模式
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[0-9+\-\s()]{8,20}$',
        'username': r'^[a-zA-Z0-9_]{3,30}$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'ip_address': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
        'credit_card': r'^\d{13,19}$',
        'postal_code': r'^\d{5,10}$',
    }
    
    # XSS防護模式
    XSS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
        r'expression\s*\(',
        r'url\s*\(',
    ]
    
    # SQL注入防護模式
    SQL_INJECTION_PATTERNS = [
        r'(\'|\"|;|--|/\*|\*/|@@|char|nchar|varchar|nvarchar|alter|begin|cast|create|cursor|declare|delete|drop|end|exec|execute|fetch|insert|kill|open|select|sys|sysobjects|syscolumns|table|update)',
        r'(\s+or\s+|\s+and\s+)\s*\d+\s*=\s*\d+',
        r'union\s+select',
        r'insert\s+into',
        r'drop\s+table',
        r'update\s+\w+\s+set',
        r'delete\s+from',
        r'truncate\s+table',
    ]
    
    def __init__(self):
        """初始化安全工具"""
        self.error_handler = ErrorHandler(module_name='security_utils')
        self.rate_limit_cache = {}  # 簡單的速率限制緩存
        
    # ==================== 輸入驗證 ====================
    
    def validate_input(self, data: Dict[str, Any], rules: Dict[str, Dict]) -> Dict[str, List[str]]:
        """
        驗證輸入數據
        
        參數:
            data: 要驗證的數據字典
            rules: 驗證規則字典
            
        返回:
            錯誤字典 {字段名: [錯誤消息]}
        """
        errors = {}
        
        for field, rule in rules.items():
            value = data.get(field)
            
            # 檢查必需字段
            if rule.get('required', False) and (value is None or value == ''):
                errors.setdefault(field, []).append("此字段為必填項")
                continue
            
            # 如果字段為空且不是必需的，跳過其他驗證
            if value is None or value == '':
                continue
            
            # 類型驗證
            if 'type' in rule:
                type_errors = self._validate_type(value, rule['type'])
                if type_errors:
                    errors.setdefault(field, []).extend(type_errors)
                    continue
            
            # 長度驗證
            if 'min_length' in rule and len(str(value)) < rule['min_length']:
                errors.setdefault(field, []).append(
                    f"長度不能少於 {rule['min_length']} 個字符")
            
            if 'max_length' in rule and len(str(value)) > rule['max_length']:
                errors.setdefault(field, []).append(
                    f"長度不能超過 {rule['max_length']} 個字符")
            
            # 模式驗證
            if 'pattern' in rule:
                if not re.match(rule['pattern'], str(value)):
                    errors.setdefault(field, []).append("格式無效")
            
            # 自定義驗證函數
            if 'validator' in rule and callable(rule['validator']):
                try:
                    if not rule['validator'](value):
                        errors.setdefault(field, []).append("驗證失敗")
                except Exception as e:
                    errors.setdefault(field, []).append(f"驗證錯誤: {str(e)}")
            
            # 枚舉值驗證
            if 'enum' in rule and value not in rule['enum']:
                errors.setdefault(field, []).append(
                    f"值必須是以下之一: {', '.join(map(str, rule['enum']))}")
        
        return errors
    
    def _validate_type(self, value: Any, expected_type: str) -> List[str]:
        """驗證數據類型"""
        errors = []
        
        if expected_type == 'string':
            if not isinstance(value, str):
                errors.append("必須是字符串")
        elif expected_type == 'integer':
            try:
                int(value)
            except (ValueError, TypeError):
                errors.append("必須是整數")
        elif expected_type == 'float':
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append("必須是數字")
        elif expected_type == 'boolean':
            if not isinstance(value, bool) and value not in (
                    'true', 'false', '0', '1', 0, 1):
                errors.append("必須是布爾值")
        elif expected_type == 'email':
            if not re.match(self.PATTERNS['email'], str(value)):
                errors.append("必須是有效的電子郵件地址")
        elif expected_type == 'phone':
            if not re.match(self.PATTERNS['phone'], str(value)):
                errors.append("必須是有效的電話號碼")
        elif expected_type == 'url':
            if not re.match(self.PATTERNS['url'], str(value)):
                errors.append("必須是有效的URL")
        
        return errors
    
    # ==================== 數據清理 ====================
    
    def sanitize_input(self, data: Union[str, Dict, List]) -> Union[str, Dict, List]:
        """
        清理輸入數據，防止XSS和SQL注入
        
        參數:
            data: 要清理的數據
            
        返回:
            清理後的數據
        """
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """清理字符串"""
        if not text:
            return text
        
        # 移除XSS模式
        for pattern in self.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 移除SQL注入模式
        for pattern in self.SQL_INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 轉義HTML特殊字符
        text = text.replace('&', '&')
        text = text.replace('<', '<')
        text = text.replace('>', '>')
        text = text.replace('"', '"')
        text = text.replace("'", '&#x27;')
        text = text.replace('/', '&#x2F;')
        
        return text.strip()
    
    def sanitize_html(self, html: str, allowed_tags: List[str] = None) -> str:
        """
        清理HTML，只允許指定的標籤
        
        參數:
            html: HTML字符串
            allowed_tags: 允許的標籤列表
            
        返回:
            清理後的HTML
        """
        if not html:
            return html
        
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'a']
        
        # 簡單的HTML清理
        import html
        cleaned = html.escape(html)
        
        # 恢復允許的標籤
        for tag in allowed_tags:
            cleaned = cleaned.replace(f'<{tag}>', f'<{tag}>')
            cleaned = cleaned.replace(f'</{tag}>', f'</{tag}>')
        
        return cleaned
    
    # ==================== 密碼安全 ====================
    
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """
        檢查密碼強度
        
        參數:
            password: 密碼
            
        返回:
            強度檢查結果
        """
        if not password:
            return {
                'valid': False,
                'score': 0,
                'issues': ['密碼不能為空']
            }
        
        issues = []
        score = 0
        
        # 長度檢查
        if len(password) < self.MIN_PASSWORD_LENGTH:
            issues.append(f"密碼長度不能少於 {self.MIN_PASSWORD_LENGTH} 個字符")
        else:
            score += 1
        
        if len(password) > self.MAX_PASSWORD_LENGTH:
            issues.append(f"密碼長度不能超過 {self.MAX_PASSWORD_LENGTH} 個字符")
        
        # 複雜度檢查
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if has_upper:
            score += 1
        else:
            issues.append("密碼應包含大寫字母")
        
        if has_lower:
            score += 1
        else:
            issues.append("密碼應包含小寫字母")
        
        if has_digit:
            score += 1
        else:
            issues.append("密碼應包含數字")
        
        if has_special:
            score += 1
        else:
            issues.append("密碼應包含特殊字符")
        
        # 常見密碼檢查
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            issues.append("密碼過於常見")
            score = max(0, score - 2)
        
        # 評分
        if score >= 4:
            strength = 'strong'
        elif score >= 3:
            strength = 'medium'
        else:
            strength = 'weak'
        
        return {
            'valid': len(issues) == 0,
            'score': score,
            'strength': strength,
            'issues': issues,
            'suggestions': self._get_password_suggestions(issues)
        }
    
    def _get_password_suggestions(self, issues: List[str]) -> List[str]:
        """獲取密碼改進建議"""
        suggestions = []
        
        if "密碼長度不能少於" in str(issues):
            suggestions.append("增加密碼長度")
        if "密碼應包含大寫字母" in str(issues):
            suggestions.append("添加大寫字母")
        if "密碼應包含小寫字母" in str(issues):
            suggestions.append("添加小寫字母")
        if "密碼應包含數字" in str(issues):
            suggestions.append("添加數字")
        if "密碼應包含特殊字符" in str(issues):
            suggestions.append("添加特殊字符（如 !@#$%）")
        if "密碼過於常見" in str(issues):
            suggestions.append("避免使用常見密碼")
        
        return suggestions
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """
        哈希密碼
        
        參數:
            password: 密碼
            salt: 鹽值（可選）
            
        返回:
            (哈希值, 鹽值)
        """
        if salt is None:
            import secrets
            salt = secrets.token_hex(self.SALT_LENGTH // 2)
        
        # 使用PBKDF2進行哈希
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            self.PASSWORD_HASH_ITERATIONS
        )
        
        hash_value = base64.b64encode(dk).decode('utf-8')
        return hash_value, salt
    
    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """
        驗證密碼
        
        參數:
            password: 密碼
            hash_value: 哈希值
            salt: 鹽值
            
        返回:
            是否匹配
        """
        try:
            new_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(new_hash, hash_value)
        except Exception:
            return False
    
    # ==================== 加密解密 ====================
    
    def encrypt_sensitive_data(self, data: str, key: str = None) -> str:
        """
        加密敏感數據
        
        參數:
            data: 要加密的數據
            key: 加密密鑰（可選）
            
        返回:
            加密後的數據
        """
        try:
            if key is None:
                key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
            
            # 簡單的加密實現（生產環境應使用更強的加密）
            import hashlib
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            
            # 生成密鑰
            key_hash = hashlib.sha256(key.encode()).digest()
            
            # 創建加密器
            cipher = AES.new(key_hash, AES.MODE_CBC)
            
            # 加密數據
            padded_data = pad(data.encode(), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            # 返回IV + 加密數據
            return base64.b64encode(cipher.iv + encrypted).decode()
            
        except ImportError:
            # 如果沒有Crypto庫，使用簡單的base64加密
            self.log_security_event('warning', 'crypto_library_missing', {
                'data_length': len(data)
            })
            return base64.b64encode(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, key: str = None) -> str:
        """
        解密敏感數據
        
        參數:
            encrypted_data: 加密的數據
            key: 解密密鑰（可選）
            
        返回:
            解密後的數據
        """
        try:
            if key is None:
                key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
            
            # 簡單的解密實現
            import hashlib
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            
            # 生成密鑰
            key_hash = hashlib.sha256(key.encode()).digest()
            
            # 解碼數據
            decoded = base64.b64decode(encrypted_data)
            
            # 提取IV和加密數據
            iv = decoded[:16]
            encrypted = decoded[16:]
            
            # 創建解密器
            cipher = AES.new(key_hash, AES.MODE_CBC, iv)
            
            # 解密數據
            decrypted = cipher.decrypt(encrypted)
            unpadded = unpad(decrypted, AES.block_size)
            
            return unpadded.decode()
            
        except ImportError:
            # 如果沒有Crypto庫，使用簡單的base64解密
            return base64.b64decode(encrypted_data).decode()
        except Exception as e:
            self.log_security_event('error', 'decryption_failed', {
                'error': str(e),
                'data_length': len(encrypted_data)
            })
            raise
    
    # ==================== 安全日誌 ====================
    
    def log_security_event(self, level: str, event_type: str, details: Dict[str, Any] = None):
        """
        記錄安全事件
        
        參數:
            level: 日誌級別 (info, warning, error, critical)
            event_type: 事件類型
            details: 事件詳情
        """
        if details is None:
            details = {}
        
        try:
            # 嘗試使用Django timezone
            timestamp = timezone.now().isoformat()
        except Exception:
            # 如果Django不可用，使用Python標準庫
            from datetime import datetime
            timestamp = datetime.now().isoformat()
        
        log_data = {
            'timestamp': timestamp,
            'event_type': event_type,
            'level': level,
            'details': details
        }
        
        log_message = f"安全事件: {event_type} - {json.dumps(log_data)}"
        
        if level == 'info':
            security_logger.info(log_message)
        elif level == 'warning':
            security_logger.warning(log_message)
        elif level == 'error':
            security_logger.error(log_message)
        elif level == 'critical':
            security_logger.critical(log_message)
        
        # 同時記錄到統一的錯誤處理系統
        try:
            self.error_handler.log_operation(
                module='security',
                operation=event_type,
                message=f"安全事件: {event_type}",
                level=level,
                **details
            )
        except Exception:
            # 如果錯誤處理系統不可用，只記錄到日誌
            pass
    
    # ==================== 速率限制 ====================
    
    def check_rate_limit(self, identifier: str, endpoint: str, limit: int = 100, window_minutes: int = 60) -> Dict[str, Any]:
        """
        檢查速率限制
        
        參數:
            identifier: 識別符（用戶ID、IP地址等）
            endpoint: API端點
            limit: 限制次數
            window_minutes: 時間窗口（分鐘）
            
        返回:
            速率限制檢查結果
        """
        cache_key = f"rate_limit:{identifier}:{endpoint}"
        current_time = time.time()
        window_seconds = window_minutes * 60
        
        # 獲取歷史記錄
        if cache_key in self.rate_limit_cache:
            history = self.rate_limit_cache[cache_key]
            # 清理過期記錄
            history = [t for t in history if current_time - t < window_seconds]
        else:
            history = []
        
        # 檢查是否超過限制
        if len(history) >= limit:
            self.log_security_event('warning', 'rate_limit_exceeded', {
                'identifier': identifier,
                'endpoint': endpoint,
                'limit': limit,
                'window_minutes': window_minutes,
                'current_count': len(history)
            })
            
            return {
                'allowed': False,
                'remaining': 0,
                'reset_in': int(window_seconds - (current_time - history[0])),
                'limit': limit,
                'window_minutes': window_minutes
            }
        
        # 添加當前請求
        history.append(current_time)
        self.rate_limit_cache[cache_key] = history
        
        return {
            'allowed': True,
            'remaining': limit - len(history),
            'reset_in': window_seconds,
            'limit': limit,
            'window_minutes': window_minutes
        }
    
    # ==================== 請求驗證 ====================
    
    def validate_request_signature(self, request_data: Dict[str, Any], 
                                  secret_key: str, 
                                  signature_field: str = 'signature',
                                  timestamp_field: str = 'timestamp') -> bool:
        """
        驗證請求簽名
        
        參數:
            request_data: 請求數據
            secret_key: 密鑰
            signature_field: 簽名字段名
            timestamp_field: 時間戳字段名
            
        返回:
            簽名是否有效
        """
        if signature_field not in request_data:
            self.log_security_event('warning', 'missing_signature', {
                'request_keys': list(request_data.keys())
            })
            return False
        
        if timestamp_field not in request_data:
            self.log_security_event('warning', 'missing_timestamp', {
                'request_keys': list(request_data.keys())
            })
            return False
        
        # 檢查時間戳是否在有效範圍內（5分鐘內）
        try:
            request_timestamp = int(request_data[timestamp_field])
            current_timestamp = int(time.time())
            
            if abs(current_timestamp - request_timestamp) > 300:  # 5分鐘
                self.log_security_event('warning', 'expired_timestamp', {
                    'request_timestamp': request_timestamp,
                    'current_timestamp': current_timestamp,
                    'difference': abs(current_timestamp - request_timestamp)
                })
                return False
        except (ValueError, TypeError):
            self.log_security_event('warning', 'invalid_timestamp', {
                'timestamp': request_data.get(timestamp_field)
            })
            return False
        
        # 提取簽名
        received_signature = request_data[signature_field]
        
        # 創建待簽名數據（排除簽名字段本身）
        data_to_sign = {k: v for k, v in request_data.items() if k != signature_field}
        
        # 排序鍵以確保一致性
        sorted_items = sorted(data_to_sign.items())
        message = '&'.join([f"{k}={v}" for k, v in sorted_items])
        
        # 計算簽名
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 比較簽名
        is_valid = hmac.compare_digest(received_signature, expected_signature)
        
        if not is_valid:
            self.log_security_event('warning', 'invalid_signature', {
                'received_signature': received_signature[:10] + '...',
                'expected_signature': expected_signature[:10] + '...'
            })
        
        return is_valid
    
    # ==================== 安全配置檢查 ====================
    
    def check_security_configuration(self) -> Dict[str, Any]:
        """
        檢查安全配置
        
        返回:
            安全配置檢查結果
        """
        checks = {}
        
        try:
            # 檢查Django SECRET_KEY
            secret_key = getattr(settings, 'SECRET_KEY', None)
            checks['secret_key'] = {
                'configured': secret_key is not None and secret_key != 'your-secret-key-here',
                'length': len(secret_key) if secret_key else 0,
                'recommended_length': 50
            }
            
            # 檢查DEBUG模式
            debug_mode = getattr(settings, 'DEBUG', False)
            checks['debug_mode'] = {
                'enabled': debug_mode,
                'recommended': False,
                'warning': debug_mode  # DEBUG模式在生產環境應為False
            }
            
            # 檢查ALLOWED_HOSTS
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            checks['allowed_hosts'] = {
                'configured': len(allowed_hosts) > 0,
                'count': len(allowed_hosts),
                'contains_wildcard': '*' in allowed_hosts,
                'warning': '*' in allowed_hosts  # 萬用字符可能不安全
            }
            
            # 檢查CSRF保護
            csrf_enabled = getattr(settings, 'CSRF_COOKIE_SECURE', False)
            checks['csrf_protection'] = {
                'secure_cookie': csrf_enabled,
                'recommended': True
            }
            
            # 檢查HTTPS重定向
            secure_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
            checks['https_redirect'] = {
                'enabled': secure_ssl_redirect,
                'recommended': True
            }
            
        except Exception:
            # 如果Django設置不可用，返回基本檢查
            checks['django_settings'] = {
                'configured': False,
                'warning': True,
                'message': 'Django設置未配置'
            }
            
            # 添加其他基本檢查
            checks['python_version'] = {
                'version': sys.version,
                'recommended': '3.8+'
            }
            
            checks['security_utils'] = {
                'configured': True,
                'message': '安全工具模塊已加載'
            }
        
        # 計算總體評分
        passed_checks = sum(1 for check in checks.values() if not check.get('warning', False))
        total_checks = len(checks)
        score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        
        try:
            timestamp = timezone.now().isoformat()
        except Exception:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
        
        return {
            'checks': checks,
            'score': score,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'timestamp': timestamp
        }
    
    # ==================== 工具函數 ====================
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        生成安全令牌
        
        參數:
            length: 令牌長度
            
        返回:
            安全令牌
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_api_key(self, prefix: str = 'bc_') -> Tuple[str, str]:
        """
        生成API密鑰對（ID和密鑰）
        
        參數:
            prefix: 前綴
            
        返回:
            (api_id, api_key)
        """
        import secrets
        
        api_id = f"{prefix}{secrets.token_hex(8)}"
        api_key = secrets.token_hex(32)
        
        return api_id, api_key
    
    def validate_api_key(self, api_id: str, api_key: str, stored_hash: str) -> bool:
        """
        驗證API密鑰
        
        參數:
            api_id: API ID
            api_key: API密鑰
            stored_hash: 存儲的哈希值
            
        返回:
            是否有效
        """
        # 組合ID和密鑰進行驗證
        combined = f"{api_id}:{api_key}"
        computed_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        return hmac.compare_digest(computed_hash, stored_hash)


# 全局實例
security_utils = SecurityUtils()

# 快捷函數
def validate_input(data: Dict[str, Any], rules: Dict[str, Dict]) -> Dict[str, List[str]]:
    """快捷函數：驗證輸入數據"""
    return security_utils.validate_input(data, rules)

def sanitize_input(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """快捷函數：清理輸入數據"""
    return security_utils.sanitize_input(data)

def check_password_strength(password: str) -> Dict[str, Any]:
    """快捷函數：檢查密碼強度"""
    return security_utils.check_password_strength(password)

def log_security_event(level: str, event_type: str, details: Dict[str, Any] = None):
    """快捷函數：記錄安全事件"""
    security_utils.log_security_event(level, event_type, details)

def check_rate_limit(identifier: str, endpoint: str, limit: int = 100, window_minutes: int = 60) -> Dict[str, Any]:
    """快捷函數：檢查速率限制"""
    return security_utils.check_rate_limit(identifier, endpoint, limit, window_minutes)

def check_security_configuration() -> Dict[str, Any]:
    """快捷函數：檢查安全配置"""
    return security_utils.check_security_configuration()


# 測試
if __name__ == "__main__":
    print("=== 測試安全工具模塊 ===")
    
    # 測試輸入驗證
    test_data = {
        'email': 'test@example.com',
        'phone': '12345678',
        'password': 'Test123!@#'
    }
    
    test_rules = {
        'email': {'type': 'email', 'required': True},
        'phone': {'type': 'phone', 'required': True},
        'password': {'type': 'string', 'required': True, 'min_length': 8}
    }
    
    errors = validate_input(test_data, test_rules)
    print(f"輸入驗證結果: {errors}")
    
    # 測試密碼強度檢查
    password_result = check_password_strength('Test123!@#')
    print(f"密碼強度檢查: {password_result}")
    
    # 測試數據清理
    dirty_input = '<script>alert("xss")</script> OR 1=1'
    cleaned = sanitize_input(dirty_input)
    print(f"數據清理前: {dirty_input}")
    print(f"數據清理後: {cleaned}")
    
    # 測試安全配置檢查
    config_check = check_security_configuration()
    print(f"安全配置檢查分數: {config_check['score']}%")
    
    # 測試速率限制
    rate_limit_result = check_rate_limit('test_user', '/api/test', limit=5, window_minutes=1)
    print(f"速率限制檢查: {rate_limit_result}")
    
    print("=== 測試完成 ===")
