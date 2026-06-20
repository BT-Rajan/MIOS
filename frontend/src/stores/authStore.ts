import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  } | null;
  isAuthenticated: boolean;
  login: (token: string, user: AuthState['user']) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      
      login: (token, user) => {
        localStorage.setItem('access_token', token);
        set({ token, user, isAuthenticated: true });
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuthStore;
