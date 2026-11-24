'use client';
import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { fetchWithAuth } from '../lib/apiClient';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState('initializing'); // 'initializing' | 'authenticated' | 'unauthenticated' | 'offline'
  const router = useRouter();
  const queryClient = useQueryClient();

  const handleOffline = (retryCount) => {
    if (status !== 'offline') {
      console.log('[DEBUG] AuthContext: Transitioning to offline state');
      setStatus('offline');
      // Set a fallback session so components don't crash if they assume session exists
      setSession((prev) => prev || { access_token: localStorage.getItem('access_token'), user: {}, offline: true });
    }
    
    // Silently poll the Next.js /ping route instead of /api/auth/me
    const pollBackend = async () => {
      try {
        const res = await fetch('/ping');
        const data = await res.json();
        
        if (data.status === 'ok') {
          console.log('[DEBUG] AuthContext: Backend is back online. Restoring session...');
          fetchUser(0);
        } else {
          setTimeout(pollBackend, 3000);
        }
      } catch (err) {
        setTimeout(pollBackend, 3000);
      }
    };

    setTimeout(pollBackend, 3000);
  };

  const fetchUser = async (retryCount = 0) => {
    try {
      console.log('[DEBUG] AuthContext: checking /api/auth/me');
      const res = await fetchWithAuth('/api/auth/me');
      if (res.ok) {
        const data = await res.json();
        setSession({
          access_token: localStorage.getItem('access_token'),
          user: data.data
        });
        console.log('[DEBUG] AuthContext: Transitioning to authenticated');
        setStatus('authenticated');
      } else if (res.status === 401 || res.status === 403) {
        console.log(`[DEBUG] AuthContext: /me returned ${res.status}. Transitioning to unauthenticated`);
        console.warn('Session expired or invalid. Redirecting to login.');
        logout(false);
      } else {
        handleOffline(retryCount);
      }
    } catch (error) {
      if (error.message === 'invalid_token') {
        console.log('[DEBUG] AuthContext: Proactive refresh failed. Transitioning to unauthenticated');
        logout(false);
      } else {
        handleOffline(retryCount);
      }
    }
  };

  useEffect(() => {
    console.log('[DEBUG] AuthContext: initializing');
    const token = localStorage.getItem('access_token');
    const hasLoggedIn = localStorage.getItem('has_logged_in');
    
    if (token || hasLoggedIn) {
      fetchUser();
    } else {
      console.log('[DEBUG] AuthContext: No token found. Transitioning to unauthenticated');
      setStatus('unauthenticated');
    }

    const handleStorageChange = (e) => {
      if (e.key === 'has_logged_in' && !e.newValue) {
        logout(false);
      } else if (e.key === 'has_logged_in' && e.newValue) {
        fetchUser();
      }
    };

    const handleAuthLogout = () => {
      logout(false);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('auth-logout', handleAuthLogout);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('auth-logout', handleAuthLogout);
    };
  }, []);

  const login = async (access_token) => {
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('has_logged_in', 'true');
    setStatus('initializing');
    await fetchUser();
  };

  const logout = async (callApi = true) => {
    // 1. Immediately purge local state so UI updates instantly
    localStorage.removeItem('access_token');
    localStorage.removeItem('has_logged_in');
    sessionStorage.clear();
    setSession(null);
    setStatus('unauthenticated');
    queryClient.clear();

    // 2. Fire backend logout in background without blocking the UI redirect
    if (callApi) {
      fetchWithAuth('/api/auth/logout', { method: 'POST' }).catch((err) => {
        console.error('Logout API failed', err);
      });
    }

    // 3. Immediately route to login
    router.replace('/login');
  };

  const logoutAll = async () => {
    try {
      await fetchWithAuth('/api/auth/logout-all', { method: 'POST' });
    } catch (err) {
      console.error('Logout all API failed', err);
    }
    logout(false);
  };

  // Keep loading boolean for backwards compatibility with other components
  const loading = status === 'initializing';

  return (
    <AuthContext.Provider value={{ session, setSession, loading, status, login, logout, logoutAll }}>
      {children}
      {status === 'offline' && (
        <div className="fixed bottom-6 right-6 z-[9999] bg-neutral-900/90 backdrop-blur-md border border-neutral-800 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-5 fade-in duration-300">
          <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-purple-500 animate-spin" />
          <span className="text-sm font-medium">Reconnecting to server...</span>
        </div>
      )}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
