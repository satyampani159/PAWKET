// src/services/api.js
import { API_BASE } from './config';
export { API_BASE };

import { authHeaders } from './auth';

export async function checkConnection() {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function request(method, path, body = null, timeoutMs = 10000) {
  try {
    const headers = await authHeaders();
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    if (e.name === 'AbortError') {
      throw new Error(`Request timed out. Is the backend running at ${API_BASE}?`);
    }
    if (e.message.includes('Network request failed') || e.message.includes('fetch')) {
      throw new Error(
        `Cannot reach server at ${API_BASE}\n\n` +
        `Check:\n` +
        `1. Backend is running (py -m uvicorn main:app)\n` +
        `2. Phone and PC on same WiFi\n` +
        `3. IP is correct in api.js\n` +
        `4. Windows Firewall allows port 8000`
      );
    }
    throw e;
  }
}

export async function parseSMSBatch(items) {
  return request('POST', '/parse/batch', items);
}

export async function correctCategory(transactionId, correctCat) {
  return request('PATCH', '/correct', {
    transaction_id: transactionId,
    correct_category: correctCat,
  });
}

export async function getCategories() {
  return request('GET', '/correct/categories');
}

export async function getAnalytics(month) {
  return request('GET', `/analytics${month ? `?month=${month}` : ''}`);
}

export async function getTransactions({ month, category, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (month)    params.append('month', month);
  if (category) params.append('category', category);
  params.append('limit', limit);
  params.append('offset', offset);
  return request('GET', `/analytics/transactions?${params}`);
}

export async function getMonths() {
  return request('GET', '/analytics/months');
}

export async function getAdvice(month, income = null) {
  const params = new URLSearchParams();
  if (month)  params.append('month', month);
  if (income) params.append('income', income);
  return request('GET', `/advice?${params}`);
}

export async function getCompare(months) {
  const params = new URLSearchParams();
  params.append('months', months.join(','));
  return request('GET', `/analytics/compare?${params}`);
}

export async function sendChat(message, month, history = []) {
  const data = await request('POST', '/chat', { message, month, history }, 20000);
  if (typeof data === 'string') return data;
  return data?.reply ?? '';
}
