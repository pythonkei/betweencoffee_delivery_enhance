"""
Django settings for betweencoffee_delivery project.
"""

import logging
import os
import sys
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from environ import Env

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化环境变量读取
env = Env()

# 尝试读取环境文件，但忽略错误
try:
    # 明确指定.env文件路径
    env_file_path = os.path.join(BASE_DIR, ".env")
    print(f"Looking for .env file at: {env_file_path}")

    if os.path.exists(env_file_path):
        env.read_env(env_file_path)
        print("Successfully loaded .env file")

        # 调试：检查关键环境变量
        print(
            f"DEBUG - Google Client ID: {os.environ.get('OAUTH_GOOGLE_CLIENT_ID', 'Not set')}"
        )
        print(
            f"DEBUG - Facebook Client ID: {os.environ.get('OAUTH_FACEBOOK_CLIENT_ID', 'Not set')}"
        )
    else:
        print(f".env file not found at {env_file_path}")

except Exception as e:
    print(f"Warning: Could not read .env file: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Render 环境检测
IS_RENDER = (
    os.environ.get("IS_RENDER") == "True" or os.environ.get("RENDER") is not None
)

# 通用生产环境检测
IS_PRODUCTION = IS_RENDER

# ==================== 安全配置 ====================


def get_secret_key():
    """安全地获取密钥，在生产环境中必须设置"""
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key and IS_RENDER:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set in environment variables in production"
        )
    elif not secret_key:
        logger.warning(
            "Using default SECRET_KEY for development. "
            "Set SECRET_KEY environment variable for production."
        )
        return "django-insecure-development-key-change-in-production"
    return secret_key


SECRET_KEY = get_secret_key()

# DEBUG 配置 - 在生产环境上强制设为 False
if IS_PRODUCTION:
    DEBUG = False
else:
    DEBUG = env.bool("DEBUG", default=True)


# ALLOWED_HOSTS 配置
def get_allowed_hosts():
    """安全地配置允许的主机"""
    default_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]

    # 開發模式支援 ngrok 隧道
    ngrok_host = os.environ.get("NGROK_HOST", "")
    if ngrok_host:
        # 從 ngrok 域名提取頂級域名模式，例如 7def-119-236-126-88.ngrok-free.app → .ngrok-free.app
        parts = ngrok_host.split(".")
        if len(parts) >= 2:
            wildcard_domain = "." + ".".join(parts[-2:])  # .ngrok-free.app
        else:
            wildcard_domain = "." + parts[-1]
        default_hosts = [ngrok_host, wildcard_domain] + default_hosts

    if IS_RENDER:
        render_domain = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        if render_domain:
            return [render_domain, ".onrender.com"] + default_hosts
        else:
            logger.warning("RENDER_EXTERNAL_HOSTNAME not set, using fallback hosts")
            return [".onrender.com"] + default_hosts
    else:
        return default_hosts


ALLOWED_HOSTS = get_allowed_hosts()


# CSRF 信任源配置
def get_csrf_trusted_origins():
    """配置CSRF信任源"""
    if IS_RENDER:
        render_domain = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        if render_domain:
            return [f"https://{render_domain}", "https://*.onrender.com"]
        else:
            return ["https://*.onrender.com"]
    else:
        origins = ["http://localhost:8081", "http://127.0.0.1:8081"]
        # 開發模式支援 ngrok 隧道
        ngrok_host = os.environ.get("NGROK_HOST", "")
        if ngrok_host:
            origins.append(f"https://{ngrok_host}")
        return origins


CSRF_TRUSTED_ORIGINS = get_csrf_trusted_origins()


# 安全配置
if IS_RENDER:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # HSTS（HTTP Strict Transport Security）
    SECURE_HSTS_SECONDS = 31536000  # 一年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Referrer 政策
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"


# 检查daphne是否已安装（Render等无ASGI环境不需要）
try:
    pass

    DAPHNE_INSTALLED = True
except ImportError:
    DAPHNE_INSTALLED = False


# ==================== 应用定义 ====================

INSTALLED_APPS = [
    "channels",
    "eshop",
    "cart",
    "socialuser",
    "crispy_forms",
    "phonenumber_field",
    "django_rename_app",
    # 'debug_toolbar',
    # allauth 社交登录
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    # Django 核心应用
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_htmx",
]

# daphne 必须放在 channels 前面，但只在已安装时添加
if DAPHNE_INSTALLED:
    INSTALLED_APPS.insert(0, "daphne")

