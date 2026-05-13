import { API_BASE } from '../config/api';

const PRIMARY_TOKEN_KEY = 'taaip_auth_token';
const TOKEN_KEYS = [PRIMARY_TOKEN_KEY, 'auth_token', 'token'];
const PERSPECTIVE_KEY = 'taaip_perspective';

let pendingTokenPromise: Promise<string | null> | null = null;

type LoginResponse = {
  token?: string;
};

function readTokenFromStorage(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  for (const key of TOKEN_KEYS) {
    const value = window.localStorage.getItem(key);
    if (value && value.trim()) {
      return value.trim();
    }
  }
  return null;
}

function writeTokenToStorage(token: string): void {
  if (typeof window === 'undefined' || !token) {
    return;
  }
  window.localStorage.setItem(PRIMARY_TOKEN_KEY, token);
}

function perspectiveLoginCandidates(): string[] {
  if (typeof window === 'undefined') {
    return ['usarec_admin', 'admin', 'dev.user'];
  }
  const perspective = (window.localStorage.getItem(PERSPECTIVE_KEY) || '').toLowerCase();
  const base = ['usarec_admin', 'admin', 'dev.user', 'commander', 'operator420t', '420t_admin'];
  if (perspective === 'operator420t') {
    return ['operator420t', '420t_admin', ...base];
  }
  if (perspective === 'admin') {
    return ['admin', 'usarec_admin', ...base];
  }
  return ['usarec_admin', 'commander', ...base];
}

async function loginForToken(username: string): Promise<string | null> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username }),
  });
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json().catch(() => null)) as LoginResponse | null;
  const token = (payload?.token || '').trim();
  return token || null;
}

export async function ensureAuthToken(): Promise<string | null> {
  const existing = readTokenFromStorage();
  if (existing) {
    return existing;
  }

  if (!pendingTokenPromise) {
    pendingTokenPromise = (async () => {
      const usernames = Array.from(new Set(perspectiveLoginCandidates()));
      for (const username of usernames) {
        try {
          const token = await loginForToken(username);
          if (token) {
            writeTokenToStorage(token);
            return token;
          }
        } catch {
          // Keep trying alternate usernames.
        }
      }
      return null;
    })().finally(() => {
      pendingTokenPromise = null;
    });
  }

  return pendingTokenPromise;
}

export async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = await ensureAuthToken();
  const headers = new Headers(init.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(input, {
    ...init,
    headers,
    credentials: init.credentials || 'include',
  });
}
