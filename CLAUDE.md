# Multi-Tenant Hardware & Sanitary Commerce Platform

## Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Auth — OTP + JWT | ✅ Complete |
| 2 | Store setup | ✅ Complete |
| 3 | Category system | ✅ Complete |
| 4 | Product catalog | ✅ Complete |
| 5 | Inventory | ✅ Complete |
| 6 | Product discovery | ✅ Complete |
| 7 | Cart | ✅ Complete |
| 8 | Checkout | ✅ Complete |
| 9 | Order management | ✅ Complete |
| 10 | Payments | ✅ Complete |

## Current Plan
Plan 1 complete. Plan 2 complete. Plan 3 complete (all 10 tasks done).
Next: Run migrations (`makemigrations cart orders payments` + `migrate`) once Docker is up, then smoke-test the full flow.

## Spec
docs/superpowers/specs/2026-06-20-platform-design.md

## Key Decisions
- Multi-tenancy: row-level isolation via tenant_id FK on every model
- Auth: OTP (phone) + JWT; SMS provider abstracted behind send_otp()
- Delivery: pin code allowlist now, lat/lng haversine later
- Payments: COD + Razorpay (test mode → live on KYC)
- No git commits in this project

## Running the project
```bash
cp .env.example .env   # fill in values
docker-compose up
```

Backend API: http://localhost:8000/api/v1/
API docs: http://localhost:8000/api/schema/swagger-ui/
Frontend: http://localhost:3000
```
