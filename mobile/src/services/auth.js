// src/services/auth.js
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from './config';

const TOKEN_KEY = '@finance_token';
const USER_KEY  = '@finance_user';

export async function saveToken(token) {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function getToken() {
  return await AsyncStorage.getItem(TOKEN_KEY);
}

export async function saveUser(user) {
  await AsyncStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function getSavedUser() {
  const raw = await AsyncStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function clearAuth() {
  await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
}

export async function authHeaders() {
  const token = await getToken();
  return {
    'Content-Type':  'application/json',
    'Authorization': `Bearer ${token || ''}`,
  };
}

async function authRequest(path, options = {}) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return res.json();
  } catch (e) {
    if (e.name === 'AbortError') {
      throw new Error(`Connection timed out. Backend not reachable at ${API_BASE}`);
    }
    throw new Error(
      `Network error: ${e.message}\n\nMake sure:\n` +
      `• Backend is running\n• Same WiFi\n• IP is ${API_BASE}`
    );
  }
}

export async function requestOTP(phone) {
  return authRequest('/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOTP(phone, otp) {
  return authRequest('/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, otp }),
  });
}

export async function getMe() {
  const headers = await authHeaders();
  return authRequest('/auth/me', { headers });
}

export async function updateSyncStatus(syncedCount) {
  const headers = await authHeaders();
  return authRequest('/auth/sync-status', {
    method: 'POST',
    headers,
    body: JSON.stringify({ user_id: 0, synced_count: syncedCount }),
  });
}

export async function logout() {
  try {
    const headers = await authHeaders();
    await authRequest('/auth/logout', { method: 'DELETE', headers });
  } catch {}
  await clearAuth();
}
