# Multi-Tenant Hardware & Sanitary Commerce Platform — Design Spec

**Date:** 2026-06-20
**Scope:** Phase 1–10 (Auth through Payments)
**Stack:** Django DRF + PostgreSQL + Redis + Celery / Next.js 14 + TypeScript + TailwindCSS

---

## 1. Project Structure

Monorepo, strict API separation. Backend is pure JSON API. Frontend is pure consumer.

```
/
├── backend/
├── frontend/
├── docker-compose.yml
├── .env.example          # all keys documented, no values
├── .env                  # on server only, never committed, chmod 600
└── CLAUDE.md             # progress tracking
```

Secrets: `.env` file on server only. Never committed to git. Documented via `.env.example`.

---

## 2. Backend — Django App Structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── tenants/          # Store, StoreSettings, tenant middleware
    ├── authentication/   # User, CustomerProfile, OTP, JWT
    ├── catalog/          # Category, Product, ProductVariant, Brand, ProductImage
    ├── inventory/        # Inventory, InventoryMovement
    ├── cart/             # Cart, CartItem
    ├── orders/           # Order, OrderItem, Address
    └── payments/         # Payment, Refund
```

API prefix: `/api/v1/` — versioned from day one.
OpenAPI docs: auto-generated via `drf-spectacular`.

---

## 3. Multi-Tenancy

**Strategy:** Row-level isolation. Every tenant-scoped model extends `TenantModel` (abstract), which carries `tenant_id` as a FK to `Store`.

**Tenant middleware:** On every authenticated request, `tenant_id` is read from the JWT claim and attached to `request.tenant`. All querysets in tenant-scoped views are filtered by `request.tenant` automatically via a base viewset mixin.

Single store initially. Architecture ready for multiple stores with no schema changes.

---

## 4. Data Models

### tenants

```
Store
├── id, name, slug, phone, address
├── logo (R2 URL)
├── delivery_pin_codes: ArrayField[str]   # serviceable pin codes
├── delivery_radius_km: int               # reserved for future lat/lng validation
└── is_active: bool
```

### authentication

```
User (custom, extends AbstractBaseUser)
├── phone: unique                         # primary identifier
├── email: optional                       # for receipts if provided
├── full_name: optional
├── is_store_owner: bool
└── is_active: bool

CustomerProfile
├── FK → User
├── FK → Store (tenant-scoped)
└── created_at

OTPVerification
├── phone
├── otp_hash                              # bcrypt, never plaintext
├── expires_at                            # 5 min from creation
├── is_used: bool
└── attempt_count: int
```

### catalog

```
Category
├── FK → Store (tenant)
├── name, slug, image
├── parent: FK → self (nullable)          # unlimited nesting, adjacency list
└── is_active: bool

Brand
├── FK → Store (tenant)
├── name, slug, logo
└── is_active: bool

Product
├── FK → Store, Category, Brand
├── name, slug, description
├── specifications: JSONField             # arbitrary key-value, no migrations per type
└── is_active: bool

ProductVariant
├── FK → Product
├── name (e.g. "1 inch", "12 inch")
├── sku: unique per store
├── price, sale_price (nullable)
└── is_active: bool

ProductImage
├── FK → Product
├── FK → ProductVariant (nullable)        # variant-specific or product-level
├── image_url (R2 URL)
└── sort_order: int
```

### inventory

```
Inventory
├── FK → ProductVariant, Store
├── available_qty: int
└── reserved_qty: int
# sold quantity = sum of InventoryMovement with reason=SOLD

InventoryMovement
├── FK → Inventory
├── delta: int (positive or negative)
├── reason: RESTOCK | RESERVE | RELEASE | SELL | ADJUSTMENT
└── created_at
```

**Stock state machine:**
- Order placed → `available_qty -= qty`, `reserved_qty += qty`
- Order cancelled → `reserved_qty -= qty`, `available_qty += qty`
- Order delivered → `reserved_qty -= qty` + InventoryMovement(reason=SELL)

### orders

```
Address
├── FK → User, Store (tenant)
├── line1, line2, city, state
├── pin_code
├── lat, lng (nullable)                   # reserved for future lat/lng validation
└── is_default: bool

Cart
└── FK → User, Store (tenant)

CartItem
├── FK → Cart, ProductVariant
└── qty: int

Order
├── FK → User, Store, Address
├── status: PLACED | PENDING_CONFIRMATION | CONFIRMED | PROCESSING |
│          OUT_FOR_DELIVERY | DELIVERED | CANCELLED
├── total_amount
├── notes (customer notes, optional)
└── created_at

