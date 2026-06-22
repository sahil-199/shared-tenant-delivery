import pytest
from unittest.mock import MagicMock
from apps.tenants.models import Store, TenantModel
from apps.tenants.mixins import TenantViewSetMixin


@pytest.mark.django_db
def test_store_creation(store):
    assert store.id is not None
    assert store.name == 'Test Hardware Store'
    assert store.is_active is True
    assert '400001' in store.delivery_pin_codes


@pytest.mark.django_db
def test_store_pin_code_check(store):
    assert store.is_pin_code_serviceable('400001') is True
    assert store.is_pin_code_serviceable('999999') is False


@pytest.mark.django_db
def test_tenant_mixin_filters_queryset(store):
    other_store = Store.objects.create(
        name='Other Store', slug='other-store', phone='1234567890', address='Other'
    )

    # TenantModel subclass for testing
    class MockModel(TenantModel):
        class Meta:
            app_label = 'tenants'

    mixin = TenantViewSetMixin()
    mixin.request = MagicMock()
    mixin.request.auth = {'tenant_id': store.id}

    assert mixin.get_tenant() == store


@pytest.mark.django_db
def test_get_tenant_raises_on_missing_id(store):
    mixin = TenantViewSetMixin()
    mixin.request = MagicMock()
    mixin.request.auth = {}

    with pytest.raises(ValueError):
        mixin.get_tenant()
