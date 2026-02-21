import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, MapPin, FileText, MessageSquare, Shield, TrendingDown, ArrowRight, Star, DollarSign, ChevronRight, Sparkles, Activity, Zap, Lock, Heart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Landing.css';

const QUICK_RESULTS = [
  { id: 1, name: "Apex Medical Center", type: "Hospital", distance: "2.4 mi", rating: 4.8, cost: "$800–$1,200", tag: "In-Network" },
  { id: 2, name: "Valley Diagnostics", type: "Imaging", distance: "5.1 mi", rating: 4.5, cost: "$400–$700", tag: "Lowest Cost" },
  { id: 3, name: "Greenfield Family", type: "Primary Care", distance: "1.2 mi", rating: 4.9, cost: "$150–$350", tag: "Walk-ins" },
  { id: 4, name: "City Health General", type: "Hospital", distance: "7.8 mi", rating: 4.1, cost: "$1,100–$2,500", tag: "24/7 ER" },
  { id: 5, name: "Pacific Wellness", type: "Specialty", distance: "3.5 mi", rating: 4.6, cost: "$500–$900", tag: "Telehealth" },
];

const Landing = () => {
  const { isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoc, setSearchLoc] = useState('');
  const [showResults, setShowResults] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery && searchLoc) setShowResults(true);
  };

  const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } } };
  const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } } };

  return (
    <div className="landing">
      {/* ====== HERO ====== */}
      <section className="hero">
        <div className="hero-mesh" aria-hidden="true">
          <div className="mesh-orb mesh-1" />
          <div className="mesh-orb mesh-2" />
          <div className="mesh-orb mesh-3" />
          <div className="mesh-orb mesh-4" />
          <div className="hero-grid" />
        </div>

        <motion.div className="hero-content container" initial="hidden" animate="visible" variants={stagger}>
          <motion.div className="hero-left" variants={stagger}>
            <motion.div className="hero-pill" variants={fadeUp}>
              <Sparkles size={14} />
              <span>Trusted by <strong>2M+</strong> patients nationwide</span>
            </motion.div>

            <motion.h1 className="hero-title" variants={fadeUp}>
              Healthcare Costs,<br />
              Made <span className="text-gradient">Crystal Clear</span>.
            </motion.h1>

            <motion.p className="hero-subtitle" variants={fadeUp}>
              Compare treatment prices, verify medical bills, and chat with our AI health assistant — all in one beautiful platform.
            </motion.p>

            {/* Search */}
            <motion.form onSubmit={handleSearch} className="hero-search glass-panel" variants={fadeUp}>
              <div className="hs-group">
                <Search size={18} className="hs-icon" aria-hidden="true" />
                <input type="text" className="hs-input" placeholder="Condition or procedure..."
                  value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                  aria-label="Search treatment" />
              </div>
              <div className="hs-divider" />
              <div className="hs-group">
                <MapPin size={18} className="hs-icon" aria-hidden="true" />
                <input type="text" className="hs-input" placeholder="City or ZIP"
                  value={searchLoc} onChange={(e) => setSearchLoc(e.target.value)}
                  aria-label="Search location" />
              </div>
              <button type="submit" className="btn btn-cta hs-btn" aria-label="Search">
                <Search size={18} />
              </button>
            </motion.form>

            {/* Stats */}
            <motion.div className="hero-stats" variants={fadeUp}>
              <div className="hs-stat">
                <strong>4.9<sup>*</sup></strong>
                <span>Avg. Rating</span>
              </div>
              <div className="hs-stat">
                <strong>$4.2M</strong>
                <span>Savings Found</span>
              </div>
              <div className="hs-stat">
                <strong>50K+</strong>
                <span>Bills Analyzed</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Hero Image */}
          <motion.div className="hero-right" variants={fadeUp}>
            <div className="hero-image-wrap">
              <img src="/images/hero-medical.png" alt="Healthcare technology illustration" className="hero-image" loading="eager" />
              {/* Floating glass cards on top of hero image */}
              <div className="floating-card fc-1 glass-panel">
                <Heart size={16} className="fc-heart" />
                <div>
                  <small>Health Score</small>
                  <strong>92/100</strong>
                </div>
              </div>
              <div className="floating-card fc-2 glass-panel">
                <TrendingDown size={16} className="fc-savings" />
                <div>
                  <small>Saved</small>
                  <strong>$4,300</strong>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ====== QUICK RESULTS ====== */}
      {showResults && (
        <motion.section className="quick-results container"
          initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="qr-header">
            <h2>Top results for "{searchQuery}"</h2>
            {!isAuthenticated && <p className="qr-hint"><Link to="/login">Log in</Link> for full results and cost breakdowns.</p>}
          </div>
          <div className="qr-grid">
            {QUICK_RESULTS.map((p) => (
              <div key={p.id} className="qr-card glass-card">
                <div className="qr-top">
                  <span className="qr-type">{p.type}</span>
                  <span className="qr-rating"><Star size={13} fill="var(--color-cta)" color="var(--color-cta)" /> {p.rating}</span>
                </div>
                <h3>{p.name}</h3>
                <div className="qr-meta">
                  <span><MapPin size={12} /> {p.distance}</span>
                  <span><DollarSign size={12} /> {p.cost}</span>
                </div>
                <span className="qr-tag">{p.tag}</span>
              </div>
            ))}
          </div>
          <div className="qr-cta">
            <Link to={isAuthenticated ? "/find-treatment" : "/register"} className="btn btn-primary">
              View All Results <ArrowRight size={16} />
            </Link>
          </div>
        </motion.section>
      )}

      {/* ====== BENTO FEATURES ====== */}
      <section className="bento-section container" id="features">
        <motion.div className="section-intro" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
          <span className="section-label"><Zap size={14} /> Core Features</span>
          <h2>Everything you need,<br />one platform.</h2>
        </motion.div>

        <div className="bento-grid">
          {/* Large card — Bill Analysis */}
          <motion.div className="bento-card bento-large glass-card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <div className="bento-content">
              <div className="bento-icon primary"><FileText size={28} /></div>
              <h3>Bill Verification & Analysis</h3>
              <p>Upload any medical bill — our AI scans each line item against fair market rates and flags overcharges instantly.</p>
              <Link to={isAuthenticated ? '/bill-analysis' : '/login'} className="bento-link">
                Analyze a Bill <ChevronRight size={16} />
              </Link>
            </div>
            <div className="bento-visual">
              <img src="/images/bill-analysis-hero.png" alt="Bill analysis visualization" loading="lazy" />
            </div>
          </motion.div>

          {/* Medium card — Find Treatment */}
          <motion.div className="bento-card bento-medium glass-card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}>
            <div className="bento-icon accent"><Search size={28} /></div>
            <h3>Find Treatment</h3>
            <p>Search and compare providers across cost, ratings, wait times, and insurance — like booking a flight for your health.</p>
            <Link to="/find-treatment" className="bento-link">
              Search Providers <ChevronRight size={16} />
            </Link>
            <div className="bento-visual-sm">
              <img src="/images/trust-shield.png" alt="Trust shield" loading="lazy" />
            </div>
          </motion.div>

          {/* Medium card — AI Assistant */}
          <motion.div className="bento-card bento-medium bento-dark glass-card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}>
            <div className="bento-icon cta"><MessageSquare size={28} /></div>
            <h3>AI Health Assistant</h3>
            <p>Chat with our AI about symptoms, treatment options, and costs. Get personalized recommendations powered by your medical profile.</p>
            <Link to={isAuthenticated ? '/assistant' : '/login'} className="bento-link">
              Start Chatting <ChevronRight size={16} />
            </Link>
            <div className="bento-visual-sm">
              <img src="/images/chat-hero.png" alt="AI assistant" loading="lazy" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* ====== HOW IT WORKS ====== */}
      <section className="how-section container" id="how-it-works">
        <motion.div className="section-intro" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
          <span className="section-label"><Activity size={14} /> How It Works</span>
          <h2>Three steps to smarter<br />healthcare decisions.</h2>
        </motion.div>

        <div className="steps-row">
          {[
            { num: "01", title: "Search or Upload", desc: "Enter your condition, find a provider, or upload a medical bill to get started." },
            { num: "02", title: "AI Analyzes", desc: "Our AI cross-references costs, ratings, and your medical profile for personalized insights." },
            { num: "03", title: "Save & Decide", desc: "Make informed decisions with transparent pricing, verified reviews, and dispute guidance." }
          ].map((step, i) => (
            <motion.div key={step.num} className="step-card glass-card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.12 }}>
              <div className="step-num">{step.num}</div>
              <h3>{step.title}</h3>
              <p>{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ====== CTA ====== */}
      <section className="cta-section">
        <div className="container">
          <motion.div className="cta-card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <div className="cta-mesh" aria-hidden="true">
              <div className="cta-orb cta-orb-1" />
              <div className="cta-orb cta-orb-2" />
            </div>
            <div className="cta-body">
              <h2>Ready to take control of<br />your healthcare costs?</h2>
              <p>Join 2 million+ patients who use HealthClear to save money and make better treatment decisions.</p>
              <div className="cta-btns">
                {isAuthenticated ? (
                  <Link to="/profile" className="btn btn-cta">Go to Dashboard <ArrowRight size={16} /></Link>
                ) : (
                  <Link to="/login" className="btn btn-cta">Get Started Free <ArrowRight size={16} /></Link>
                )}
                <Link to="/find-treatment" className="btn btn-secondary">Search Providers</Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ====== FOOTER ====== */}
      <footer className="landing-footer">
        <div className="container footer-inner">
          <div className="footer-brand">
            <Activity size={16} />
            <span>HealthClear</span>
          </div>
          <nav className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
          </nav>
          <span className="footer-copy">&copy; 2025 HealthClear. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
