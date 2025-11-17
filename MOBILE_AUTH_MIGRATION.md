# Mobile App Authentication Migration Guide

## Summary
The BOMA mobile app has been migrated from Clerk authentication to a simple, self-hosted email/password JWT-based authentication system.

## Changes Made

### 1. Dependencies Removed
- `@clerk/clerk-expo` - No longer needed
- `expo-auth-session` - Not needed for basic email/password auth
- `expo-web-browser` - Not needed for basic email/password auth

### 2. Dependencies Kept
- `expo-secure-store` - For secure storage of JWT tokens
- `axios` - For API calls
- `zustand` - For state management
- All other Expo and React Native dependencies

## Required Code Changes

### 1. Remove Clerk Provider (mobile/App.tsx)
**Before:**
```tsx
import { ClerkProvider } from '@clerk/clerk-expo';

export default function App() {
  return (
    <ClerkProvider publishableKey={CLERK_KEY}>
      {/* app code */}
    </ClerkProvider>
  );
}
```

**After:**
```tsx
// No Clerk provider needed
export default function App() {
  return (
    <NavigationContainer>
      {/* app code */}
    </NavigationContainer>
  );
}
```

### 2. Update Auth Store (mobile/src/store/authStore.ts)
Create or update the auth store to manage JWT tokens:

```typescript
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { apiClient } from '../services/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_host: boolean;
  is_guest: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, phoneNumber: string) => Promise<void>;
  logout: () => Promise<void>;
  loadToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  isAuthenticated: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token, user } = response.data;

      // Save token securely
      await SecureStore.setItemAsync('auth_token', access_token);

      // Update API client with token
      apiClient.setAuthToken(access_token);

      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (email, password, full_name, phone_number) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        password,
        full_name,
        phone_number
      });

      // Auto-login after registration
      await useAuthStore.getState().login(email, password);
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('auth_token');
    apiClient.setAuthToken(null);
    set({ user: null, token: null, isAuthenticated: false });
  },

  loadToken: async () => {
    set({ isLoading: true });
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        apiClient.setAuthToken(token);
        // Fetch user profile
        const response = await apiClient.get('/users/me');
        set({
          user: response.data,
          token,
          isAuthenticated: true,
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      await SecureStore.deleteItemAsync('auth_token');
      set({ isLoading: false });
    }
  },
}));
```

### 3. Update API Client (mobile/src/services/api.ts)
The API client already exists and should handle JWT tokens properly. Ensure it:
- Adds `Authorization: Bearer {token}` header to all requests
- Has a `setAuthToken()` method
- Handles 401 errors by logging out the user

### 4. Create Auth Screens

#### Login Screen (mobile/src/screens/auth/LoginScreen.tsx)
```tsx
import React, { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';
import { useAuthStore } from '../../store/authStore';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuthStore();

  const handleLogin = async () => {
    try {
      await login(email, password);
      // Navigation will be handled by the auth state change
    } catch (err) {
      setError('Invalid email or password');
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text>Email:</Text>
      <TextInput
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <Text>Password:</Text>
      <TextInput
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      {error ? <Text style={{ color: 'red' }}>{error}</Text> : null}

      <Button title="Login" onPress={handleLogin} disabled={isLoading} />
      <Button title="Register" onPress={() => navigation.navigate('Register')} />
    </View>
  );
}
```

#### Register Screen (mobile/src/screens/auth/RegisterScreen.tsx)
```tsx
import React, { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';
import { useAuthStore } from '../../store/authStore';

export default function RegisterScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const { register, isLoading } = useAuthStore();

  const handleRegister = async () => {
    try {
      await register(email, password, fullName, phoneNumber);
      // Will auto-navigate after successful registration
    } catch (err) {
      setError('Registration failed. Please try again.');
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text>Full Name:</Text>
      <TextInput value={fullName} onChangeText={setFullName} />

      <Text>Email:</Text>
      <TextInput
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <Text>Phone Number:</Text>
      <TextInput
        value={phoneNumber}
        onChangeText={setPhoneNumber}
        keyboardType="phone-pad"
      />

      <Text>Password:</Text>
      <TextInput value={password} onChangeText={setPassword} secureTextEntry />

      {error ? <Text style={{ color: 'red' }}>{error}</Text> : null}

      <Button title="Register" onPress={handleRegister} disabled={isLoading} />
      <Button title="Back to Login" onPress={() => navigation.goBack()} />
    </View>
  );
}
```

### 5. Update Navigation (mobile/App.tsx)
```tsx
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from './src/store/authStore';

import LoginScreen from './src/screens/auth/LoginScreen';
import RegisterScreen from './src/screens/auth/RegisterScreen';
// ... other screens

const Stack = createNativeStackNavigator();

export default function App() {
  const { isAuthenticated, loadToken } = useAuthStore();

  useEffect(() => {
    loadToken(); // Load stored token on app start
  }, []);

  return (
    <NavigationContainer>
      <Stack.Navigator>
        {!isAuthenticated ? (
          // Auth Stack
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        ) : (
          // App Stack (your existing screens)
          <>
            <Stack.Screen name="Home" component={HomeScreen} />
            {/* ... other authenticated screens */}
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

## Testing the Migration

1. **Install dependencies:**
   ```bash
   cd mobile
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Test Registration:**
   - Launch the app
   - Navigate to Register screen
   - Create a new account
   - Verify token is stored in SecureStore

3. **Test Login:**
   - Logout
   - Login with registered credentials
   - Verify navigation to main app

4. **Test Token Persistence:**
   - Close and reopen the app
   - Verify user stays logged in

5. **Test Logout:**
   - Click logout button
   - Verify token is deleted
   - Verify navigation to login screen

## Environment Variables

Update mobile `.env` file:
```env
# Remove Clerk key
# EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=...

# Add API URL
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Benefits of This Approach

✅ **No external dependencies** - Complete control over auth flow
✅ **Lower costs** - No Clerk subscription needed
✅ **Simpler codebase** - Less abstraction, easier to debug
✅ **Faster development** - No waiting for Clerk API responses
✅ **Better offline support** - JWT stored locally
✅ **More flexible** - Easy to customize auth logic

## Security Considerations

✅ Tokens stored in SecureStore (encrypted on device)
✅ HTTPS communication with backend
✅ Tokens expire after 30 minutes (refresh logic can be added)
✅ Password hashing handled server-side with bcrypt

## Next Steps (Optional Enhancements)

1. **Token Refresh**: Implement refresh token logic to avoid re-login
2. **Password Reset**: Add forgot password flow with email
3. **Social Login**: Add Google/Facebook OAuth later if needed
4. **Biometric Auth**: Use expo-local-authentication for fingerprint/face unlock
5. **Session Management**: Add "remember me" functionality
