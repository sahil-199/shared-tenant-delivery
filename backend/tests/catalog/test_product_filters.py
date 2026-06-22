import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import Inventory


@pytest.mark.django_db
def test_search_by_name(store, category):
    Product.objects.create(tenant=store, category=category, name='Ball Valve', slug='ball-valve')
    Product.objects.create(tenant=store, category=category, name='Gate Valve', slug='gate-valve')
    res = APIClient().get('/api/v1/products/?search=ball')
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]['slug'] == 'ball-valve'


@pytest.mark.django_db
def test_search_by_description(store, category):
    Product.objects.create(
        tenant=store, category=category, name='Pipe', slug='pipe-desc',
        description='high pressure industrial fitting'
    )
    Product.objects.create(tenant=store, category=category, name='Valve', slug='valve-desc')
    res = APIClient().get('/api/v1/products/?search=industrial')
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_filter_in_stock(store, category):
    p_in = Product.objects.create(tenant=store, category=category, name='In Stock', slug='in-stock')
    v_in = ProductVariant.objects.create(product=p_in, name='A', sku='IN-A', price=Decimal('10'))
    Inventory.objects.create(tenant=store, variant=v_in, available_qty=5, reserved_qty=0)

    p_out = Product.objects.create(tenant=store, category=category, name='Out Stock', slug='out-stock')
    v_out = ProductVariant.objects.create(product=p_out, name='B', sku='OUT-B', price=Decimal('10'))
    Inventory.objects.create(tenant=store, variant=v_out, available_qty=0, reserved_qty=0)

    res = APIClient().get('/api/v1/products/?in_stock=true')
    slugs = [d['slug'] for d in res.json()]
    assert 'in-stock' in slugs
    assert 'out-stock' not in slugs


@pytest.mark.django_db
def test_sort_price_asc(store, category):
    p1 = Product.objects.create(tenant=store, category=category, name='Cheap', slug='cheap')
    ProductVariant.objects.create(product=p1, name='A', sku='CH-A', price=Decimal('10'))
    p2 = Product.objects.create(tenant=store, category=category, name='Expensive', slug='expensive')
    ProductVariant.objects.create(product=p2, name='B', sku='EX-B', price=Decimal('100'))

    res = APIClient().get('/api/v1/products/?sort=price_asc')
    slugs = [d['slug'] for d in res.json()]
    assert slugs.index('cheap') < slugs.index('expensive')


@pytest.mark.django_db
def test_sort_price_desc(store, category):
    p1 = Product.objects.create(tenant=store, category=category, name='Cheap2', slug='cheap2')
    ProductVariant.objects.create(product=p1, name='A', sku='CH2-A', price=Decimal('10'))
    p2 = Product.objects.create(tenant=store, category=category, name='Pricey2', slug='pricey2')
    ProductVariant.objects.create(product=p2, name='B', sku='PR2-B', price=Decimal('200'))

    res = APIClient().get('/api/v1/products/?sort=price_desc')
    slugs = [d['slug'] for d in res.json()]
    assert slugs.index('pricey2') < slugs.index('cheap2')
