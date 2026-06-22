from django.core.management.base import BaseCommand
from apps.tenants.models import Store
from apps.authentication.models import User, CustomerProfile


class Command(BaseCommand):
    help = 'Create the initial store and owner account'

    def add_arguments(self, parser):
        parser.add_argument('--name', default='My Hardware Store')
        parser.add_argument('--slug', default='my-hardware-store')
        parser.add_argument('--phone', default='9999999999')
        parser.add_argument('--address', default='Enter store address')
        parser.add_argument('--pin-codes', default='400001', help='Comma-separated')
        parser.add_argument('--owner-phone', required=True, help='Owner mobile number')

    def handle(self, *args, **options):
        pin_codes = [p.strip() for p in options['pin_codes'].split(',')]

        store, created = Store.objects.get_or_create(
            slug=options['slug'],
            defaults={
                'name': options['name'],
                'phone': options['phone'],
                'address': options['address'],
                'delivery_pin_codes': pin_codes,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Store created: {store.name}'))
        else:
            self.stdout.write(f'Store already exists: {store.name}')

        owner, created = User.objects.get_or_create(
            phone=options['owner_phone'],
            defaults={'is_store_owner': True, 'is_staff': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Owner created: {owner.phone}'))
        else:
            self.stdout.write(f'Owner already exists: {owner.phone}')

        CustomerProfile.objects.get_or_create(user=owner, tenant=store)
        self.stdout.write(self.style.SUCCESS('Done. Login with OTP using the owner phone number.'))
