import pytest
from apps.authentication.tokens import TenantRefreshToken


@pytest.mark.django_db
def test_token_contains_tenant_id(store):
    from apps.authentication.models import User
    user = User.objects.create_user(phone='9876543210')

    refresh = TenantRefreshToken.for_user_and_store(user, store)
    access = refresh.access_token

    assert access['tenant_id'] == store.id
    assert access['phone'] == '9876543210'
    assert access['is_store_owner'] is False
    assert 'user_id' in access
