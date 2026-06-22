import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.orders.models import Order, Address
from apps.payments.models import Payment


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='8000000001')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def user_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.fixture
def placed_order(store, user, db):
    addr = Address.objects.create(
        tenant=store, user=user,
        line1='10 Park St', city='Mumbai', state='MH', pin_code='400001',
    )
    return Order.objects.create(
        tenant=store,
        user=user,
        address=addr,
        status=Order.PLACED,
        total_amount=Decimal('500.00'),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cod_payment_initiates_and_confirms_order(user_client, placed_order):
    """COD: payment is created with status=paid and order transitions to CONFIRMED."""
    res = user_client.post(
        '/api/v1/payments/initiate/',
        {'order_id': placed_order.id, 'method': 'cod'},
        format='json',
    )
    assert res.status_code == 201, res.json()

    data = res.json()
    assert data['method'] == 'cod'
    assert data['status'] == 'paid'

    payment = Payment.objects.get(id=data['id'])
    assert payment.status == 'paid'
    assert payment.amount == Decimal('500.00')

    placed_order.refresh_from_db()
    assert placed_order.status == Order.PENDING_CONFIRMATION


@pytest.mark.django_db
def test_razorpay_payment_creates_razorpay_order(user_client, placed_order):
    """Razorpay: payment is created with status=initiated and razorpay_order_id set."""
    mock_rp_order = {'id': 'order_test_abc123'}

    with patch('apps.payments.views.razorpay.Client') as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        mock_client_instance.order.create.return_value = mock_rp_order

        res = user_client.post(
            '/api/v1/payments/initiate/',
            {'order_id': placed_order.id, 'method': 'razorpay'},
            format='json',
        )

    assert res.status_code == 201, res.json()

    data = res.json()
    assert data['status'] == 'initiated'
    assert data['razorpay_order_id'] == 'order_test_abc123'
    assert 'razorpay_key' in data

    payment = Payment.objects.get(id=data['id'])
    assert payment.razorpay_order_id == 'order_test_abc123'
    assert payment.status == 'initiated'

    # Order should still be PLACED (not yet confirmed — waits for webhook)
    placed_order.refresh_from_db()
    assert placed_order.status == Order.PLACED


@pytest.mark.django_db
def test_duplicate_payment_rejected(user_client, placed_order, store):
    """Second initiate call for the same order returns 400."""
    # Create first payment manually
    Payment.objects.create(
        tenant=store,
        order=placed_order,
        method='cod',
        status='paid',
        amount=placed_order.total_amount,
    )

    res = user_client.post(
        '/api/v1/payments/initiate/',
        {'order_id': placed_order.id, 'method': 'cod'},
        format='json',
    )
    assert res.status_code == 400
    assert 'already initiated' in res.json().get('detail', '').lower()


@pytest.mark.django_db
def test_invalid_order_returns_404(user_client):
    """Initiating payment for a non-existent order returns 404."""
    res = user_client.post(
        '/api/v1/payments/initiate/',
        {'order_id': 999999, 'method': 'cod'},
        format='json',
    )
    assert res.status_code == 404
