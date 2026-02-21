import { createContext, useContext, useState } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

// Hardcoded credentials for demo
const VALID_CREDENTIALS = {
  email: 'patient@healthclear.com',
  password: 'health123'
};

const MOCK_USER = {
  name: 'Alex Johnson',
  email: 'patient@healthclear.com',
  bloodType: 'O+',
  allergies: ['Penicillin'],
  conditions: ['Mild Asthma'],
  medications: ['Ventolin Inhaler (as needed)'],
  dob: '1992-04-15',
  gender: 'Male',
  profileComplete: true
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('hc-user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (email, password) => {
    if (email === VALID_CREDENTIALS.email && password === VALID_CREDENTIALS.password) {
      setUser(MOCK_USER);
      localStorage.setItem('hc-user', JSON.stringify(MOCK_USER));
      return { success: true };
    }
    return { success: false, error: 'Invalid credentials. Try patient@healthclear.com / health123' };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('hc-user');
  };

  const completeOnboarding = (data) => {
    const updated = { ...user, ...data, profileComplete: true };
    setUser(updated);
    localStorage.setItem('hc-user', JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, completeOnboarding, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};