SITE_ID = 1


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "betweencoffee_delivery.middleware.CartMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "betweencoffee_delivery.middleware.AdminSessionMiddleware",
    "eshop.view_utils.ErrorLoggingMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

ROOT_URLCONF = "betweencoffee_delivery.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_count",
                "eshop.view_utils.error_context_processor",
            ],
            "string_if_invalid": "",
        },
    },
]

WSGI_APPLICATION = "betweencoffee_delivery.wsgi.application"


# Channels 層配置 - 開發環境使用內存層，生產環境使用Redis
if IS_RENDER:
    # Render環境使用Redis（如有配置）
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [redis_url],
                    "socket_timeout": 10,
                    "socket_connect_timeout": 10,
                    "retry_on_timeout": True,
                },
            },
        }
        print("使用Redis Channel層進行生產環境")
    else:
        # Render free plan 無 Redis，使用內存層
        CHANNEL_LAYERS = {
            "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
        }
        print("使用內存Channel層（Render 無 Redis）")
else:
    # 開發環境使用內存層（無需Redis）
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    print("使用內存Channel層進行開發")

# ✅ 確認 ASGI 應用設定正確
ASGI_APPLICATION = "betweencoffee_delivery.asgi.application"


# ==================== 数据库配置 ====================


def parse_database_url(url):
    """手動解析 DATABASE_URL，支援 Supabase 等複雜格式

    使用正則表達式直接從 URL 中提取各組件，避免 urlparse 在 Python 3.11+
    中可能出現的 hostname 驗證問題（如 ValueError: 'hostname' does not
    appear to be an IPv4 or IPv6 address）。
    """
    import re

    # 清理 pgbouncer 等 psycopg2 不支援的連線選項
    if "?" in url:
        base_url, query_string = url.split("?", 1)
        params = query_string.split("&")
        valid_params = [p for p in params if not p.startswith("pgbouncer")]
        url = base_url + ("?" + "&".join(valid_params) if valid_params else "")

    # 使用正則表達式解析 PostgreSQL URL
    # 格式: postgresql://user:password@host:port/database?options
    pattern = r"^postgres(?:ql)?://(?:([^:@]+)(?::([^@]*))?@)?([^:/?#]+)(?::(\d+))?(?:/([^?#]*))?(?:\?([^#]*))?"
    match = re.match(pattern, url)

    if match:
        username = unquote(match.group(1)) if match.group(1) else ""
        password = unquote(match.group(2)) if match.group(2) else ""
        host = match.group(3) or ""
        port = int(match.group(4)) if match.group(4) else 5432
        db_name = match.group(5) if match.group(5) else "postgres"
    else:
        # 正則表達式匹配失敗，回退到 urlparse
        logger.warning(f"Regex parse failed for DATABASE_URL, falling back to urlparse")
        parsed = urlparse(url)
        username = unquote(parsed.username) if parsed.username else ""
        password = unquote(parsed.password) if parsed.password else ""
        host = parsed.hostname or ""
        port = parsed.port or 5432
        db_name = parsed.path.lstrip("/") if parsed.path else "postgres"

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db_name,
        "USER": username,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
        "CONN_MAX_AGE": 0 if IS_RENDER else 600,
        "ATOMIC_REQUESTS": False,
    }


def get_database_config():
    """安全地配置数据库"""
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        try:
            db_config = parse_database_url(database_url)
            logger.info(
                f"Using DATABASE_URL (host={db_config['HOST']}, db={db_config['NAME']}, user={db_config['USER']})"
            )
            return {"default": db_config}
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            raise ImproperlyConfigured(f"Invalid DATABASE_URL: {e}")
    elif IS_RENDER:
        # Render 環境：資料庫已遷移至 Supabase，透過 DATABASE_URL 環境變數連接
        logger.warning(
            "Render environment detected but no DATABASE_URL set. Database will not be available."
        )
        # 返回一個無法連接的配置，但至少不會崩潰
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "unavailable",
                "USER": "unavailable",
                "PASSWORD": "unavailable",
                "HOST": "unavailable",
                "PORT": "5432",
                "CONN_MAX_AGE": 0,
                "ATOMIC_REQUESTS": False,
            }
        }
    else:
        # 本地开发环境
        logger.info("Using local PostgreSQL database")
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env("DB_NAME", default="betweencoffee_delivery_db"),
                "USER": env("DB_USER", default="postgres"),
                "PASSWORD": env("DB_PASSWORD", default="111111"),
                "HOST": env("DB_HOST", default="localhost"),
                "PORT": env("DB_PORT", default="5432"),
                "CONN_MAX_AGE": 600,
                "ATOMIC_REQUESTS": False,
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
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # 明确指定会话后端
SESSION_COOKIE_AGE = 1209600  # 2周，以秒为单位
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 认证设置
LOGIN_URL = "/accounts/login/"
LOGOUT_REDIRECT_URL = "/"


