"""
Django settings for betweencoffee_delivery project.
"""

import os
import sys
import logging
import dj_database_url
from environ import Env
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化环境变量读取
env = Env()

# 尝试读取环境文件，但忽略错误
try:
    # 明确指定.env文件路径
    env_file_path = os.path.join(BASE_DIR, '.env')
    print(f"Looking for .env file at: {env_file_path}")
    
    if os.path.exists(env_file_path):
        env.read_env(env_file_path)
        print("Successfully loaded .env file")
        
        # 调试：检查关键环境变量
        print(f"DEBUG - Google Client ID: {os.environ.get('OAUTH_GOOGLE_CLIENT_ID', 'Not set')}")
        print(f"DEBUG - Facebook Client ID: {os.environ.get('OAUTH_FACEBOOK_CLIENT_ID', 'Not set')}")
    else:
        print(f".env file not found at {env_file_path}")
        
except Exception as e:
    print(f"Warning: Could not read .env file: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Railway 环境检测
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# ==================== 安全配置 ====================

def get_secret_key():
    """安全地获取密钥，在生产环境中必须设置"""
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key and IS_RAILWAY:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set in environment variables in production"
        )
    elif not secret_key:
        logger.warning(
            "Using default SECRET_KEY for development. "
            "Set SECRET_KEY environment variable for production."
        )
        return 'django-insecure-development-key-change-in-production'
    return secret_key

SECRET_KEY = get_secret_key()

# DEBUG 配置 - 在 Railway 上强制设为 False
if IS_RAILWAY:
    DEBUG = False
else:
    DEBUG = env.bool('DEBUG', default=True)


# ALLOWED_HOSTS 配置
def get_allowed_hosts():
    """安全地配置允许的主机"""
    default_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
    
    if IS_RAILWAY:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain:
            return [railway_domain, '.railway.app'] + default_hosts
        else:
            logger.warning("RAILWAY_PUBLIC_DOMAIN not set, using fallback hosts")
            return ['.railway.app'] + default_hosts
    else:
        return default_hosts

ALLOWED_HOSTS = get_allowed_hosts()


# CSRF 信任源配置
def get_csrf_trusted_origins():
    """配置CSRF信任源"""
    if IS_RAILWAY:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain:
            return [f'https://{railway_domain}', 'https://*.railway.app']
        else:
            return ['https://*.railway.app']
    else:
        return ['http://localhost:8081', 'http://127.0.0.1:8081']

CSRF_TRUSTED_ORIGINS = get_csrf_trusted_origins()


# 安全配置
if IS_RAILWAY:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# 临时调试中间件
class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path == '/eshop/order_confirm/' and request.method == 'POST':
            print("=== 中间件检测到订单确认POST请求 ===")
            print(f"请求体: {request.POST}")
        
        response = self.get_response(request)
        return response


# # 检查daphne是否已安装
# try:
#     import daphne
#     DAPHNE_INSTALLED = True
# except ImportError:
#     DAPHNE_INSTALLED = False


# ==================== 应用定义 ====================

INSTALLED_APPS = [
    'daphne',  # 必须放在最前面
    'channels',
    'eshop',
    'cart',
    'socialuser',
    'crispy_forms',
    'phonenumber_field',
    "django_rename_app",
    # 'debug_toolbar',

    # allauth 社交登录
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',

    # Django 核心应用
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_htmx',
]

SITE_ID = 1


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'betweencoffee_delivery.middleware.CartMiddleware',
    'betweencoffee_delivery.middleware.DebugMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'betweencoffee_delivery.middleware.AdminSessionMiddleware',
    'eshop.view_utils.ErrorLoggingMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

ROOT_URLCONF = 'betweencoffee_delivery.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_count',
                'eshop.view_utils.error_context_processor',
            ],
            'string_if_invalid': 'INVALID_EXPRESSION' if DEBUG else '',
        },
    },
]

WSGI_APPLICATION = 'betweencoffee_delivery.wsgi.application'



# Channels 層配置 - 使用 Redis 作為後端
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],  # 開發環境
        },
    },
}

# 或在 Railway 上使用 URL 格式：
if IS_RAILWAY:
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_url],
                "socket_timeout": 10,
                "socket_connect_timeout": 10,
                "retry_on_timeout": True,
            },
        },
    }

