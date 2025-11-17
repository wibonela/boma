# Quick Fix: Authentication Bypass for Testing

## Problem
Mobile app can't create bookings because:
1. Backend requires Clerk authentication
2. Mobile app doesn't have Clerk integration yet
3. No auth token = network error

## Temporary Solution (Development Only)

Create a test user and use a simple dev token bypass.

### Step 1: Create Test User in Database

Run this script:

```bash
cd /Users/walid/Desktop/TheFILES/boma/backend
python backend/create_test_user.py
```

This creates a test user with:
- ID: `test-user-123`
- Email: test@boma.co.tz
- Role: guest

### Step 2: Update Mobile App to Send Dev Token

Add to `mobile/src/api/client.ts`:

```typescript
// DEVELOPMENT ONLY - Remove before production
if (__DEV__) {
  this.setAuthToken('dev-bypass-token');
}
```

### Step 3: Add Dev Auth Bypass in Backend

Already done - the `/bookings` endpoint now accepts a special dev token in development mode.

## Next Steps (Proper Fix)

1. Set up Clerk in mobile app (see docs)
2. Add ClerkProvider to App.tsx
3. Use useAuth() hook to get real tokens
4. Remove dev bypass code

## Test the Fix

1. Restart backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Restart mobile app:
   ```bash
   cd mobile
   npx expo start --clear
   ```

3. Try creating a booking - should work now!
