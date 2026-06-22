### Task 11: Login Page — OTP Flow UI

**Files:**
- Create: `frontend/app/(auth)/login/page.tsx`
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/app/(store)/page.tsx`

**Interfaces:**
- Consumes: `apiFetch` from `@/lib/api`, `useAuthStore` from `@/store/auth`, `Button` and `Input` from `@/components/ui/`
- Produces: Working OTP login flow — enter phone → receive OTP → enter OTP → redirect to home

- [ ] **Step 1: Write login page**

`frontend/app/(auth)/login/page.tsx`:
```typescript
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

type Step = 'phone' | 'otp';

interface OTPVerifyResponse {
  access_token: string;
  refresh_token: string;
  is_new_user: boolean;
}

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handlePhoneSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiFetch('/api/v1/auth/otp/request/', {
        method: 'POST',
        body: JSON.stringify({ phone }),
      });
      setStep('otp');
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'phone' in err
        ? (err as { phone: string[] }).phone[0]
        : 'Failed to send OTP. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleOtpSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch<OTPVerifyResponse>('/api/v1/auth/otp/verify/', {
        method: 'POST',
        body: JSON.stringify({ phone, otp }),
      });
      // Decode phone from token payload (base64 middle segment)
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      setAuth(
        { phone: payload.phone, isStoreOwner: payload.is_store_owner },
        data.access_token,
        data.refresh_token,
      );
      router.push('/');
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'non_field_errors' in err
        ? (err as { non_field_errors: string[] }).non_field_errors[0]
        : 'Invalid OTP. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome</h1>
        <p className="text-gray-500 text-sm mb-8">
          {step === 'phone' ? 'Enter your mobile number to continue' : `Enter the OTP sent to ${phone}`}
        </p>

        {step === 'phone' ? (
          <form onSubmit={handlePhoneSubmit} className="flex flex-col gap-4">
            <Input
              label="Mobile Number"
              type="tel"
              placeholder="9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={10}
              inputMode="numeric"
              error={error}
              required
            />
            <Button type="submit" loading={loading} className="w-full">
              Send OTP
            </Button>
          </form>
        ) : (
          <form onSubmit={handleOtpSubmit} className="flex flex-col gap-4">
            <Input
              label="OTP"
              type="text"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              maxLength={6}
              inputMode="numeric"
              error={error}
              required
            />
            <Button type="submit" loading={loading} className="w-full">
              Verify OTP
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => { setStep('phone'); setError(''); setOtp(''); }}
            >
              Change number
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write root layout**

`frontend/app/layout.tsx`:
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Hardware & Sanitary Store',
  description: 'Quality hardware, sanitary, and construction materials delivered to your door.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 3: Write home placeholder**

`frontend/app/(store)/page.tsx`:
```typescript
export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <p className="text-gray-500">Store coming soon — Phase 3+</p>
    </main>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 5: Start the dev server and verify login page loads**

```bash
# Ensure .env is populated and Docker Compose is running, then:
cd frontend && npm run dev
```
Open http://localhost:3000/login — confirm the phone entry form renders.
Open http://localhost:8000/api/schema/swagger-ui/ — confirm API docs render.

---

