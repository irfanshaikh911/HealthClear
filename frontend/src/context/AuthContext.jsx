import { createContext, useContext, useState, useEffect } from 'react';
import { loginUser, registerUser, getMe, submitOnboarding } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('hc-user');
    return saved ? JSON.parse(saved) : null;
  });

  const persistUser = (userData) => {
    setUser(userData);
    localStorage.setItem('hc-user', JSON.stringify(userData));
  };

  // Rehydrate user on mount if we have a stored user id
  useEffect(() => {
    if (user?.id && !user?.profileComplete) {
      getMe(user.id)
        .then((data) => persistUser(data.user))
        .catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (email, password) => {
    try {
      const data = await loginUser(email, password);
      persistUser(data.user);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const register = async (name, email, password) => {
    try {
      const data = await registerUser(name, email, password);
      persistUser(data.user);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('hc-user');
  };

  const completeOnboarding = async (patientData) => {
    if (!user?.id) return;
    try {
      const result = await submitOnboarding(user.id, patientData);
      // Refresh full user data
      const meData = await getMe(user.id);
      persistUser(meData.user);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const needsOnboarding = !!user && !user.profileComplete;

  return (
    <AuthContext.Provider value={{
      user,
      login,
      register,
      logout,
      completeOnboarding,
      isAuthenticated: !!user,
      needsOnboarding
    }}>
      {children}
    </AuthContext.Provider>
  );
};
