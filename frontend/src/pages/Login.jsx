import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, Mail, Lock, ArrowRight, Eye, EyeOff, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();
  const { theme, toggle } = useTheme();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Small delay for UX feedback
    await new Promise(r => setTimeout(r, 600));

    const result = login(email, password);
    setLoading(false);

    if (result.success) {
      navigate('/profile');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      {/* Theme toggle on login page */}
      <button className="login-theme-toggle" onClick={toggle}
        aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
      </button>

      {/* Decorative orbs */}
      <div className="login-orbs" aria-hidden="true">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <motion.div
        className="login-card glass-panel"
        initial={{ opacity: 0, y: 30, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="login-header animate-in delay-1">
          <div className="login-logo-mark">
            <Activity size={28} strokeWidth={2.5} />
          </div>
          <h1>HealthClear</h1>
          <p className="login-subtitle">Transparent healthcare costs. Better decisions.</p>
        </div>

        <form onSubmit={handleLogin} className="login-form animate-in delay-2" noValidate>
          {error && (
            <motion.div
              className="login-error"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              role="alert"
            >
              {error}
            </motion.div>
          )}

          <div className="input-group">
            <label className="input-label" htmlFor="login-email">Email Address</label>
            <div className="input-with-icon">
              <Mail className="field-icon" size={18} aria-hidden="true" />
              <input
                id="login-email"
                type="email"
                className="input-field"
                placeholder="patient@healthclear.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="input-group">
            <div className="label-row">
              <label className="input-label" htmlFor="login-password">Password</label>
              <a href="#" className="forgot-link">Forgot?</a>
            </div>
            <div className="input-with-icon">
              <Lock className="field-icon" size={18} aria-hidden="true" />
              <input
                id="login-password"
                type={showPw ? 'text' : 'password'}
                className="input-field"
                placeholder="health123"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="pw-toggle"
                onClick={() => setShowPw(!showPw)}
                aria-label={showPw ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary w-full login-submit" disabled={loading}>
            {loading ? <span className="spinner" /> : (
              <>
                <span>Sign In</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <p className="login-footer animate-in delay-3">
          Demo credentials: <strong>patient@healthclear.com</strong> / <strong>health123</strong>
        </p>
      </motion.div>
    </div>
  );
};

export default Login;