OrderItem
├── FK → Order, ProductVariant
├── qty: int
├── unit_price                            # snapshot at time of order
└── variant_name                          # snapshot at time of order
```

### payments

```
Payment
├── FK → Order
├── method: COD | RAZORPAY
├── status: PENDING | COMPLETED | FAILED | REFUNDED
├── gateway_ref (Razorpay order/payment ID)
└── amount

Refund
├── FK → Payment
├── amount, reason, status
└── gateway_ref
```

---

## 5. Auth Flow

```
POST /api/v1/auth/otp/request/
  body: { phone }
  → rate limited: max 3 requests per phone per 10 min (Redis)
  → generates 6-digit OTP, bcrypt hash stored, expiry 5 min
  → dev: OTP logged to console
  → prod: send_otp(phone, otp) in authentication/services.py (swap provider here)

POST /api/v1/auth/otp/verify/
  body: { phone, otp }
  → max 5 failed attempts before 15-min lockout
  → on success: creates User + CustomerProfile if new user
  → returns { access_token, refresh_token, is_new_user }

POST /api/v1/auth/token/refresh/
  body: { refresh_token }
  → returns new access_token

JWT payload: { user_id, tenant_id, phone, is_store_owner }
JWT access token expiry: 1 hour
JWT refresh token expiry: 30 days
```

SMS provider abstraction: single function `send_otp(phone: str, otp: str)` in `apps/authentication/services.py`. Swap body to change provider, nothing else changes.

---

## 6. API Endpoints

```
# Auth (public)
POST   /api/v1/auth/otp/request/
POST   /api/v1/auth/otp/verify/
POST   /api/v1/auth/token/refresh/

# Store
GET    /api/v1/store/
PATCH  /api/v1/store/                     # owner only

# Categories
GET    /api/v1/categories/                # ?format=tree (nested JSON) or flat list with parent_id (default)
POST   /api/v1/categories/               # owner only
PATCH  /api/v1/categories/{id}/
DELETE /api/v1/categories/{id}/

# Brands
GET    /api/v1/brands/
POST   /api/v1/brands/                   # owner only
PATCH  /api/v1/brands/{id}/
DELETE /api/v1/brands/{id}/

# Products
GET    /api/v1/products/                 # ?search= ?category= ?brand= ?min_price= ?max_price= ?in_stock= ?sort=price_asc|price_desc|newest
GET    /api/v1/products/{slug}/
POST   /api/v1/products/                 # owner only
PATCH  /api/v1/products/{id}/
GET    /api/v1/products/{id}/variants/

# Inventory (owner only)
GET    /api/v1/inventory/
PATCH  /api/v1/inventory/{variant_id}/
GET    /api/v1/inventory/movements/

# Cart (authenticated)
GET    /api/v1/cart/
POST   /api/v1/cart/items/
PATCH  /api/v1/cart/items/{id}/
DELETE /api/v1/cart/items/{id}/

# Addresses
GET    /api/v1/addresses/
POST   /api/v1/addresses/
PATCH  /api/v1/addresses/{id}/
DELETE /api/v1/addresses/{id}/

# Orders
POST   /api/v1/orders/                   # checkout: validates pin code, reserves inventory
GET    /api/v1/orders/                   # customer: own; owner: all
GET    /api/v1/orders/{id}/
PATCH  /api/v1/orders/{id}/status/       # owner only