# ✅ 確認 ASGI 應用設定正確
ASGI_APPLICATION = 'betweencoffee_delivery.asgi.application'


# # Channels层配置 - 使用Redis作为后端
# if IS_RAILWAY:
#     # Railway环境使用Redis
#     CHANNEL_LAYERS = {
#         'default': {
#             'BACKEND': 'channels_redis.core.RedisChannelLayer',
#             'CONFIG': {
#                 "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
#             },
#         },
#     }
# else:
#     # 开发环境使用内存层（无需Redis）
#     CHANNEL_LAYERS = {
#         "default": {
#             "BACKEND": "channels.layers.InMemoryChannelLayer"
#         }
#     }
#     print("使用内存Channel层进行开发")



# ==================== 数据库配置 ====================

def get_database_config():
    """安全地配置数据库"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        try:
            # 简化配置，移除重复参数
            db_config = dj_database_url.parse(database_url)
            
            # 确保必要的配置
            db_config.setdefault('CONN_MAX_AGE', 600)
            db_config.setdefault('ATOMIC_REQUESTS', False)  # 改为False避免事务问题
            
            return {
                'default': db_config
            }
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            raise ImproperlyConfigured(f"Invalid DATABASE_URL: {e}")
    else:
        # 本地开发环境
        logger.info("Using local PostgreSQL database")
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME', default='betweencoffee_delivery_db'),
                'USER': env('DB_USER', default='postgres'),
                'PASSWORD': env('DB_PASSWORD', default='111111'),
                'HOST': env('DB_HOST', default='localhost'),
                'PORT': env('DB_PORT', default='5432'),
                'CONN_MAX_AGE': 600,
                'ATOMIC_REQUESTS': False,
            }
        }
    

DATABASES = get_database_config()


# PostgreSQL pgAdmin Backup -
# 步驟- 備份對話框設置Backup database: betweencoffee_delivery_db
# betweencoffee_delivery_db  ← 右鍵這裡
# -----------------------------------------
# General 標籤:
#   Filename:    /home/kei/coffee_backup_20250126_154230.backup
#   Format:      Custom
#   Encoding:    UTF8

# Options 標籤:
#   □ Sections: Pre-data, Data, Post-data  (全勾選)
#   □ Verbose messages: ✓ 勾選
#   □ Use Column Inserts
#   □ Use Insert Commands

# Dump Options #1 標籤:
#   □ DROP DATABASE statement  (不要勾選！)
#   □ IF EXISTS clause         (✓ 建議勾選)

# Dump Options #2 標籤:
#   保持預設

# file1. betweencoffee_delivery_db_backup_20250126_6pm.backup


# 使用 postgres 用戶測試
# 1. 創建測試數據庫
# sudo -u postgres createdb betweencoffee_delivery_test

# 2. 檢查是否創建成功
# sudo -u postgres psql -l | grep betweencoffee_delivery_test

# 3. 恢復備份到測試數據庫
# sudo -u postgres pg_restore --verbose --clean --if-exists --no-acl --no-owner -d betweencoffee_delivery_test betweencoffee_delivery_db_backup_20250126_6pm.backup

# 4. 驗證數據恢復
# sudo -u postgres psql -d betweencoffee_delivery_test -c "SELECT COUNT(*) FROM eshop_ordermodel;"
# sudo -u postgres psql -d betweencoffee_delivery_test -c "SELECT COUNT(*) FROM eshop_coffeeitem;"




# Session设置
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # 明确指定会话后端
SESSION_COOKIE_AGE = 1209600  # 2周，以秒为单位
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 认证设置
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = '/'


# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ==================== 国际化配置 ====================

LANGUAGE_CODE = 'zh-hant'
TIME_ZONE = 'Asia/Hong_Kong'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==================== 静态文件配置 ====================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise 配置
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# 媒体文件
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 购物车会话
CART_SESSION_ID = 'cart'
CRISPY_TEMPLATE_PACK = 'bootstrap4'


# ==================== 社交登录配置 ====================

def get_social_providers():
    """安全地配置社交登录提供商"""
    providers = {}
    
    # 获取基础URL用于回调
    if IS_RAILWAY:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6a798.up.railway.app')
        base_domain = railway_domain
    else:
        base_domain = 'localhost:8081'
    
    # Google配置
    google_client_id = env('OAUTH_GOOGLE_CLIENT_ID', default='')
    google_secret = env('OAUTH_GOOGLE_SECRET', default='')
    
    if google_client_id and google_secret:
        providers['google'] = {
            'APP': {
                'client_id': google_client_id,
                'secret': google_secret,
            },
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {
                'access_type': 'online',
                'prompt': 'select_account',
            },
        }
        logger.info(f"Google OAuth configured for domain: {base_domain}")
    else:
        logger.warning("Google OAuth credentials not set")

    # Facebook配置
    facebook_client_id = env('OAUTH_FACEBOOK_CLIENT_ID', default='')
    facebook_secret = env('OAUTH_FACEBOOK_SECRET', default='')
    
    if facebook_client_id and facebook_secret:
        providers['facebook'] = {
            'APP': {
                'client_id': facebook_client_id,
                'secret': facebook_secret,
            },
            'METHOD': 'oauth2',
            'SCOPE': ['email', 'public_profile'],
            'FIELDS': [
                'id',
                'email', 
                'name',
                'first_name',
                'last_name',
            ],
            'AUTH_PARAMS': {
                'auth_type': 'reauthenticate',
                'display': 'popup',
            },
            'EXCHANGE_TOKEN': True,
            'VERIFIED_EMAIL': True,
        }
        logger.info(f"Facebook OAuth configured for domain: {base_domain}")
    else:
        logger.warning("Facebook OAuth credentials not set")
    
    return providers

SOCIALACCOUNT_PROVIDERS = get_social_providers()

# allauth 关键配置
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'socialuser.adapters.NoNewUsersAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'socialuser.adapters.SocialAccountAdapter'

# 社交账户配置
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_LOGIN_ON_GET = True  # 设置为 True 可以直接跳转到 OAuth 页面
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# 允许社交账户注册
ACCOUNT_ALLOW_SOCIAL_SIGNUP = True

# 重要：动态站点配置
def setup_site_config():
    """动态配置站点信息"""
    if IS_RAILWAY:
        domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6a798.up.railway.app')
        name = 'Between Coffee - Railway'
        protocol = 'https'
    else:
        domain = 'localhost:8081'
        name = 'Between Coffee - Local'
        protocol = 'http'
    
    return domain, name, protocol

SITE_DOMAIN, SITE_NAME, PROTOCOL = setup_site_config()

# 更新站点信息
try:
    from django.contrib.sites.models import Site
    site = Site.objects.get(id=SITE_ID)
    if site.domain != SITE_DOMAIN or site.name != SITE_NAME:
        site.domain = SITE_DOMAIN
        site.name = SITE_NAME
        site.save()
        logger.info(f"Site updated: {SITE_DOMAIN} - {SITE_NAME}")
except Exception as e:
    logger.warning(f"Could not update site: {e}")

LOGIN_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/profile/settings/'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/accounts/login/'

SOCIALACCOUNT_TEMPLATES = {
    'login_cancelled': 'socialuser/login_cancelled.html',
}



# 重要：配置社交登录回调URL
def get_social_callback_urls():
    """配置社交登录回调URL"""
    if IS_RAILWAY:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain:
            base_url = f'https://{railway_domain}'
        else:
            base_url = 'https://*.railway.app'
    else:
        base_url = 'http://localhost:8081'
    
    return {
        'google_callback': f'{base_url}/accounts/google/login/callback/',
        'facebook_callback': f'{base_url}/accounts/facebook/login/callback/',
    }

SOCIAL_CALLBACK_URLS = get_social_callback_urls()

# 电话号码字段配置
PHONENUMBER_DEFAULT_REGION = "HK"
PHONENUMBER_DB_FORMAT = "NATIONAL"

# ==================== 邮箱配置 ====================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # 简化邮箱配置

# ==================== 日志配置 ====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_errors.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'betweencoffee_delivery': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ==================== payment配置 ====================


ALIPAY_APP_ID = env('ALIPAY_APP_ID', default='9021000151625966')

# 从文件读取密钥
def read_key_file(filename):
    """从文件读取密钥"""
    key_path = os.path.join(BASE_DIR, 'keys', filename)
    try:
        with open(key_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"密钥文件未找到: {key_path}")
        return ''

ALIPAY_APP_PRIVATE_KEY = read_key_file('alipay_private_key.pem')
ALIPAY_PUBLIC_KEY = read_key_file('alipay_public_key.pem')

# 如果文件读取失败，回退到环境变量
if not ALIPAY_APP_PRIVATE_KEY:
    ALIPAY_APP_PRIVATE_KEY = env('ALIPAY_APP_PRIVATE_KEY', default='')
if not ALIPAY_PUBLIC_KEY:
    ALIPAY_PUBLIC_KEY = env('ALIPAY_PUBLIC_KEY', default='')

ALIPAY_DEBUG = True
ALIPAY_SIGN_TYPE = 'RSA2'
ALIPAY_CHARSET = 'utf-8'
ALIPAY_RETURN_URL = env('ALIPAY_RETURN_URL', default='http://localhost:8081/eshop/payment/alipay/callback/' )
ALIPAY_NOTIFY_URL = env('ALIPAY_NOTIFY_URL', default='http://localhost:8081/eshop/payment/alipay/notify/')

# PayPal配置
PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID', default='')
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET', default='')
PAYPAL_ENVIRONMENT = env('PAYPAL_ENVIRONMENT', default='sandbox')  # 添加这行

# 如果环境变量为空，使用硬编码值作为后备（仅用于开发）
if not PAYPAL_CLIENT_ID:
    PAYPAL_CLIENT_ID = 'AZPAFBc3xr01Ap4DUkDj0P6pGhPwizG93cXocVlQv-PJQ87BROpjqxxRXgYpI82guz3Aebq9uhvIaUp-'
    logger.warning("使用后备PayPal Client ID")

if not PAYPAL_CLIENT_SECRET:
    PAYPAL_CLIENT_SECRET = 'EPwY7G6-uAKNjmDUhy-Awa_HC-MjaU3VHN8d4K4eQ3n67_2ndR_3A8TFrC8O-ZL3QVFIELPlB81XAWwS'
    logger.warning("使用后备PayPal Client Secret")

print(f"DEBUG - 最终PayPal配置: {PAYPAL_CLIENT_ID[:20]}...")

# FPS配置
FPS_MERCHANT_ID = env('FPS_MERCHANT_ID', default='BETWEENCOFFEE')
FPS_BANK_ACCOUNT = env('FPS_BANK_ACCOUNT', default='')
FPS_PHONE_NUMBER = env('FPS_PHONE_NUMBER', default='+85212345678')

# Twilio配置
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')



# ==================== 异常处理 ====================

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical(
        "Unhandled exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

sys.excepthook = handle_unhandled_exception



# ==================== 环境检查 ====================


def validate_paypal_config():
    """验证PayPal配置"""
    issues = []
    
    if not PAYPAL_CLIENT_ID:
        issues.append("PAYPAL_CLIENT_ID 未设置")
    elif len(PAYPAL_CLIENT_ID) < 10:
        issues.append("PAYPAL_CLIENT_ID 长度异常")
    
    if not PAYPAL_CLIENT_SECRET:
        issues.append("PAYPAL_CLIENT_SECRET 未设置")
    elif len(PAYPAL_CLIENT_SECRET) < 10:
        issues.append("PAYPAL_CLIENT_SECRET 长度异常")
    
    if not PAYPAL_ENVIRONMENT:
        issues.append("PAYPAL_ENVIRONMENT 未设置")
    elif PAYPAL_ENVIRONMENT not in ['sandbox', 'live']:
        issues.append("PAYPAL_ENVIRONMENT 必须是 'sandbox' 或 'live'")
    
    if issues:
        logger.warning(f"PayPal配置问题: {', '.join(issues)}")
        return False
    else:
        logger.info("PayPal配置验证通过")
        return True


def check_environment():
    """检查环境配置"""
    logger.info("=== Environment Check ===")
    logger.info(f"IS_RAILWAY: {IS_RAILWAY}")
    logger.info(f"DEBUG: {DEBUG}")
    logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    logger.info(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
    
    # 检查社交登录配置
    google_configured = bool(env('OAUTH_GOOGLE_CLIENT_ID', default=''))
    facebook_configured = bool(env('OAUTH_FACEBOOK_CLIENT_ID', default=''))
    
    # 修复：更宽松的支付配置检查
    alipay_configured = bool(ALIPAY_APP_ID and ALIPAY_APP_PRIVATE_KEY and ALIPAY_PUBLIC_KEY)
    paypal_configured = bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)
    
    logger.info(f"Google OAuth configured: {google_configured}")
    logger.info(f"Facebook OAuth configured: {facebook_configured}")
    logger.info(f"Alipay configured: {alipay_configured}")
    logger.info(f"PayPal configured: {paypal_configured}")
    logger.info(f"SOCIAL_CALLBACK_URLS: {SOCIAL_CALLBACK_URLS}")
    
    # 详细支付配置信息
    logger.info(f"Alipay App ID: {ALIPAY_APP_ID}")
    logger.info(f"Alipay Private Key length: {len(ALIPAY_APP_PRIVATE_KEY) if ALIPAY_APP_PRIVATE_KEY else 0}")
    logger.info(f"Alipay Public Key length: {len(ALIPAY_PUBLIC_KEY) if ALIPAY_PUBLIC_KEY else 0}")
    
    # 修复：更详细的PayPal配置日志
    logger.info(f"PayPal Client ID: {'*' * 8}{PAYPAL_CLIENT_ID[-8:]}" if PAYPAL_CLIENT_ID else "PayPal Client ID: Not set")
    logger.info(f"PayPal Client Secret: {'*' * 8}{PAYPAL_CLIENT_SECRET[-8:]}" if PAYPAL_CLIENT_SECRET else "PayPal Client Secret: Not set")
    logger.info(f"PayPal Environment: {PAYPAL_ENVIRONMENT}")
    
    # 修复：添加环境变量直接检查
    paypal_client_id_env = os.environ.get('PAYPAL_CLIENT_ID')
    paypal_secret_env = os.environ.get('PAYPAL_CLIENT_SECRET')
    logger.info(f"ENV PayPal Client ID: {'Set' if paypal_client_id_env else 'Not set'}")
    logger.info(f"ENV PayPal Client Secret: {'Set' if paypal_secret_env else 'Not set'}")
    
    logger.info("=== Environment Check Complete ===")

    # 验证PayPal配置
    paypal_valid = validate_paypal_config()
    logger.info(f"PayPal配置验证: {'通过' if paypal_valid else '失败'}")



# 加载本地设置（如果存在）
try:
    from .local_settings import *
    logger.info("Local settings loaded successfully")
except ImportError:
    logger.info("No local settings found, using default configuration")
except Exception as e:
    logger.error(f"Error loading local settings: {e}")


# 在设置加载完成后运行环境检查
try:
    check_environment()
    validate_paypal_config()
except Exception as e:
    logger.error(f"启动时配置检查失败: {e}")

# 最终安全检查
if DEBUG and IS_RAILWAY:
    logger.warning("DEBUG mode is enabled in production environment!")

if not SECRET_KEY.startswith('django-insecure-') and DEBUG:
    logger.info("Production SECRET_KEY is being used")




'''
For myself reference

virtualenvwrapper path:
/home/kei/.virtualenvs/betweencoffee_delivery/bin/python
/home/kei/.virtualenvs/betweencoffee_delivery/bin/python
Check 日志 command：
tail -f /home/kei/Desktop/betweencoffee_delivery_enhance/cron.log 

HK Alipay bussiness ac
pythonkei@gmail.com, Password_123
Alipay Sandbox:
https://global.alipay.com/docs/ac/hk_auto_debit/sandbox
https://noter.tw/5445/php-%E4%B8%B2%E6%8E%A5-alipayhk-%E8%B8%A9%E5%9D%91%E8%A8%98%E9%8C%84/



DeepSeek API key
sk-362506ad6b114bf8a9c944bec5e2dd1e

Paypal_pass_829919

Alipay bussiness ac
pythonkei@gmail.com, Password_123
设置支付宝国际账户支付密码:Alipaypass123_

china mobile:
19168604470

csdn account
id:heyeahheyeah


Fully Tutorial for social login (followed):
OAuth - Social Logins with Django and Allauth - Google, Github, X and Facebook
https://www.youtube.com/watch?v=dASjmItZcWE


#FB:
#PassPassPassFB999
#meta for developers ac and my app info:
#app name: kei_production
'''

'''
ollama ac:
pythonkei
pythonkei@gmail.com
'''

