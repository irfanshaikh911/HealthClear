import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, Mail, Lock, ArrowRight, Eye, EyeOff, Sun, Moon, Shield, TrendingDown, FileText } from 'lucide-react';
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
    const result = await login(email, password);
    setLoading(false);
    if (result.success) {
      navigate('/profile');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="auth-page">
      {/* Theme toggle */}
      <button className="auth-theme-toggle" onClick={toggle}
        aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
      </button>

      {/* LEFT: Form side */}
      <div className="auth-form-side">
        <div className="auth-form-inner">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Logo */}
            <Link to="/" className="auth-logo">
              <div className="auth-logo-mark">
                <Activity size={24} strokeWidth={2.5} />
              </div>
              <span>HealthClear</span>
            </Link>

            <div className="auth-heading">
              <h1>Welcome back</h1>
              <p>Sign in to access your dashboard, analyze bills, and manage your healthcare.</p>
            </div>

            <form onSubmit={handleLogin} className="auth-form" noValidate>
              {error && (
                <motion.div className="auth-error"
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} role="alert">
                  {error}
                </motion.div>
              )}

              <div className="input-group">
                <label className="input-label" htmlFor="login-email">Email Address</label>
                <div className="input-with-icon">
                  <Mail className="field-icon" size={18} aria-hidden="true" />
                  <input id="login-email" type="email" className="input-field"
                    placeholder="patient@healthclear.com"
                    value={email} onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email" required />
                </div>
              </div>

              <div className="input-group">
                <div className="label-row">
                  <label className="input-label" htmlFor="login-password">Password</label>
                  <a href="#" className="forgot-link">Forgot?</a>
                </div>
                <div className="input-with-icon">
                  <Lock className="field-icon" size={18} aria-hidden="true" />
                  <input id="login-password" type={showPw ? 'text' : 'password'}
                    className="input-field" placeholder="health123"
                    value={password} onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password" required />
                  <button type="button" className="pw-toggle"
                    onClick={() => setShowPw(!showPw)}
                    aria-label={showPw ? 'Hide password' : 'Show password'} tabIndex={-1}>
                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button type="submit" className="btn btn-primary w-full auth-submit" disabled={loading}>
                {loading ? <span className="spinner" /> : (
                  <><span>Sign In</span><ArrowRight size={18} /></>
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p>Demo: <strong>patient@healthclear.com</strong> / <strong>health123</strong></p>
              <p className="mt-2">Don't have an account? <Link to="/register" className="auth-link">Sign up</Link></p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* RIGHT: Hero side */}
      <div className="auth-hero-side">
        <div className="auth-hero-overlay" />
        <img src="/images/auth-hero.png" alt="" className="auth-hero-img" aria-hidden="true" />
        <div className="auth-hero-content">
          <div className="auth-hero-badge">
            <Shield size={14} /> Trusted by 2M+ patients
          </div>
          <h2>Take control of your<br />healthcare costs</h2>
          <div className="auth-hero-stats">
            <div className="auth-hero-stat">
              <TrendingDown size={18} />
              <div>
                <strong>$4.2M</strong>
                <span>Savings found</span>
              </div>
            </div>
            <div className="auth-hero-stat">
              <FileText size={18} />
              <div>
                <strong>50K+</strong>
                <span>Bills analyzed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
