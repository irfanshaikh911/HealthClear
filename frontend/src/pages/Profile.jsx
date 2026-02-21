import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { User, FileText, Search, MessageSquare, ChevronRight, Clock, ShieldCheck, TrendingDown, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();
  const name = user?.full_name || user?.name || 'User';

  return (
    <motion.div
      className="profile-page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <div className="profile-hero animate-in delay-1">
        <div className="profile-avatar">
          <User size={36} strokeWidth={1.5} />
        </div>
        <div className="profile-hero-text">
          <h1>Welcome back, {name.split(' ')[0]}</h1>
          <span className="badge badge-accent"><ShieldCheck size={14} /> Profile Complete</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stats-row animate-in delay-2">
        <div className="stat-card glass-card">
          <div className="stat-icon primary"><TrendingDown size={20} /></div>
          <div>
            <p className="stat-value">$4,300</p>
            <p className="stat-label">Total Savings Found</p>
          </div>
        </div>
        <div className="stat-card glass-card">
          <div className="stat-icon accent"><FileText size={20} /></div>
          <div>
            <p className="stat-value">3</p>
            <p className="stat-label">Bills Analyzed</p>
          </div>
        </div>
        <div className="stat-card glass-card">
          <div className="stat-icon cta"><MessageSquare size={20} /></div>
          <div>
            <p className="stat-value">12</p>
            <p className="stat-label">Assistant Queries</p>
          </div>
        </div>
      </div>

      <div className="dash-grid">
        {/* Quick Actions */}
        <div className="glass-card dash-section animate-in delay-2">
          <h2>Quick Actions</h2>
          <div className="action-list">
            <Link to="/bill-analysis" className="action-row">
              <div className="action-icon-box primary"><FileText size={22} /></div>
              <div className="action-text">
                <h4>Analyze a Bill</h4>
                <p>Upload and verify your medical invoices</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
            <Link to="/find-treatment" className="action-row">
              <div className="action-icon-box accent"><Search size={22} /></div>
              <div className="action-text">
                <h4>Find Treatment</h4>
                <p>Compare providers and costs near you</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
            <Link to="/assistant" className="action-row">
              <div className="action-icon-box cta"><MessageSquare size={22} /></div>
              <div className="action-text">
                <h4>Health Assistant</h4>
                <p>Ask questions about treatment and pricing</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-card dash-section animate-in delay-3">
          <div className="section-top">
            <h2>Recent Activity</h2>
            <button className="btn btn-ghost">View All</button>
          </div>
          <div className="activity-feed">
            <div className="activity-item">
              <div className="activity-dot primary" />
              <div className="activity-body">
                <h4>City Hospital MRI Bill Analyzed</h4>
                <p>Saved 15% — flagged 2 overcharges</p>
              </div>
              <span className="activity-time"><Clock size={13} /> 2d ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-dot accent" />
              <div className="activity-body">
                <h4>Searched Physical Therapy Providers</h4>
                <p>Near Seattle, WA — 3 results found</p>
              </div>
              <span className="activity-time"><Clock size={13} /> 1w ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-dot cta" />
              <div className="activity-body">
                <h4>Asked Assistant about Knee Surgery Costs</h4>
                <p>Average range: $12,000–$18,000</p>
              </div>
              <span className="activity-time"><Clock size={13} /> 2w ago</span>
            </div>
          </div>
        </div>

        {/* Health Profile Summary */}
        <div className="glass-card dash-section summary-section animate-in delay-4">
          <h2>Health Profile</h2>
          <div className="profile-tags">
            {(user?.blood_type || user?.bloodType) && <span className="tag">Blood Type: {user?.blood_type || user?.bloodType}</span>}
            {user?.gender && <span className="tag">Gender: {user?.gender}</span>}
            {user?.allergies && <span className="tag">Allergies: {typeof user.allergies === 'string' ? user.allergies : user.allergies[0]}</span>}
            {user?.medical_history && <span className="tag">History: {user.medical_history}</span>}
            {(user?.conditions && Array.isArray(user.conditions)) && <span className="tag">Condition: {user.conditions[0]}</span>}
            {user?.height_cm && <span className="tag">Height: {user.height_cm} cm</span>}
            {user?.weight_kg && <span className="tag">Weight: {user.weight_kg} kg</span>}
            {user?.organ_donor && <span className="tag">Organ Donor: Yes</span>}
          </div>
          <button className="btn btn-secondary w-full mt-4">Update Medical History</button>
        </div>
      </div>
    </motion.div>
  );
};

export default Profile;
