import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import {
  MessageSquare, Search, MapPin, FileText, ArrowRight,
  Sparkles, Send, Star, Shield, Clock, DollarSign, User,
  Tag, HandHeart, Bed
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const PROVIDERS = [
  { id: 1, name: "Apex Medical Center", type: "Hospital", distance: "2.4 mi", rating: 4.8, reviews: 342, costRange: "$800 – $1,200", tags: ["High Trust Score", "In-Network"], waitTime: "~15 min", address: "123 Main St, Seattle, WA 98101" },
  { id: 2, name: "Valley Diagnostics & Imaging", type: "Specialty Clinic", distance: "5.1 mi", rating: 4.5, reviews: 128, costRange: "$400 – $700", tags: ["Fast Availability", "Lowest Cost"], waitTime: "~5 min", address: "456 Oak Ave, Bellevue, WA 98004" },
  { id: 3, name: "Greenfield Family Clinic", type: "Primary Care", distance: "1.2 mi", rating: 4.9, reviews: 67, costRange: "$150 – $350", tags: ["Walk-ins Welcome", "Telehealth"], waitTime: "~10 min", address: "21 Elm St, Seattle, WA 98103" },
  { id: 4, name: "Pacific Wellness Center", type: "Specialty", distance: "3.5 mi", rating: 4.6, reviews: 215, costRange: "$500 – $900", tags: ["Telehealth", "Top Rated"], waitTime: "~8 min", address: "55 Pine Ave, Seattle, WA 98105" },
  { id: 5, name: "Sound Health Clinic", type: "Primary Care", distance: "2.8 mi", rating: 4.8, reviews: 186, costRange: "$200 – $400", tags: ["Walk-ins", "Pediatrics"], waitTime: "~15 min", address: "77 Market St, Seattle, WA 98101" },
  { id: 6, name: "City Health General", type: "Hospital", distance: "7.8 mi", rating: 4.1, reviews: 890, costRange: "$1,100 – $2,500", tags: ["24/7 ER", "Level 1 Trauma"], waitTime: "~30 min", address: "789 Cedar Blvd, Tacoma, WA 98402" },
];

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const name = user?.full_name || user?.name || 'User';

  // Assistant
  const [assistantInput, setAssistantInput] = useState('');
  const handleAssistantSubmit = (e) => {
    e.preventDefault();
    if (assistantInput.trim()) navigate('/assistant', { state: { initialMessage: assistantInput } });
  };
  const quickPrompts = [
    'What treatments are available for chronic back pain?',
    'Compare MRI costs near me',
    'Explain my recent lab results',
    'Find affordable physical therapy',
  ];

  // Find Treatment
  const [treatment, setTreatment] = useState('');
  const [location, setLocation] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!treatment || !location) return;
    setIsSearching(true);
    setTimeout(() => { setIsSearching(false); setHasSearched(true); }, 800);
  };

  return (
    <motion.div
      className="dash-page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* ============ HEADER ============ */}
      <div className="dash-header animate-in delay-1">
        <div className="dash-header-left">
          <div className="dash-avatar">
            <User size={28} strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="dash-greeting">Welcome back, <span className="dash-name">{name.split(' ')[0]}</span></h1>
            <p className="dash-subtitle">Here's your health overview</p>
          </div>
        </div>
      </div>

      {/* ============ AI ASSISTANT HERO ============ */}
      <div className="assistant-hero glass-card animate-in delay-2">
        <div className="assistant-hero-glow" aria-hidden="true" />
        <div className="assistant-hero-top">
          <div className="assistant-badge">
            <Sparkles size={16} />
            <span>AI Health Assistant</span>
          </div>
          <Link to="/assistant" className="assistant-open-link">
            Open full chat <ArrowRight size={14} />
          </Link>
        </div>
        <h2 className="assistant-hero-title">What can I help you with today?</h2>
        <form className="assistant-input-row" onSubmit={handleAssistantSubmit}>
          <div className="assistant-input-wrap">
            <MessageSquare size={18} className="assistant-input-icon" />
            <input type="text" className="assistant-input"
              placeholder="Ask about treatments, costs, medications..."
              value={assistantInput} onChange={(e) => setAssistantInput(e.target.value)} />
            <button type="submit" className="assistant-send-btn" aria-label="Send">
              <Send size={18} />
            </button>
          </div>
        </form>
        <div className="assistant-prompts">
          {quickPrompts.map((prompt) => (
            <button key={prompt} className="prompt-chip"
              onClick={() => navigate('/assistant', { state: { initialMessage: prompt } })}>
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* ============ FIND TREATMENT ============ */}
      <div className="treatment-section animate-in delay-3">
        <div className="treatment-header">
          <h2><Search size={20} /> Find Treatment</h2>
          <p>Compare providers, costs, and reviews near you</p>
        </div>

        <form onSubmit={handleSearch} className={`search-bar glass-panel ${hasSearched ? 'compact-bar' : ''}`}>
          <div className="search-input-group">
            <Search className="si-icon" size={20} aria-hidden="true" />
            <input type="text" placeholder="Condition, procedure, or doctor..."
              className="si-input" value={treatment}
              onChange={(e) => setTreatment(e.target.value)} aria-label="Search treatment" />
          </div>
          <div className="search-divider" />
          <div className="search-input-group">
            <MapPin className="si-icon" size={20} aria-hidden="true" />
            <input type="text" placeholder="City, ZIP, or 'Near Me'"
              className="si-input" value={location}
              onChange={(e) => setLocation(e.target.value)} aria-label="Search location" />
          </div>
          <button type="submit" className="btn btn-primary search-submit" disabled={isSearching}>
            {isSearching ? <span className="spinner" /> : 'Search'}
          </button>
        </form>

        <AnimatePresence>
          {hasSearched && !isSearching && (
            <motion.div className="results-section"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}>
              <div className="results-meta">
                <p>
                  Showing <strong>{PROVIDERS.length}</strong> results
                  for <strong>"{treatment}"</strong> near <strong>{location}</strong>
                </p>
              </div>
              <div className="provider-list">
                {PROVIDERS.map((p, i) => (
                  <motion.div key={p.id} className="provider-card glass-card"
                    initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}>
                    <div className="provider-main">
                      <div className="provider-top-row">
                        <span className="provider-type">{p.type}</span>
                        <div className="provider-rating">
                          <Star size={15} fill="var(--color-cta)" color="var(--color-cta)" />
                          <strong>{p.rating}</strong>
                          <span className="rating-count">({p.reviews})</span>
                        </div>
                      </div>
                      <h3 className="provider-name">{p.name}</h3>
                      <p className="provider-address"><MapPin size={14} /> {p.address}</p>
                      <div className="provider-tags">
                        {p.tags.map((tag, j) => (
                          <span key={j} className="ptag"><Shield size={12} /> {tag}</span>
                        ))}
                      </div>
                    </div>
                    <div className="provider-side">
                      <div className="cost-block">
                        <span className="cost-label"><DollarSign size={14} /> Est. Cost</span>
                        <strong className="cost-value">{p.costRange}</strong>
                      </div>
                      <div className="wait-block">
                        <span className="cost-label"><Clock size={14} /> Wait Time</span>
                        <strong className="cost-value small">{p.waitTime}</strong>
                      </div>
                      <button className="btn btn-primary provider-cta">
                        View Details <ArrowRight size={16} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ============ BOTTOM ACTIONS ============ */}
      <div className="dash-bottom-row animate-in delay-4">
        <Link to="/bill-analysis" className="bottom-action glass-card">
          <div className="bottom-action-icon"><FileText size={22} /></div>
          <div>
            <h4>Analyze a Bill</h4>
            <p>Upload and verify medical invoices</p>
          </div>
          <ArrowRight size={18} className="bottom-arrow" />
        </Link>
        <Link to="/assistant" className="bottom-action glass-card">
          <div className="bottom-action-icon accent"><MessageSquare size={22} /></div>
          <div>
            <h4>Chat History</h4>
            <p>View past assistant conversations</p>
          </div>
          <ArrowRight size={18} className="bottom-arrow" />
        </Link>
        <Link to="/deals" className="bottom-action glass-card">
          <div className="bottom-action-icon" style={{ background: 'var(--color-cta)' }}><Tag size={22} /></div>
          <div>
            <h4>Medical Deals</h4>
            <p>Discounts, camps & offers near you</p>
          </div>
          <ArrowRight size={18} className="bottom-arrow" />
        </Link>
        <Link to="/fundraisers" className="bottom-action glass-card">
          <div className="bottom-action-icon" style={{ background: 'var(--color-danger)' }}><HandHeart size={22} /></div>
          <div>
            <h4>Fundraisers</h4>
            <p>Discover & contribute to health funds</p>
          </div>
          <ArrowRight size={18} className="bottom-arrow" />
        </Link>
        <Link to="/icu-beds" className="bottom-action glass-card">
          <div className="bottom-action-icon" style={{ background: 'var(--color-success)' }}><Bed size={22} /></div>
          <div>
            <h4>ICU Beds</h4>
            <p>Live bed availability across hospitals</p>
          </div>
          <ArrowRight size={18} className="bottom-arrow" />
        </Link>
      </div>
    </motion.div>
  );
};

export default Profile;
