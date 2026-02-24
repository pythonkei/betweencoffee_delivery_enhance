"""
安全配置模塊 - 集中管理系統安全配置

這個模塊提供：
1. 安全配置常量定義
2. 安全策略管理
3. 安全配置驗證
4. 安全配置工具

版本: 1.0.0
"""

from typing import Dict, List, Any, Optional
from django.conf import settings


class SecurityConfig:
    """安全配置類"""
    
    # ==================== 安全常量 ====================
    
    # 密碼策略
    PASSWORD_POLICY = {
        'min_length': 8,
        'max_length': 128,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True,
        'max_age_days': 90,  # 密碼最長使用天數
        'history_count': 5,  # 記住最近幾個密碼
    }
    
    # 會話安全
    SESSION_SECURITY = {
        'timeout_minutes': 30,  # 會話超時時間
        'absolute_timeout_hours': 24,  # 絕對超時時間
        'renewal_threshold_minutes': 5,  # 續期閾值
        'secure_cookie': True,  # 安全Cookie
        'http_only': True,  # HTTP Only
        'same_site': 'Lax',  # SameSite策略
    }
    
    # API安全
    API_SECURITY = {
        'rate_limits': {
            'default': {'limit': 100, 'window_minutes': 60},
            'auth': {'limit': 5, 'window_minutes': 1},
            'payment': {'limit': 10, 'window_minutes': 1},
            'order': {'limit': 30, 'window_minutes': 1},
            'admin': {'limit': 1000, 'window_minutes': 60},
        },
        'require_https': True,
        'cors_allowed_origins': [],  # 生產環境應明確指定
        'cors_allow_credentials': False,
    }
    
    # 輸入驗證規則
    VALIDATION_RULES = {
        'email': {
            'type': 'string',
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'min_length': 5,
            'max_length': 255,
            'required': True,
        },
        'phone': {
            'type': 'string',
            'pattern': r'^[0-9+\-\s()]{8,20}$',
            'min_length': 8,
            'max_length': 20,
            'required': True,
        },
        'username': {
            'type': 'string',
            'pattern': r'^[a-zA-Z0-9_]{3,30}$',
            'min_length': 3,
            'max_length': 30,
            'required': True,
        },
        'password': {
            'type': 'string',
            'min_length': 8,
            'max_length': 128,
            'required': True,
        },
        'name': {
            'type': 'string',
            'min_length': 2,
            'max_length': 100,
            'required': True,
        },
        'address': {
            'type': 'string',
            'min_length': 5,
            'max_length': 500,
            'required': False,
        },
        'order_notes': {
            'type': 'string',
            'min_length': 0,
            'max_length': 1000,
            'required': False,
        },
    }
    
    # 支付安全配置
    PAYMENT_SECURITY = {
        'amount_tolerance_percent': 1.0,  # 金額容差百分比
        'timeout_minutes': 15,  # 支付超時時間
        'max_retries': 3,  # 最大重試次數
        'require_https': True,
        'validate_signature': True,
        'log_all_transactions': True,
    }
    
    # 日誌安全配置
    LOGGING_SECURITY = {
        'log_sensitive_data': False,  # 是否記錄敏感數據
        'mask_credit_cards': True,  # 掩蓋信用卡號
        'mask_emails': False,  # 掩蓋電子郵件
        'mask_phones': False,  # 掩蓋電話號碼
        'retention_days': 90,  # 日誌保留天數
        'security_event_logging': True,  # 安全事件日誌
    }
    
    # 數據備份配置
    BACKUP_SECURITY = {
        'enabled': True,
        'frequency_hours': 24,  # 備份頻率
        'retention_days': 30,  # 保留天數
        'encrypt_backups': True,  # 加密備份
        'verify_backups': True,  # 驗證備份
        'offsite_backup': False,  # 異地備份
    }
    
    # ==================== 安全頭部配置 ====================
    
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    # ==================== 初始化方法 ====================
    
    def __init__(self):
        """初始化安全配置"""
        self._load_settings()
    
    def _load_settings(self):
        """加載Django設置中的安全配置"""
        try:
            # 從Django設置中覆蓋默認配置
            self.PASSWORD_POLICY.update(
                getattr(settings, 'SECURITY_PASSWORD_POLICY', {})
            )
            self.SESSION_SECURITY.update(
                getattr(settings, 'SECURITY_SESSION_CONFIG', {})
            )
            self.API_SECURITY.update(
                getattr(settings, 'SECURITY_API_CONFIG', {})
            )
            self.PAYMENT_SECURITY.update(
                getattr(settings, 'SECURITY_PAYMENT_CONFIG', {})
            )
            self.LOGGING_SECURITY.update(
                getattr(settings, 'SECURITY_LOGGING_CONFIG', {})
            )
            self.BACKUP_SECURITY.update(
                getattr(settings, 'SECURITY_BACKUP_CONFIG', {})
            )
            self.SECURITY_HEADERS.update(
                getattr(settings, 'SECURITY_HEADERS_CONFIG', {})
            )
        except Exception:
            # 如果Django設置不可用，使用默認配置
            pass
    
    # ==================== 配置驗證方法 ====================
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        驗證安全配置
        
        返回:
            配置驗證結果
        """
        from eshop.utils.security_utils import security_utils
        
        # 使用安全工具檢查配置
        config_check = security_utils.check_security_configuration()
        
        # 添加自定義檢查
        custom_checks = {}
        
        # 檢查密碼策略
        password_policy = self.PASSWORD_POLICY
        custom_checks['password_policy'] = {
            'min_length_ok': password_policy['min_length'] >= 8,
            'max_length_ok': password_policy['max_length'] <= 128,
            'complexity_required': all([
                password_policy['require_uppercase'],
                password_policy['require_lowercase'],
                password_policy['require_digits'],
                password_policy['require_special'],
            ]),
            'max_age_ok': password_policy['max_age_days'] <= 180,
        }
        
        # 檢查會話安全
        session_security = self.SESSION_SECURITY
        custom_checks['session_security'] = {
            'timeout_ok': session_security['timeout_minutes'] <= 60,
            'secure_cookie': session_security['secure_cookie'],
            'http_only': session_security['http_only'],
            'same_site_ok': session_security['same_site'] in ['Strict', 'Lax'],
        }
        
        # 檢查API安全
        api_security = self.API_SECURITY
        custom_checks['api_security'] = {
            'rate_limits_configured': len(api_security['rate_limits']) > 0,
            'require_https': api_security['require_https'],
            'cors_restrictive': len(api_security['cors_allowed_origins']) == 0 or 
                               '*' not in api_security['cors_allowed_origins'],
        }
        
        # 計算總體評分
        all_checks = {**config_check['checks'], **custom_checks}
        passed_checks = sum(
            1 for check in all_checks.values() 
            if not check.get('warning', False) and check.get('configured', True)
        )
        total_checks = len(all_checks)
        score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        
        return {
            'django_config': config_check,
            'custom_checks': custom_checks,
            'overall_score': score,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'recommendations': self._get_recommendations(all_checks),
        }
    
    def _get_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """獲取安全配置建議"""
        recommendations = []
        
        # Django配置建議
        django_checks = checks
        
        if django_checks.get('secret_key', {}).get('warning'):
            recommendations.append("更換Django SECRET_KEY，使用更長的隨機字符串")
        
        if django_checks.get('debug_mode', {}).get('warning'):
            recommendations.append("在生產環境中禁用DEBUG模式")
        
        if django_checks.get('allowed_hosts', {}).get('warning'):
            recommendations.append("避免在ALLOWED_HOSTS中使用萬用字符(*)")
        
        if not django_checks.get('csrf_protection', {}).get('secure_cookie'):
            recommendations.append("啟用CSRF_COOKIE_SECURE以保護CSRF令牌")
        
        if not django_checks.get('https_redirect', {}).get('enabled'):
            recommendations.append("啟用SECURE_SSL_REDIRECT以強制HTTPS")
        
        # 密碼策略建議
        password_checks = checks.get('password_policy', {})
        if not password_checks.get('min_length_ok'):
            recommendations.append("密碼最小長度應至少為8個字符")
        
        if not password_checks.get('complexity_required'):
            recommendations.append("啟用密碼複雜度要求（大寫、小寫、數字、特殊字符）")
        
        # 會話安全建議
        session_checks = checks.get('session_security', {})
        if not session_checks.get('secure_cookie'):
            recommendations.append("啟用安全會話Cookie")
        
        if not session_checks.get('http_only'):
            recommendations.append("啟用HTTP Only會話Cookie")
        
        # API安全建議
        api_checks = checks.get('api_security', {})
        if not api_checks.get('require_https'):
            recommendations.append("API應要求HTTPS連接")
        
        if not api_checks.get('cors_restrictive'):
            recommendations.append("限制CORS允許的來源，避免使用萬用字符")
        
        return recommendations
    
    # ==================== 配置獲取方法 ====================
    
    def get_password_policy(self) -> Dict[str, Any]:
        """獲取密碼策略"""
        return self.PASSWORD_POLICY.copy()
    
    def get_session_config(self) -> Dict[str, Any]:
        """獲取會話配置"""
        return self.SESSION_SECURITY.copy()
    
    def get_api_security_config(self) -> Dict[str, Any]:
        """獲取API安全配置"""
        return self.API_SECURITY.copy()
    
    def get_validation_rules(self, rule_name: Optional[str] = None) -> Dict[str, Any]:
        """獲取驗證規則"""
        if rule_name:
            return self.VALIDATION_RULES.get(rule_name, {}).copy()
        return self.VALIDATION_RULES.copy()
    
    def get_payment_security_config(self) -> Dict[str, Any]:
        """獲取支付安全配置"""
        return self.PAYMENT_SECURITY.copy()
    
    def get_security_headers(self) -> Dict[str, str]:
        """獲取安全頭部配置"""
        return self.SECURITY_HEADERS.copy()
    
    def get_rate_limit_config(self, endpoint_type: str = 'default') -> Dict[str, Any]:
        """獲取速率限制配置"""
        rate_limits = self.API_SECURITY['rate_limits']
        return rate_limits.get(endpoint_type, rate_limits['default']).copy()
    
    # ==================== 配置更新方法 ====================
    
    def update_password_policy(self, updates: Dict[str, Any]) -> None:
        """更新密碼策略"""
        self.PASSWORD_POLICY.update(updates)
    
    def update_session_config(self, updates: Dict[str, Any]) -> None:
        """更新會話配置"""
        self.SESSION_SECURITY.update(updates)
    
    def update_api_security_config(self, updates: Dict[str, Any]) -> None:
        """更新API安全配置"""
        self.API_SECURITY.update(updates)
    
    def update_validation_rules(self, rule_name: str, updates: Dict[str, Any]) -> None:
        """更新驗證規則"""
        if rule_name in self.VALIDATION_RULES:
            self.VALIDATION_RULES[rule_name].update(updates)
        else:
            self.VALIDATION_RULES[rule_name] = updates
    
    # ==================== 工具方法 ====================
    
    def get_config_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            'password_policy': {
                'min_length': self.PASSWORD_POLICY['min_length'],
                'require_complexity': all([
                    self.PASSWORD_POLICY['require_uppercase'],
                    self.PASSWORD_POLICY['require_lowercase'],
                    self.PASSWORD_POLICY['require_digits'],
                    self.PASSWORD_POLICY['require_special'],
                ]),
            },
            'session_security': {
                'timeout_minutes': self.SESSION_SECURITY['timeout_minutes'],
                'secure_cookie': self.SESSION_SECURITY['secure_cookie'],
            },
            'api_security': {
                'rate_limits_count': len(self.API_SECURITY['rate_limits']),
                'require_https': self.API_SECURITY['require_https'],
            },
            'payment_security': {
                'validate_signature': self.PAYMENT_SECURITY['validate_signature'],
                'log_transactions': self.PAYMENT_SECURITY['log_all_transactions'],
            },
            'backup_security': {
                'enabled': self.BACKUP_SECURITY['enabled'],
                'encrypt_backups': self.BACKUP_SECURITY['encrypt_backups'],
            },
            'security_headers_count': len(self.SECURITY_HEADERS),
        }
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全報告"""
        config_validation = self.validate_configuration()
        
        return {
            'timestamp': self._get_current_timestamp(),
            'configuration_summary': self.get_config_summary(),
            'validation_results': config_validation,
            'recommendations': config_validation['recommendations'],
            'overall_score': config_validation['overall_score'],
            'status': 'secure' if config_validation['overall_score'] >= 80 else 'needs_improvement',
        }
    
    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳"""
        try:
            from django.utils import timezone
            return timezone.now().isoformat()
        except Exception:
            from datetime import datetime
            return datetime.now().isoformat()


# 全局配置實例
security_config = SecurityConfig()

# 快捷函數
def get_password_policy() -> Dict[str, Any]:
    """獲取密碼策略"""
    return security_config.get_password_policy()

def get_validation_rules(rule_name: str = None) -> Dict[str, Any]:
    """獲取驗證規則"""
    return security_config.get_validation_rules(rule_name)

def get_security_headers() -> Dict[str, str]:
    """獲取安全頭部配置"""
    return security_config.get_security_headers()

def validate_security_configuration() -> Dict[str, Any]:
    """驗證安全配置"""
    return security_config.validate_configuration()

def generate_security_report() -> Dict[str, Any]:
    """生成安全報告"""
    return security_config.generate_security_report()


# 測試
if __name__ == "__main__":
    print("=== 測試安全配置模塊 ===")
    
    # 測試配置獲取
    password_policy = get_password_policy()
    print(f"密碼策略: {password_policy}")
    
    # 測試驗證規則
    email_rules = get_validation_rules('email')
    print(f"電子郵件驗證規則: {email_rules}")
    
    # 測試安全頭部
    security_headers = get_security_headers()
    print(f"安全頭部數量: {len(security_headers)}")
    
    # 測試配置驗證
    config_validation = validate_security_configuration()
    print(f"配置驗證分數: {config_validation['overall_score']}%")
    
    # 測試安全報告
    security_report = generate_security_report()
    print(f"安全報告狀態: {security_report['status']}")
    
    print("=== 測試完成 ===")
