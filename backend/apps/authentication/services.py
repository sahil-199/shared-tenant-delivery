import random
import string
import bcrypt
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    pass


class AccountLocked(Exception):
    pass


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    return bcrypt.checkpw(otp.encode(), otp_hash.encode())


def send_otp(phone: str, otp: str) -> None:
    provider = settings.OTP_PROVIDER
    if provider == 'mock':
        # ponytail: mock provider — swap body here for real SMS
        print(f"[OTP] Phone: {phone}, OTP: {otp}")
        logger.info(f"OTP for {phone}: {otp}")
        return
    raise NotImplementedError(f"OTP provider '{provider}' not implemented")


class OTPRateLimitService:
    def _rate_limit_key(self, phone: str) -> str:
        return f"otp:rate:{phone}"

    def _lockout_key(self, phone: str) -> str:
        return f"otp:lockout:{phone}"

    def _failed_key(self, phone: str) -> str:
        return f"otp:failed:{phone}"

    def check_rate_limit(self, phone: str) -> None:
        key = self._rate_limit_key(phone)
        count = cache.get(key, 0)
        if count >= settings.OTP_RATE_LIMIT_COUNT:
            raise RateLimitExceeded(
                f"Max {settings.OTP_RATE_LIMIT_COUNT} OTP requests per "
                f"{settings.OTP_RATE_LIMIT_WINDOW_MINUTES} minutes"
            )

    def record_otp_request(self, phone: str) -> None:
        key = self._rate_limit_key(phone)
        count = cache.get(key, 0)
        ttl = settings.OTP_RATE_LIMIT_WINDOW_MINUTES * 60
        cache.set(key, count + 1, timeout=ttl)

    def check_lockout(self, phone: str) -> None:
        if cache.get(self._lockout_key(phone)):
            raise AccountLocked("Account temporarily locked. Try again later.")

    def record_failed_attempt(self, phone: str) -> None:
        key = self._failed_key(phone)
        count = cache.get(key, 0) + 1
        cache.set(key, count, timeout=settings.OTP_MAX_ATTEMPTS * 60)
        if count >= settings.OTP_MAX_ATTEMPTS:
            lockout_ttl = settings.OTP_LOCKOUT_MINUTES * 60
            cache.set(self._lockout_key(phone), True, timeout=lockout_ttl)
            cache.delete(key)

    def clear_failed_attempts(self, phone: str) -> None:
        cache.delete(self._failed_key(phone))
        cache.delete(self._lockout_key(phone))
