import { Link, useLocation } from 'react-router-dom';
import { Activity, FileText, Search, MessageSquare, User, Sun, Moon, LogOut } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const location = useLocation();
  const { theme, toggle } = useTheme();
  const { isAuthenticated, logout } = useAuth();

  // Hide on login, register & questionnaire
  if (['/login', '/register', '/questionnaire'].includes(location.pathname)) return null;

  const isLanding = location.pathname === '/';

  // Authenticated nav links
  const navLinks = [
    { path: '/profile', icon: User, label: 'Dashboard' },
    { path: '/bill-analysis', icon: FileText, label: 'Bill Analysis' },
    { path: '/find-treatment', icon: Search, label: 'Find Treatment' },
    { path: '/assistant', icon: MessageSquare, label: 'Assistant' },
  ];

  return (
    <header className={`navbar-wrapper ${isLanding ? 'landing-nav' : ''}`}>
      <nav className="navbar glass-panel" role="navigation" aria-label="Main navigation">
        <Link to="/" className="logo" aria-label="Health Clear Home">
          <div className="logo-mark">
            <Activity size={20} strokeWidth={2.5} />
          </div>
          <span className="logo-text">HealthClear</span>
        </Link>

        {/* If authenticated and NOT on landing, show app nav */}
        {isAuthenticated && !isLanding && (
          <div className="nav-links">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link key={link.path} to={link.path}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                  aria-label={link.label} aria-current={isActive ? 'page' : undefined}>
                  <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="nav-label">{link.label}</span>
                </Link>
              );
            })}
          </div>
        )}

        {/* Landing page nav links */}
        {isLanding && (
          <div className="nav-links">
            <a href="#features" className="nav-link">Features</a>
            <a href="#how-it-works" className="nav-link">How It Works</a>
            <Link to="/find-treatment" className="nav-link">Find Treatment</Link>
          </div>
        )}

        <div className="nav-actions">
          <button className="btn-icon theme-toggle" onClick={toggle}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>

          {isAuthenticated ? (
            <>
              {isLanding && (
                <Link to="/profile" className="btn btn-secondary nav-auth-btn">Dashboard</Link>
              )}
              {!isLanding && (
                <Link to="/login" onClick={logout} className="btn-icon logout-btn" aria-label="Log out" title="Log out">
                  <LogOut size={18} />
                </Link>
              )}
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link login-link">Login</Link>
              <Link to="/register" className="btn btn-primary nav-auth-btn">Sign Up</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
