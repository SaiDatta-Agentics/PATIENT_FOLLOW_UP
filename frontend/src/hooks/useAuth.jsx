import { createContext, useContext, useState, useCallback } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const fullName = localStorage.getItem('fullName');
    const patientId = localStorage.getItem('patientId');
    return token ? { token, role, fullName, patientId: patientId ? Number(patientId) : null } : null;
  });

  const persist = useCallback((data) => {
    const next = {
      token: data.access_token,
      role: data.role,
      fullName: data.full_name,
      patientId: data.patient_id ?? null,
    };
    localStorage.setItem('token', next.token);
    localStorage.setItem('role', next.role);
    localStorage.setItem('fullName', next.fullName);
    if (next.patientId) localStorage.setItem('patientId', String(next.patientId));
    else localStorage.removeItem('patientId');
    setUser(next);
    return next;
  }, []);

  const login = useCallback(async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password });
    return persist(data);
  }, [persist]);

  const register = useCallback(async (payload) => {
    const { data } = await api.post('/auth/register', payload);
    return persist(data);
  }, [persist]);

  const logout = useCallback(() => {
    ['token', 'role', 'fullName', 'patientId'].forEach(k => localStorage.removeItem(k));
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
