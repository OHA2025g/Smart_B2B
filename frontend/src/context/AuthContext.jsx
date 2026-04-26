import { createContext, useContext, useState, useEffect } from 'react';
import { authApi, AUTH_TOKEN_KEY, AUTH_USER_KEY } from '../api/client';

const AuthContext = createContext(null);

const LEGACY_USER_KEY = 'user';

async function fetchMeWithRetry(maxAttempts = 3) {
  let lastErr;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      return await authApi.me();
    } catch (e) {
      lastErr = e;
      const status = e.response?.status;
      if (status === 401 || status === 403) throw e;
      if (attempt < maxAttempts - 1) {
        await new Promise((r) => setTimeout(r, 350 * (attempt + 1)));
      }
    }
  }
  throw lastErr;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return undefined;
    }

    const raw = localStorage.getItem(AUTH_USER_KEY) || localStorage.getItem(LEGACY_USER_KEY);
    if (raw) {
      try {
        setUser(JSON.parse(raw));
      } catch {
        localStorage.removeItem(AUTH_USER_KEY);
        localStorage.removeItem(LEGACY_USER_KEY);
      }
    }

    let cancelled = false;
    fetchMeWithRetry()
      .then((res) => {
        if (cancelled) return;
        const u = res.data?.data?.user;
        if (u) {
          setUser(u);
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(u));
          localStorage.removeItem(LEGACY_USER_KEY);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        const status = err.response?.status;
        // Only drop session on real auth failures — not on network/CORS/5xx (those used to wipe token every refresh).
        if (status === 401 || status === 403) {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_USER_KEY);
          localStorage.removeItem(LEGACY_USER_KEY);
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = (userData, token) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(userData));
    localStorage.removeItem(LEGACY_USER_KEY);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(LEGACY_USER_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