# Payments
POST   /api/v1/payments/initiate/        # creates Razorpay order or COD record
POST   /api/v1/payments/webhook/         # Razorpay callback (async via Celery)
POST   /api/v1/payments/cod/confirm/     # owner confirms COD receipt
```

---

## 7. Delivery Validation

**Phase 1–10 (current):** Pin code allowlist on `Store.delivery_pin_codes`. On checkout, address `pin_code` checked against this list. If not found → 400 with message "Delivery not available to this pin code."

**Future (post Phase 10):** Lat/lng geocoding via Nominatim + Haversine check against `Store.delivery_radius_km`. `Address.lat` and `Address.lng` fields are already in schema.

---

## 8. Payment Flow

**Recommended flow (avoids refund complexity at launch):**
1. Customer places order → status: PLACED
2. Owner reviews + confirms → status: CONFIRMED, WhatsApp sent to customer
3. Customer pays → status moves forward

**COD:** Payment confirmed by owner on delivery.
**Razorpay (UPI / cards / netbanking):** Single Razorpay integration. Built in test mode from day one. Goes live when Razorpay KYC approves (2–5 business days). One env var: `RAZORPAY_MODE=live`.

---

## 9. Notifications

**WhatsApp provider:** To be selected before Phase 9. Recommended options for India: Interakt, WATI, Gupshup. All expose a similar REST API — abstracted behind a single `send_whatsapp(phone, template, params)` function in `apps/notifications/services.py`.

**WhatsApp (primary — reaches all users):**
- Order placed (to customer + store owner)
- Order confirmed (to customer)
- Out for delivery (to customer)
- Order delivered (to customer)

**Email (secondary — only if user.email is set):**
- Order confirmation with order summary

**Receipt:** Always visible on order detail page in UI. WhatsApp message contains full order details (items, total, address). No PDF generation.

---

## 10. Frontend Architecture

```
frontend/
├── app/
│   ├── (store)/
│   │   ├── page.tsx                      # home / product discovery
│   │   ├── products/
│   │   │   ├── page.tsx                  # listing + filters
│   │   │   └── [slug]/page.tsx           # product detail + variant selector
│   │   ├── cart/page.tsx
│   │   ├── checkout/page.tsx
│   │   ├── orders/
│   │   │   ├── page.tsx                  # order history
│   │   │   └── [id]/page.tsx             # order detail + receipt
│   │   └── account/page.tsx              # profile, addresses
│   ├── (auth)/
│   │   └── login/page.tsx                # OTP flow
│   ├── admin/                            # owner-facing (extensible, minimal for Phase 1–10)
│   │   ├── products/
│   │   ├── orders/
│   │   └── inventory/
│   └── layout.tsx
├── components/
│   ├── ui/                               # Button, Input, Badge, Sheet, Modal
│   ├── product/                          # ProductCard, ProductGrid, VariantSelector
│   ├── cart/                             # CartDrawer, CartItem
│   ├── checkout/                         # AddressForm, PaymentSelector
│   └── order/                            # OrderCard, OrderTimeline
├── lib/
│   ├── api.ts                            # typed fetch wrapper, auto token refresh
│   ├── auth.ts                           # token storage + refresh logic
│   └── hooks/                            # useCart, useAuth, useOrders
└── store/                                # Zustand: cart + auth client state
```

**Rendering strategy:**
- Product listing + detail pages: Server Components (fast load, SEO)
- Cart, checkout, auth: Client Components (interactive)

**UI principles:** Mobile-first, TailwindCSS only (no component library), large touch targets, minimal clicks to checkout.

---

## 11. Infrastructure

```yaml
# docker-compose.yml services
db       # PostgreSQL 16
redis    # Redis 7 (cache + Celery broker)
backend  # Django (gunicorn prod / runserver dev)
celery   # Celery worker (notifications, async tasks)
frontend # Next.js
nginx    # reverse proxy (prod only)
```

**Storage:** Cloudflare R2 via `django-storages` (S3-compatible). Swap to Backblaze B2 with 3 env var changes.

**No Celery beat needed for Phase 1–10** — only async worker tasks (notifications, webhook processing).

---

## 12. Phase Delivery Sequence

| Phase | Deliverable | Depends On |
|-------|-------------|------------|
| 1 | Auth — OTP + JWT | — |
| 2 | Store setup — model + settings | 1 |
| 3 | Category system — unlimited nesting | 2 |
| 4 | Product catalog — products, variants, images, brands | 3 |
| 5 | Inventory — stock tracking + movement audit | 4 |
| 6 | Product discovery — search + filters | 5 |
| 7 | Cart — persistent, add/remove/update | 6 |
| 8 | Checkout — address + pin code delivery validation | 7 |
| 9 | Order management — state machine + WhatsApp notifications | 8 |
| 10 | Payments — COD live + Razorpay (test → live on KYC) | 9 |

---

## 13. Security Constraints

- OTP: 5 min expiry, single use, bcrypt hashed
- Rate limiting: 3 OTP requests / 10 min per phone (Redis)
- Lockout: 5 failed OTP verify attempts → 15 min lockout
- All tenant queries filtered by `tenant_id` via base viewset mixin
- JWT: 1h access / 30d refresh
- `.env` on server only, `chmod 600`, never committed
- Razorpay webhook signature verified before processing
- Input validation at all API boundaries

---

## 14. Non-Functional Targets

- API response time: < 300ms p95
- Product catalog: supports 10,000+ products
- Test coverage: 80%+ (unit + integration)
- Architecture: Service layer + Repository pattern in Django apps
