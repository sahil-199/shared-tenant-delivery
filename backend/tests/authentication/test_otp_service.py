import pytest
from unittest.mock import patch
from apps.authentication.services import (
    generate_otp, hash_otp, verify_otp_hash, send_otp,
    OTPRateLimitService, RateLimitExceeded, AccountLocked,
)


def test_generate_otp_is_6_digits():
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_otp_hash_and_verify():
    otp = '123456'
    hashed = hash_otp(otp)
    assert verify_otp_hash(otp, hashed) is True
    assert verify_otp_hash('999999', hashed) is False


def test_send_otp_mock_logs(capsys):
    send_otp('9876543210', '123456')
    captured = capsys.readouterr()
    assert '123456' in captured.out


@pytest.mark.django_db
def test_rate_limit_blocks_after_threshold(store):
    phone = '9876543210'
    service = OTPRateLimitService()
    # First 3 should pass
    for _ in range(3):
        service.check_rate_limit(phone)
        service.record_otp_request(phone)
    # 4th should raise
    with pytest.raises(RateLimitExceeded):
        service.check_rate_limit(phone)


@pytest.mark.django_db
def test_lockout_blocks_after_failed_attempts():
    phone = '9876543210'
    service = OTPRateLimitService()
    for _ in range(5):
        service.record_failed_attempt(phone)
    with pytest.raises(AccountLocked):
        service.check_lockout(phone)
