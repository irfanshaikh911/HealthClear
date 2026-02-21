import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import {
  User, MessageSquare, Search, FileText, Activity, Heart,
  Droplets, Ruler, Weight, Shield, ChevronRight, ArrowRight,
  Sparkles, Clock, Pill, AlertTriangle, Send
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const name = user?.full_name || user?.name || 'User';
  const [assistantInput, setAssistantInput] = useState('');

  const handleAssistantSubmit = (e) => {
    e.preventDefault();
    if (assistantInput.trim()) {
      navigate('/assistant', { state: { initialMessage: assistantInput } });
    }
  };

  const quickPrompts = [
    'What treatments are available for chronic back pain?',
    'Compare MRI costs near me',
    'Explain my recent lab results',
    'Find affordable physical therapy',
  ];

  // Compute BMI if height and weight exist
  const heightCm = parseFloat(user?.height_cm);
  const weightKg = parseFloat(user?.weight_kg);
  const bmi = heightCm && weightKg ? (weightKg / ((heightCm / 100) ** 2)).toFixed(1) : null;
  const bmiCategory = bmi
    ? bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese'
    : null;

  const bloodType = user?.blood_type || user?.bloodType;
  const gender = user?.gender;
  const allergies = user?.allergies;
  const medications = user?.medications;
  const medicalHistory = user?.medical_history || (user?.conditions ? user.conditions.join(', ') : null);

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
        <div className="dash-header-actions">
          <Link to="/find-treatment" className="btn btn-secondary btn-sm">
            <Search size={16} /> Find Treatment
          </Link>
        </div>
      </div>

      {/* ============ ASSISTANT HERO ============ */}
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
            <input
              type="text"
              className="assistant-input"
              placeholder="Ask about treatments, costs, medications..."
              value={assistantInput}
              onChange={(e) => setAssistantInput(e.target.value)}
            />
            <button type="submit" className="assistant-send-btn" aria-label="Send">
              <Send size={18} />
            </button>
          </div>
        </form>
        <div className="assistant-prompts">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              className="prompt-chip"
              onClick={() => navigate('/assistant', { state: { initialMessage: prompt } })}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* ============ VITALS BENTO ============ */}
      <div className="vitals-grid animate-in delay-3">
        <div className="vital-card glass-card">
          <div className="vital-icon-wrap primary"><Heart size={20} /></div>
          <div className="vital-info">
            <span className="vital-label">Blood Type</span>
            <span className="vital-value">{bloodType || '—'}</span>
          </div>
        </div>

        <div className="vital-card glass-card">
          <div className="vital-icon-wrap accent"><Droplets size={20} /></div>
          <div className="vital-info">
            <span className="vital-label">Gender</span>
            <span className="vital-value">{gender || '—'}</span>
          </div>
        </div>

        <div className="vital-card glass-card">
          <div className="vital-icon-wrap success"><Ruler size={20} /></div>
          <div className="vital-info">
            <span className="vital-label">Height</span>
            <span className="vital-value">{user?.height_cm ? `${user.height_cm} cm` : '—'}</span>
          </div>
        </div>

        <div className="vital-card glass-card">
          <div className="vital-icon-wrap warning"><Weight size={20} /></div>
          <div className="vital-info">
            <span className="vital-label">Weight</span>
            <span className="vital-value">{user?.weight_kg ? `${user.weight_kg} kg` : '—'}</span>
          </div>
        </div>

        {bmi && (
          <div className="vital-card glass-card vital-wide">
            <div className="vital-icon-wrap cta"><Activity size={20} /></div>
            <div className="vital-info">
              <span className="vital-label">BMI</span>
              <span className="vital-value">{bmi} <small className="bmi-cat">{bmiCategory}</small></span>
            </div>
            <div className="bmi-bar">
              <div className="bmi-fill" style={{ width: `${Math.min((bmi / 40) * 100, 100)}%` }} />
            </div>
          </div>
        )}

        {user?.organ_donor && (
          <div className="vital-card glass-card">
            <div className="vital-icon-wrap primary"><Shield size={20} /></div>
            <div className="vital-info">
              <span className="vital-label">Organ Donor</span>
              <span className="vital-value">✓ Registered</span>
            </div>
          </div>
        )}
      </div>

      {/* ============ LOWER GRID ============ */}
      <div className="dash-lower-grid">
        {/* Medical Profile */}
        <div className="glass-card dash-section animate-in delay-4">
          <div className="section-top">
            <h2><Pill size={18} /> Medical Profile</h2>
          </div>

          {allergies && (
            <div className="med-row">
              <div className="med-row-icon warning"><AlertTriangle size={16} /></div>
              <div className="med-row-body">
                <span className="med-row-label">Allergies</span>
                <p className="med-row-value">{allergies}</p>
              </div>
            </div>
          )}

          {medications && (
            <div className="med-row">
              <div className="med-row-icon accent"><Pill size={16} /></div>
              <div className="med-row-body">
                <span className="med-row-label">Medications</span>
                <p className="med-row-value">{medications}</p>
              </div>
            </div>
          )}

          {medicalHistory && (
            <div className="med-row">
              <div className="med-row-icon primary"><FileText size={16} /></div>
              <div className="med-row-body">
                <span className="med-row-label">Medical History</span>
                <p className="med-row-value">{medicalHistory}</p>
              </div>
            </div>
          )}

          {!allergies && !medications && !medicalHistory && (
            <p className="med-empty">No medical history recorded yet.</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="glass-card dash-section animate-in delay-4">
          <h2>Quick Actions</h2>
          <div className="action-list">
            <Link to="/assistant" className="action-row">
              <div className="action-icon-box primary"><MessageSquare size={20} /></div>
              <div className="action-text">
                <h4>Health Assistant</h4>
                <p>Ask about treatments, costs & medications</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
            <Link to="/find-treatment" className="action-row">
              <div className="action-icon-box accent"><Search size={20} /></div>
              <div className="action-text">
                <h4>Find Treatment</h4>
                <p>Compare providers and costs near you</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
            <Link to="/bill-analysis" className="action-row">
              <div className="action-icon-box muted"><FileText size={20} /></div>
              <div className="action-text">
                <h4>Analyze a Bill</h4>
                <p>Upload and verify medical invoices</p>
              </div>
              <ChevronRight size={18} className="action-chev" />
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-card dash-section animate-in delay-5">
          <div className="section-top">
            <h2><Clock size={18} /> Recent Activity</h2>
          </div>
          <div className="activity-feed">
            <div className="activity-item">
              <div className="activity-dot primary" />
              <div className="activity-body">
                <h4>Asked about knee surgery options</h4>
                <p>Received 3 treatment plans with cost estimates</p>
              </div>
              <span className="activity-time"><Clock size={12} /> 1d ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-dot accent" />
              <div className="activity-body">
                <h4>Found physical therapy providers</h4>
                <p>Compared 5 options near your area</p>
              </div>
              <span className="activity-time"><Clock size={12} /> 3d ago</span>
            </div>
            <div className="activity-item">
              <div className="activity-dot cta" />
              <div className="activity-body">
                <h4>Medication interaction check</h4>
                <p>All clear — no conflicts detected</p>
              </div>
              <span className="activity-time"><Clock size={12} /> 1w ago</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Profile;