# 密码验证（強化：加入常用密碼檢查，提升安全性）
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# ==================== 国际化配置 ====================

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Hong_Kong"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==================== 静态文件配置 ====================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# WhiteNoise 配置
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# 媒体文件
# MEDIA_URL 根據環境動態設置：
# - 本地開發（DEBUG=True）：/media/ → Django static() helper 提供服務
# - 生產環境（DEBUG=False）：/static/media/ → Whitenoise 從 staticfiles/media/ 提供服務
# 這樣 image.url 在所有環境中都返回正確的路徑，無需額外的 get_media_url() 轉換。
if IS_PRODUCTION:
    MEDIA_URL = "/static/media/"
else:
    MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 购物车会话
CART_SESSION_ID = "cart"
CRISPY_TEMPLATE_PACK = "bootstrap4"


# ==================== 社交登录配置 ====================

# ==================== 惰性社交登录配置 ====================
# 注意：SOCIALACCOUNT_PROVIDERS 使用惰性加載（Lazy Load），
# 確保在 Render 運行時（而非 Docker build 階段）才讀取環境變數。
# 這樣 local 開發和 Render 生產環境都能正確獲取 OAuth 憑證和域名。


class LazySocialAccountProviders:
    """惰性加載 SOCIALACCOUNT_PROVIDERS

    在運行時才讀取環境變數和 Render 域名，解決：
    1. Docker build 階段 IS_RENDER=False 導致使用 localhost 的問題
    2. Render 環境變數在 build 階段不可用的問題
    """

    _cached_providers = None
    _logged = False

    def _load_providers(self):
        """運行時加載社交登錄提供商配置（僅首次執行 logger）"""
        if self._cached_providers is not None:
            return self._cached_providers

        providers = {}

        # 獲取基礎 URL 用於回調（運行時判斷）
        if IS_RENDER:
            render_domain = os.environ.get(
                "RENDER_EXTERNAL_HOSTNAME", "betweencoffee.onrender.com"
            )
            base_domain = render_domain
        else:
            base_domain = os.environ.get("NGROK_HOST", "localhost:8081")

        # Google 配置
        google_client_id = env("OAUTH_GOOGLE_CLIENT_ID", default="")
        google_secret = env("OAUTH_GOOGLE_SECRET", default="")

        if google_client_id and google_secret:
            providers["google"] = {
                "APP": {
                    "client_id": google_client_id,
                    "secret": google_secret,
                },
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {
                    "access_type": "online",
                    "prompt": "select_account",
                },
            }
        else:
            providers["google"] = {}

        # Facebook 配置
        facebook_client_id = env("OAUTH_FACEBOOK_CLIENT_ID", default="")
        facebook_secret = env("OAUTH_FACEBOOK_SECRET", default="")

        if facebook_client_id and facebook_secret:
            providers["facebook"] = {
                "APP": {
                    "client_id": facebook_client_id,
                    "secret": facebook_secret,
                },
                "METHOD": "oauth2",
                "SCOPE": ["email", "public_profile"],
                "FIELDS": [
                    "id",
                    "email",
                    "name",
                    "first_name",
                    "last_name",
                ],
                "AUTH_PARAMS": {
                    "auth_type": "reauthenticate",
                },
                "EXCHANGE_TOKEN": True,
                "VERIFIED_EMAIL": True,
            }
        else:
            providers["facebook"] = {}

        # 僅首次載入時記錄一次
        if not self._logged:
            google_ok = bool(google_client_id and google_secret)
            facebook_ok = bool(facebook_client_id and facebook_secret)
            logger.info(
                f"OAuth | Google: {'✅ configured' if google_ok else '❌ not set'} | Facebook: {'✅ configured' if facebook_ok else '❌ not set'} | domain: {base_domain}"
            )
            self._logged = True

        self._cached_providers = providers
        return providers

    def __getitem__(self, key):
        """支援字典式訪問（django-allauth 需要）"""
        return self._load_providers().__getitem__(key)

    def __contains__(self, key):
        """支援 'in' 運算符"""
        return key in self._load_providers()

    def __iter__(self):
        """支援迭代"""
        return iter(self._load_providers())

    def __len__(self):
        """支援 len()"""
        return len(self._load_providers())

    def get(self, key, default=None):
        """支援 .get() 方法"""
        return self._load_providers().get(key, default)

    def keys(self):
        """支援 .keys() 方法"""
        return self._load_providers().keys()

    def values(self):
        """支援 .values() 方法"""
        return self._load_providers().values()

    def items(self):
        """支援 .items() 方法"""
        return self._load_providers().items()


