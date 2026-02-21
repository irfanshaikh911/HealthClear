import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  User, Heart, Droplets, Ruler, Weight, Activity, Shield,
  Pill, AlertTriangle, FileText, ChevronRight, Mail, Calendar
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Settings.css';

const Settings = () => {
  const { user } = useAuth();
  const name = user?.full_name || user?.name || 'User';

  const bloodType = user?.blood_type || user?.bloodType;
  const gender = user?.gender;
  const dob = user?.date_of_birth;
  const heightCm = parseFloat(user?.height_cm);
  const weightKg = parseFloat(user?.weight_kg);
  const bmi = heightCm && weightKg ? (weightKg / ((heightCm / 100) ** 2)).toFixed(1) : null;
  const bmiCategory = bmi
    ? bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese'
    : null;

  const allergies = user?.allergies;
  const medications = user?.medications;
  const medicalHistory = user?.medical_history || (user?.conditions ? user.conditions.join(', ') : null);

  return (
    <motion.div
      className="settings-page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* ============ PROFILE CARD ============ */}
      <div className="settings-profile-card glass-card animate-in delay-1">
        <div className="settings-avatar">
          <User size={36} strokeWidth={1.5} />
        </div>
        <div className="settings-profile-info">
          <h1>{name}</h1>
          <p className="settings-email"><Mail size={14} /> {user?.email || 'No email on file'}</p>
          {dob && <p className="settings-dob"><Calendar size={14} /> Born {dob}</p>}
        </div>
        <div className="settings-profile-badge">
          <Shield size={14} /> Profile Complete
        </div>
      </div>

      {/* ============ VITALS ============ */}
      <h2 className="settings-section-title animate-in delay-2">Health Vitals</h2>
      <div className="vitals-grid animate-in delay-2">
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

      {/* ============ MEDICAL HISTORY ============ */}
      <h2 className="settings-section-title animate-in delay-3">Medical History</h2>
      <div className="glass-card settings-med-card animate-in delay-3">
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
              <span className="med-row-label">Current Medications</span>
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
          <p className="med-empty">No medical history recorded yet. Complete the questionnaire to add your details.</p>
        )}

        <Link to="/questionnaire" className="btn btn-secondary w-full mt-4">
          <ChevronRight size={16} /> Update Medical Information
        </Link>
      </div>
    </motion.div>
  );
};

export default Settings;
