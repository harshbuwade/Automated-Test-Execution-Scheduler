import React, { createContext, useContext, useEffect, useState } from 'react';
import { authService } from '../services/authService';
import type { User, UserLoginRequest, UserRegisterRequest } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (data: UserRegisterRequest) => Promise<void>;
  logout: () => void;
}

const DEFAULT_DEMO_USER = {
  name: 'Default User',
  email: 'demo@scheduler.local',
  password: 'DemoPassword123!',
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const performAutoAuth = async () => {
    try {
      // 1. Try logging in with default demo user
      const loginRes = await authService.login({
        email: DEFAULT_DEMO_USER.email,
        password: DEFAULT_DEMO_USER.password,
      });
      localStorage.setItem('token', loginRes.access_token);
      setToken(loginRes.access_token);
      const currentUser = await authService.me();
      setUser(currentUser);
    } catch {
      // 2. If login fails, register the default demo user first then log in
      try {
        await authService.register(DEFAULT_DEMO_USER);
        const loginRes = await authService.login({
          email: DEFAULT_DEMO_USER.email,
          password: DEFAULT_DEMO_USER.password,
        });
        localStorage.setItem('token', loginRes.access_token);
        setToken(loginRes.access_token);
        const currentUser = await authService.me();
        setUser(currentUser);
      } catch (err) {
        console.error('Silent auto-authentication failed:', err);
      }
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const currentUser = await authService.me();
          setUser(currentUser);
          setToken(storedToken);
          setIsLoading(false);
          return;
        } catch {
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }

      // Automatically authenticate if no valid token exists
      await performAutoAuth();
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: UserLoginRequest) => {
    setIsLoading(true);
    try {
      const res = await authService.login(credentials);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      const currentUser = await authService.me();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: UserRegisterRequest) => {
    setIsLoading(true);
    try {
      await authService.register(data);
      await login({ email: data.email, password: data.password });
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    // Perform auto-auth to seamlessly switch back to default session
    performAutoAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