SOCIALACCOUNT_PROVIDERS = LazySocialAccountProviders()


# allauth 关键配置
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_ADAPTER = "socialuser.adapters.NoNewUsersAccountAdapter"
SOCIALACCOUNT_ADAPTER = "socialuser.adapters.SocialAccountAdapter"

# 社交账户配置
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
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
    if IS_RENDER:
        domain = os.environ.get(
            "RENDER_EXTERNAL_HOSTNAME", "betweencoffee.onrender.com"
        )
        name = "Between Coffee - Render"
        protocol = "https"
    else:
        ngrok_host = os.environ.get("NGROK_HOST", "")
        if ngrok_host:
            domain = ngrok_host
            name = "Between Coffee - Local (ngrok)"
            protocol = "https"
        else:
            domain = "localhost:8081"
            name = "Between Coffee - Local"
            protocol = "http"

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

LOGIN_REDIRECT_URL = "/"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/profile/settings/"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/accounts/login/"

SOCIALACCOUNT_TEMPLATES = {
    "login_cancelled": "socialuser/login_cancelled.html",
}


# 重要：配置社交登录回调URL
def get_social_callback_urls():
    """配置社交登录回调URL"""
    if IS_RENDER:
        render_domain = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        if render_domain:
            base_url = f"https://{render_domain}"
        else:
            base_url = "https://*.onrender.com"
    else:
        ngrok_host = os.environ.get("NGROK_HOST", "")
        if ngrok_host:
            base_url = f"https://{ngrok_host}"
        else:
            base_url = "http://localhost:8081"

    return {
        "google_callback": f"{base_url}/accounts/google/login/callback/",
        "facebook_callback": f"{base_url}/accounts/facebook/login/callback/",
    }


SOCIAL_CALLBACK_URLS = get_social_callback_urls()

# 电话号码字段配置
PHONENUMBER_DEFAULT_REGION = "HK"
PHONENUMBER_DB_FORMAT = "NATIONAL"

# ==================== 邮箱配置 ====================

# Gmail SMTP 郵件配置
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Between Coffee <pythonkei@gmail.com>"
)

# ==================== 日志配置 ====================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "django_errors.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "allauth": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "betweencoffee_delivery": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

# ==================== payment配置 ====================


ALIPAY_APP_ID = env("ALIPAY_APP_ID", default="9021000151625966")


#   安全優先：環境變數優先於檔案（2026-08-01 修改）
#   確保 Render 上使用環境變數設定的新金鑰，而不是 repo 歷史遺留的舊金鑰檔案
def read_alipay_key(env_name, filename):
    """安全地讀取支付寶金鑰：環境變數優先，檔案為 fallback（僅供本地開發）"""
    key_from_env = env(env_name, default="").strip()
    if key_from_env:
        return key_from_env

    key_path = os.path.join(BASE_DIR, "keys", filename)
    try:
        with open(key_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"密钥文件未找到: {key_path}")
        return ""


ALIPAY_APP_PRIVATE_KEY = read_alipay_key("ALIPAY_APP_PRIVATE_KEY", "alipay_private_key.pem")
ALIPAY_PUBLIC_KEY = read_alipay_key("ALIPAY_PUBLIC_KEY", "alipay_public_key.pem")

ALIPAY_DEBUG = True
ALIPAY_SIGN_TYPE = "RSA2"
ALIPAY_CHARSET = "utf-8"
ALIPAY_RETURN_URL = env(
    "ALIPAY_RETURN_URL", default="http://localhost:8081/eshop/payment/alipay/callback/"
)
ALIPAY_NOTIFY_URL = env(
    "ALIPAY_NOTIFY_URL", default="http://localhost:8081/eshop/payment/alipay/notify/"
)

