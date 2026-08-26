import { api } from './api';
import type { TokenResponse, User, UserLoginRequest, UserRegisterRequest } from '../types/auth';

export const authService = {
  async login(credentials: UserLoginRequest): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  async register(data: UserRegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  async me(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};
