import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, User, Mail, Lock, ArrowRight, Eye, EyeOff, Sun, Moon, Shield, Heart, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import './Register.css';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();
  const { theme, toggle } = useTheme();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    if (password !== confirmPw) { setError('Passwords do not match.'); return; }
    setLoading(true);
    await new Promise(r => setTimeout(r, 600));
    const result = register(name, email, password);
    setLoading(false);
    if (result.success) { navigate('/questionnaire'); } else { setError(result.error); }
  };

  return (
    <div className="auth-page">
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
            <Link to="/" className="auth-logo">
              <div className="auth-logo-mark">
                <Activity size={24} strokeWidth={2.5} />
              </div>
              <span>HealthClear</span>
            </Link>

            <div className="auth-heading">
              <h1>Create your account</h1>
              <p>Join HealthClear and start making smarter healthcare decisions today.</p>
            </div>

            <form onSubmit={handleRegister} className="auth-form" noValidate>
              {error && (
                <motion.div className="auth-error"
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} role="alert">
                  {error}
                </motion.div>
              )}

              <div className="input-group">
                <label className="input-label" htmlFor="reg-name">Full Name</label>
                <div className="input-with-icon">
                  <User className="field-icon" size={18} aria-hidden="true" />
                  <input id="reg-name" type="text" className="input-field"
                    placeholder="Alex Johnson" value={name}
                    onChange={(e) => setName(e.target.value)} autoComplete="name" required />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="reg-email">Email Address</label>
                <div className="input-with-icon">
                  <Mail className="field-icon" size={18} aria-hidden="true" />
                  <input id="reg-email" type="email" className="input-field"
                    placeholder="you@example.com" value={email}
                    onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="reg-password">Password</label>
                <div className="input-with-icon">
                  <Lock className="field-icon" size={18} aria-hidden="true" />
                  <input id="reg-password" type={showPw ? 'text' : 'password'}
                    className="input-field" placeholder="Min. 6 characters"
                    value={password} onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password" required />
                  <button type="button" className="pw-toggle"
                    onClick={() => setShowPw(!showPw)}
                    aria-label={showPw ? 'Hide password' : 'Show password'} tabIndex={-1}>
                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="reg-confirm">Confirm Password</label>
                <div className="input-with-icon">
                  <Lock className="field-icon" size={18} aria-hidden="true" />
                  <input id="reg-confirm" type={showPw ? 'text' : 'password'}
                    className="input-field" placeholder="Re-enter password"
                    value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)}
                    autoComplete="new-password" required />
                </div>
              </div>

              <button type="submit" className="btn btn-primary w-full auth-submit" disabled={loading}>
                {loading ? <span className="spinner" /> : (
                  <><span>Create Account</span><ArrowRight size={18} /></>
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p>Already have an account? <Link to="/login" className="auth-link">Sign in</Link></p>
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
            <Sparkles size={14} /> Your health, your data
          </div>
          <h2>Transparent pricing.<br />Better outcomes.</h2>
          <div className="auth-hero-stats">
            <div className="auth-hero-stat">
              <Shield size={18} />
              <div>
                <strong>HIPAA</strong>
                <span>Compliant</span>
              </div>
            </div>
            <div className="auth-hero-stat">
              <Heart size={18} />
              <div>
                <strong>4.9★</strong>
                <span>User rating</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
