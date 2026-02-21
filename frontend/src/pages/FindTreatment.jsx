import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, MapPin, Star, Shield, ArrowRight, Clock, DollarSign, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './FindTreatment.css';

const ALL_RESULTS = [
  { id: 1, name: "Apex Medical Center", type: "Hospital", distance: "2.4 mi", rating: 4.8, reviews: 342, costRange: "$800 – $1,200", tags: ["High Trust Score", "In-Network"], waitTime: "~15 min", address: "123 Main St, Seattle, WA 98101" },
  { id: 2, name: "Valley Diagnostics & Imaging", type: "Specialty Clinic", distance: "5.1 mi", rating: 4.5, reviews: 128, costRange: "$400 – $700", tags: ["Fast Availability", "Lowest Cost"], waitTime: "~5 min", address: "456 Oak Ave, Bellevue, WA 98004" },
  { id: 3, name: "City Health General", type: "Hospital", distance: "7.8 mi", rating: 4.1, reviews: 890, costRange: "$1,100 – $2,500", tags: ["24/7 ER", "Level 1 Trauma"], waitTime: "~30 min", address: "789 Cedar Blvd, Tacoma, WA 98402" },
  { id: 4, name: "Greenfield Family Clinic", type: "Primary Care", distance: "1.2 mi", rating: 4.9, reviews: 67, costRange: "$150 – $350", tags: ["Walk-ins Welcome", "Telehealth"], waitTime: "~10 min", address: "21 Elm St, Seattle, WA 98103" },
  { id: 5, name: "Pacific Wellness Center", type: "Specialty", distance: "3.5 mi", rating: 4.6, reviews: 215, costRange: "$500 – $900", tags: ["Telehealth", "Top Rated"], waitTime: "~8 min", address: "55 Pine Ave, Seattle, WA 98105" },
  { id: 6, name: "Harborview Medical", type: "Hospital", distance: "4.2 mi", rating: 4.7, reviews: 1240, costRange: "$900 – $1,800", tags: ["Level 1 Trauma", "Teaching"], waitTime: "~25 min", address: "325 9th Ave, Seattle, WA 98104" },
  { id: 7, name: "Eastside Health Partners", type: "Multi-Specialty", distance: "6.3 mi", rating: 4.4, reviews: 305, costRange: "$350 – $750", tags: ["In-Network", "Lab On-Site"], waitTime: "~12 min", address: "100 Lake Dr, Kirkland, WA 98033" },
  { id: 8, name: "Sound Health Clinic", type: "Primary Care", distance: "2.8 mi", rating: 4.8, reviews: 186, costRange: "$200 – $400", tags: ["Walk-ins", "Pediatrics"], waitTime: "~15 min", address: "77 Market St, Seattle, WA 98101" },
];

const FindTreatment = () => {
  const { isAuthenticated } = useAuth();
  const [treatment, setTreatment] = useState('');
  const [location, setLocation] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!treatment || !location) return;
    setIsSearching(true);
    setTimeout(() => { setIsSearching(false); setHasSearched(true); }, 1000);
  };

  const visibleResults = isAuthenticated ? ALL_RESULTS : ALL_RESULTS.slice(0, 5);

  return (
    <motion.div className="treatment-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className={`search-hero ${hasSearched ? 'compact' : ''}`}>
        <div className="hero-inner animate-in delay-1">
          {!hasSearched && <h1>Find the Right Care<br/>at the Right Price</h1>}
          {!hasSearched && <p>Compare treatments, reviews, and costs across providers near you.</p>}
        </div>

        <form onSubmit={handleSearch} className={`search-bar glass-panel animate-in delay-2 ${hasSearched ? 'compact-bar' : ''}`}>
          <div className="search-input-group">
            <Search className="si-icon" size={20} aria-hidden="true" />
            <input type="text" placeholder="Condition, procedure, or doctor..."
              className="si-input" value={treatment} onChange={(e) => setTreatment(e.target.value)}
              aria-label="Search treatment or condition" />
          </div>
          <div className="search-divider" />
          <div className="search-input-group">
            <MapPin className="si-icon" size={20} aria-hidden="true" />
            <input type="text" placeholder="City, ZIP, or 'Near Me'"
              className="si-input" value={location} onChange={(e) => setLocation(e.target.value)}
              aria-label="Search location" />
          </div>
          <button type="submit" className="btn btn-primary search-submit" disabled={isSearching}>
            {isSearching ? <span className="spinner" /> : 'Search'}
          </button>
        </form>
      </div>

      <AnimatePresence>
        {hasSearched && !isSearching && (
          <motion.div className="results-section"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
            <div className="results-meta">
              <p>
                Showing <strong>{visibleResults.length}</strong>
                {!isAuthenticated && <> of <strong>{ALL_RESULTS.length}</strong></>} results
                for <strong>"{treatment}"</strong> near <strong>{location}</strong>
              </p>
            </div>

            <div className="provider-list">
              {visibleResults.map((p, i) => (
                <motion.div key={p.id} className="provider-card glass-card"
                  initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}>
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

            {/* Login Prompt for unauthenticated users */}
            {!isAuthenticated && (
              <motion.div className="login-prompt glass-card"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                <Lock size={22} />
                <div>
                  <h3>See all {ALL_RESULTS.length} results</h3>
                  <p>Log in for full provider details, cost breakdowns, and insurance filtering.</p>
                </div>
                <Link to="/login" className="btn btn-cta">
                  Log In <ArrowRight size={16} />
                </Link>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default FindTreatment;