# PayPal配置（僅從環境變數讀取，不設硬編碼 fallback）
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_CLIENT_SECRET = env("PAYPAL_CLIENT_SECRET", default="")
PAYPAL_ENVIRONMENT = env("PAYPAL_ENVIRONMENT", default="sandbox")

# FPS配置
FPS_MERCHANT_ID = env("FPS_MERCHANT_ID", default="BETWEENCOFFEE")
FPS_BANK_ACCOUNT = env("FPS_BANK_ACCOUNT", default="")
FPS_PHONE_NUMBER = env("FPS_PHONE_NUMBER", default="+85212345678")

# Twilio配置
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_PHONE_NUMBER = env("TWILIO_PHONE_NUMBER", default="")

# WhatsApp Cloud API 配置
WHATSAPP_TOKEN = env("WHATSAPP_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
WHATSAPP_BUSINESS_ACCOUNT_ID = env("WHATSAPP_BUSINESS_ACCOUNT_ID", default="")
WHATSAPP_ENABLED = bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID)

# ==================== 异常处理 ====================


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
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
    elif PAYPAL_ENVIRONMENT not in ["sandbox", "live"]:
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
    logger.info(f"IS_RENDER: {IS_RENDER}")
    logger.info(f"DEBUG: {DEBUG}")
    logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    logger.info(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")

    # 检查社交登录配置
    google_configured = bool(env("OAUTH_GOOGLE_CLIENT_ID", default=""))
    facebook_configured = bool(env("OAUTH_FACEBOOK_CLIENT_ID", default=""))

    # 修复：更宽松的支付配置检查
    alipay_configured = bool(
        ALIPAY_APP_ID and ALIPAY_APP_PRIVATE_KEY and ALIPAY_PUBLIC_KEY
    )
    paypal_configured = bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)

    logger.info(f"Google OAuth configured: {google_configured}")
    logger.info(f"Facebook OAuth configured: {facebook_configured}")
    logger.info(f"Alipay configured: {alipay_configured}")
    logger.info(f"PayPal configured: {paypal_configured}")
    logger.info(f"SOCIAL_CALLBACK_URLS: {SOCIAL_CALLBACK_URLS}")

    # 详细支付配置信息
    logger.info(f"Alipay App ID: {ALIPAY_APP_ID}")
    logger.info(
        f"Alipay Private Key length: {len(ALIPAY_APP_PRIVATE_KEY) if ALIPAY_APP_PRIVATE_KEY else 0}"
    )
    logger.info(
        f"Alipay Public Key length: {len(ALIPAY_PUBLIC_KEY) if ALIPAY_PUBLIC_KEY else 0}"
    )

    # 修复：更详细的PayPal配置日志
    logger.info(
        f"PayPal Client ID: {'*' * 8}{PAYPAL_CLIENT_ID[-8:]}"
        if PAYPAL_CLIENT_ID
        else "PayPal Client ID: Not set"
    )
    logger.info(
        f"PayPal Client Secret: {'*' * 8}{PAYPAL_CLIENT_SECRET[-8:]}"
        if PAYPAL_CLIENT_SECRET
        else "PayPal Client Secret: Not set"
    )
    logger.info(f"PayPal Environment: {PAYPAL_ENVIRONMENT}")

    # 修复：添加环境变量直接检查
    paypal_client_id_env = os.environ.get("PAYPAL_CLIENT_ID")
    paypal_secret_env = os.environ.get("PAYPAL_CLIENT_SECRET")
    logger.info(f"ENV PayPal Client ID: {'Set' if paypal_client_id_env else 'Not set'}")
    logger.info(
        f"ENV PayPal Client Secret: {'Set' if paypal_secret_env else 'Not set'}"
    )

    logger.info("=== Environment Check Complete ===")

    # 验证PayPal配置
    paypal_valid = validate_paypal_config()
    logger.info(f"PayPal配置验证: {'通过' if paypal_valid else '失败'}")


# 加载本地设置（如果存在）
try:
    pass

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
if DEBUG and IS_RENDER:
    logger.warning("DEBUG mode is enabled in production environment!")

if not SECRET_KEY.startswith("django-insecure-") and DEBUG:
    logger.info("Production SECRET_KEY is being used")


# Sensitive credentials removed for security
# 所有明文密碼/API keys/資料庫憑證已移除（2026-08-01 安全審查）
