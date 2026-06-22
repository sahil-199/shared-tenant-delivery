### Task 12: Create Initial Store via Management Command

**Files:**
- Create: `backend/apps/tenants/management/__init__.py`
- Create: `backend/apps/tenants/management/commands/__init__.py`
- Create: `backend/apps/tenants/management/commands/create_store.py`

**Interfaces:**
- Produces: `python manage.py create_store` — creates the first store and a superuser/owner

- [ ] **Step 1: Write management command**

`backend/apps/tenants/management/commands/create_store.py`:
```python
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
            owner.is_store_owner = True
            owner.is_staff = True
            owner.save()
            self.stdout.write(self.style.SUCCESS(f'Owner created: {owner.phone}'))

        CustomerProfile.objects.get_or_create(user=owner, tenant=store)
        self.stdout.write(self.style.SUCCESS('Done. Login with OTP using the owner phone number.'))
```

- [ ] **Step 2: Run the command**

```bash
cd backend && python manage.py create_store \
  --name "Sahil Hardware" \
  --slug "sahil-hardware" \
  --owner-phone "9876543210" \
  --pin-codes "400001,400002,400003"
```
Expected: `Store created: Sahil Hardware` + `Owner created: 9876543210`

---

## End-to-End Smoke Test

After all tasks complete, run this sequence to confirm the full auth + store flow works:

- [ ] Start Docker Compose: `docker-compose up -d`
- [ ] Run migrations: `docker-compose exec backend python manage.py migrate`
- [ ] Create store: `docker-compose exec backend python manage.py create_store --owner-phone 9876543210 --pin-codes 400001,400002`
- [ ] Request OTP (check backend logs for OTP value since mock): `curl -X POST http://localhost:8000/api/v1/auth/otp/request/ -H "Content-Type: application/json" -d '{"phone":"9876543210"}'`
- [ ] Verify OTP: `curl -X POST http://localhost:8000/api/v1/auth/otp/verify/ -H "Content-Type: application/json" -d '{"phone":"9876543210","otp":"<from-logs>"}'`
- [ ] Get store: `curl http://localhost:8000/api/v1/store/`
- [ ] Open http://localhost:3000/login and complete OTP login in browser

Expected: JWT tokens returned, store info returned, browser login succeeds and redirects to `/`
