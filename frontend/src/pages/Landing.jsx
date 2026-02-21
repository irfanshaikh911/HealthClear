import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, MapPin, FileText, MessageSquare, Shield, TrendingDown, Users, ArrowRight, Star, Clock, DollarSign, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Landing.css';

const QUICK_RESULTS = [
  { id: 1, name: "Apex Medical Center", type: "Hospital", distance: "2.4 mi", rating: 4.8, cost: "$800–$1,200", tag: "In-Network" },
  { id: 2, name: "Valley Diagnostics", type: "Imaging Clinic", distance: "5.1 mi", rating: 4.5, cost: "$400–$700", tag: "Lowest Cost" },
  { id: 3, name: "Greenfield Family Clinic", type: "Primary Care", distance: "1.2 mi", rating: 4.9, cost: "$150–$350", tag: "Walk-ins" },
  { id: 4, name: "City Health General", type: "Hospital", distance: "7.8 mi", rating: 4.1, cost: "$1,100–$2,500", tag: "24/7 ER" },
  { id: 5, name: "Pacific Wellness Center", type: "Specialty", distance: "3.5 mi", rating: 4.6, cost: "$500–$900", tag: "Telehealth" },
];

const Landing = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoc, setSearchLoc] = useState('');
  const [showResults, setShowResults] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery && searchLoc) setShowResults(true);
  };

  const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.1 } } };
  const fadeUp = { hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } } };

  return (
    <div className="landing">
      {/* ====== HERO ====== */}
      <section className="hero">
        <div className="hero-bg" aria-hidden="true">
          <div className="hero-orb orb-a" />
          <div className="hero-orb orb-b" />
          <div className="hero-orb orb-c" />
          <div className="hero-grid-lines" />
        </div>

        <motion.div className="hero-content" initial="hidden" animate="visible" variants={stagger}>
          <motion.div className="hero-badge" variants={fadeUp}>
            <Shield size={14} /> Trusted by <strong>2M+</strong> patients
          </motion.div>

          <motion.h1 className="hero-title" variants={fadeUp}>
            Healthcare Costs,<br />Made <span className="text-gradient">Crystal Clear</span>.
          </motion.h1>

          <motion.p className="hero-subtitle" variants={fadeUp}>
            Compare treatment prices, verify your bills, and get AI-powered health guidance — all in one platform.
          </motion.p>

          {/* Search Bar */}
          <motion.form onSubmit={handleSearch} className="hero-search glass-panel" variants={fadeUp}>
            <div className="hs-group">
              <Search size={20} className="hs-icon" aria-hidden="true" />
              <input type="text" className="hs-input" placeholder="Condition, procedure, or doctor..."
                value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search treatment" />
            </div>
            <div className="hs-divider" />
            <div className="hs-group">
              <MapPin size={20} className="hs-icon" aria-hidden="true" />
              <input type="text" className="hs-input" placeholder="City or ZIP code"
                value={searchLoc} onChange={(e) => setSearchLoc(e.target.value)}
                aria-label="Search location" />
            </div>
            <button type="submit" className="btn btn-cta hs-btn">
              <Search size={18} /> Search
            </button>
          </motion.form>

          {/* Quick Stats */}
          <motion.div className="hero-stats" variants={fadeUp}>
            <div className="hero-stat">
              <strong>4.9</strong>
              <span>Avg Rating</span>
            </div>
            <div className="stat-divider" />
            <div className="hero-stat">
              <strong>$4.2M</strong>
              <span>Savings Found</span>
            </div>
            <div className="stat-divider" />
            <div className="hero-stat">
              <strong>50K+</strong>
              <span>Bills Analyzed</span>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ====== QUICK RESULTS (if search performed) ====== */}
      {showResults && (
        <motion.section className="quick-results container"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="qr-header">
            <h2>Top results for "{searchQuery}" near {searchLoc}</h2>
            {!isAuthenticated && <p className="qr-hint">
              <Link to="/login">Log in</Link> to see full results, ratings, and detailed cost breakdowns.
            </p>}
          </div>
          <div className="qr-list">
            {QUICK_RESULTS.map((p, i) => (
              <div key={p.id} className="qr-card glass-card">
                <div className="qr-top">
                  <span className="qr-type">{p.type}</span>
                  <span className="qr-rating"><Star size={14} fill="var(--color-cta)" color="var(--color-cta)" /> {p.rating}</span>
                </div>
                <h3>{p.name}</h3>
                <div className="qr-meta">
                  <span><MapPin size={13} /> {p.distance}</span>
                  <span><DollarSign size={13} /> {p.cost}</span>
                </div>
                <span className="qr-tag">{p.tag}</span>
              </div>
            ))}
          </div>
          <div className="qr-cta">
            <Link to="/find-treatment" className="btn btn-primary">
              View All Results <ArrowRight size={16} />
            </Link>
          </div>
        </motion.section>
      )}

      {/* ====== FEATURES ====== */}
      <section className="features container" id="features">
        <motion.div className="section-intro"
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }}>
          <h2>Everything you need.<br/>One platform.</h2>
          <p>Three powerful tools to navigate healthcare with confidence.</p>
        </motion.div>

        <div className="feature-grid">
          <motion.div className="feature-card glass-card"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ delay: 0 }}>
            <div className="fc-icon primary"><FileText size={28} /></div>
            <h3>Bill Verification</h3>
            <p>Upload any medical bill and instantly detect overcharges. Our AI compares each line item against fair market rates.</p>
            <Link to={isAuthenticated ? '/bill-analysis' : '/login'} className="fc-link">
              Analyze a Bill <ChevronRight size={16} />
            </Link>
          </motion.div>

          <motion.div className="feature-card glass-card"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ delay: 0.1 }}>
            <div className="fc-icon accent"><Search size={28} /></div>
            <h3>Find Treatment</h3>
            <p>Search providers like you search for flights — compare costs, ratings, wait times, and insurance coverage side by side.</p>
            <Link to="/find-treatment" className="fc-link">
              Search Providers <ChevronRight size={16} />
            </Link>
          </motion.div>

          <motion.div className="feature-card glass-card"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ delay: 0.2 }}>
            <div className="fc-icon cta"><MessageSquare size={28} /></div>
            <h3>AI Health Assistant</h3>
            <p>Chat with our AI to understand symptoms, compare treatment options, and get personalized cost estimates in real-time.</p>
            <Link to={isAuthenticated ? '/assistant' : '/login'} className="fc-link">
              Start Chatting <ChevronRight size={16} />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ====== HOW IT WORKS ====== */}
      <section className="how-it-works container" id="how-it-works">
        <motion.div className="section-intro"
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }}>
          <h2>Simple. Smart. Safe.</h2>
          <p>Three steps to better healthcare decisions.</p>
        </motion.div>

        <div className="steps-row">
          <motion.div className="step-card" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <div className="step-num">01</div>
            <h3>Search or Upload</h3>
            <p>Enter your condition or upload a medical bill to get started.</p>
          </motion.div>
          <div className="step-connector" aria-hidden="true" />
          <motion.div className="step-card" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}>
            <div className="step-num">02</div>
            <h3>Compare & Analyze</h3>
            <p>Our AI cross-references costs, ratings, and your medical profile for personalized insights.</p>
          </motion.div>
          <div className="step-connector" aria-hidden="true" />
          <motion.div className="step-card" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}>
            <div className="step-num">03</div>
            <h3>Save & Decide</h3>
            <p>Make informed decisions with transparent pricing and trusted reviews.</p>
          </motion.div>
        </div>
      </section>

      {/* ====== CTA BANNER ====== */}
      <section className="cta-banner">
        <div className="container cta-inner">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2>Ready to take control of your healthcare costs?</h2>
            <p>Join 2 million+ patients who use HealthClear to save money and make better treatment decisions.</p>
            <div className="cta-btns">
              {isAuthenticated ? (
                <Link to="/profile" className="btn btn-cta">Go to Dashboard <ArrowRight size={16} /></Link>
              ) : (
                <Link to="/login" className="btn btn-cta">Get Started Free <ArrowRight size={16} /></Link>
              )}
              <Link to="/find-treatment" className="btn btn-secondary">Search Providers</Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ====== FOOTER ====== */}
      <footer className="landing-footer">
        <div className="container footer-inner">
          <span className="footer-brand">HealthClear &copy; 2025</span>
          <nav className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
          </nav>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
