import { createContext, useContext, useState } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

// Hardcoded demo credentials
const DEMO_CREDENTIALS = {
  email: 'patient@healthclear.com',
  password: 'health123'
};

const DEMO_USER = {
  name: 'Alex Johnson',
  email: 'patient@healthclear.com',
  bloodType: 'O+',
  allergies: 'Penicillin',
  conditions: 'Mild Asthma',
  medications: 'Ventolin Inhaler (as needed)',
  dob: '1992-04-15',
  gender: 'Male',
  profileComplete: true
};

// Helper: get registered users from localStorage
const getRegisteredUsers = () => {
  try {
    return JSON.parse(localStorage.getItem('hc-registered-users') || '[]');
  } catch { return []; }
};

const saveRegisteredUsers = (users) => {
  localStorage.setItem('hc-registered-users', JSON.stringify(users));
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('hc-user');
    return saved ? JSON.parse(saved) : null;
  });

  const persistUser = (userData) => {
    setUser(userData);
    localStorage.setItem('hc-user', JSON.stringify(userData));
  };

  const login = (email, password) => {
    // Check demo credentials first
    if (email === DEMO_CREDENTIALS.email && password === DEMO_CREDENTIALS.password) {
      persistUser(DEMO_USER);
      return { success: true };
    }
    // Check registered users
    const users = getRegisteredUsers();
    const found = users.find(u => u.email === email && u.password === password);
    if (found) {
      const { password: _, ...userData } = found;
      persistUser(userData);
      return { success: true };
    }
    return { success: false, error: 'Invalid email or password. Please try again.' };
  };

  const register = (name, email, password) => {
    const users = getRegisteredUsers();
    // Check if email already exists
    if (email === DEMO_CREDENTIALS.email || users.some(u => u.email === email)) {
      return { success: false, error: 'An account with this email already exists.' };
    }
    // Create new user with profileComplete: false
    const newUser = {
      name,
      email,
      password, // stored in registered-users list for login
      profileComplete: false,
      createdAt: new Date().toISOString()
    };
    users.push(newUser);
    saveRegisteredUsers(users);
    // Log them in (without password in session)
    const { password: _, ...sessionUser } = newUser;
    persistUser(sessionUser);
    return { success: true };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('hc-user');
  };

  const completeOnboarding = (patientData) => {
    const updated = { ...user, ...patientData, profileComplete: true };
    persistUser(updated);
    // Also update in registered users list
    const users = getRegisteredUsers();
    const idx = users.findIndex(u => u.email === user.email);
    if (idx !== -1) {
      users[idx] = { ...users[idx], ...patientData, profileComplete: true };
      saveRegisteredUsers(users);
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
