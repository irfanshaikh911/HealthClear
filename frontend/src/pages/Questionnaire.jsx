import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, Ruler, Weight, Heart, ClipboardList,
  AlertCircle, CheckCircle2, ChevronLeft, ChevronRight, Pill, Stethoscope
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Questionnaire.css';

const Questionnaire = () => {
  const navigate = useNavigate();
  const { user, completeOnboarding } = useAuth();
  const [step, setStep] = useState(1);
  const totalSteps = 4;

  // Fields mapped directly to DDL schema
  const [formData, setFormData] = useState({
    // patients table
    full_name: user?.name || '',
    date_of_birth: '',
    gender: '',
    is_pregnant: false,
    blood_type: '',
    height_cm: '',
    weight_kg: '',
    allergies: '',
    medications: '',
    medical_history: '',
    organ_donor: false,
  });

  const update = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      await completeOnboarding(formData);
      navigate('/profile');
    }
  };

  const stepLabels = ['Personal', 'Body & Lifestyle', 'Medical', 'Confirm'];

  const showPregnancy = formData.gender === 'Female';

  return (
    <div className="q-page">
      <motion.div
        className="q-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="q-header animate-in delay-1">
          <h1>Complete Your Profile</h1>
          <p>Help us personalize your HealthClear experience.</p>
        </div>

        {/* Progress */}
        <div className="q-progress animate-in delay-2">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${(step / totalSteps) * 100}%` }} />
          </div>
          <div className="step-labels">
            {stepLabels.map((label, i) => (
              <span key={label} className={`step-label ${step > i + 1 ? 'done' : ''} ${step === i + 1 ? 'current' : ''}`}>
                <span className="step-dot">{step > i + 1 ? '✓' : i + 1}</span>
                <span className="step-text">{label}</span>
              </span>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ duration: 0.3 }}
            >
              {/* ============ STEP 1: Personal Details ============ */}
              {step === 1 && (
                <div className="q-card glass-card">
                  <div className="q-card-top">
                    <div className="q-icon-box primary"><User size={22} /></div>
                    <h2>Personal Details</h2>
                  </div>
                  <div className="q-grid">
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-name">Full Name</label>
                      <input id="q-name" type="text" className="input-field" placeholder="Alex Johnson"
                        value={formData.full_name} onChange={(e) => update('full_name', e.target.value)} required />
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-dob">Date of Birth</label>
                      <input id="q-dob" type="date" className="input-field"
                        value={formData.date_of_birth} onChange={(e) => update('date_of_birth', e.target.value)} required />
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-gender">Gender</label>
                      <select id="q-gender" className="input-field"
                        value={formData.gender} onChange={(e) => update('gender', e.target.value)} required>
                        <option value="">Select gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-blood">Blood Type</label>
                      <select id="q-blood" className="input-field"
                        value={formData.blood_type} onChange={(e) => update('blood_type', e.target.value)}>
                        <option value="">Select type</option>
                        <option value="A+">A+</option><option value="A-">A-</option>
                        <option value="B+">B+</option><option value="B-">B-</option>
                        <option value="O+">O+</option><option value="O-">O-</option>
                        <option value="AB+">AB+</option><option value="AB-">AB-</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* ============ STEP 2: Body & Lifestyle ============ */}
              {step === 2 && (
                <div className="q-card glass-card">
                  <div className="q-card-top">
                    <div className="q-icon-box accent"><Ruler size={22} /></div>
                    <h2>Body & Lifestyle</h2>
                  </div>
                  <div className="q-grid">
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-height">Height (cm)</label>
                      <div className="input-with-icon">
                        <Ruler className="field-icon" size={18} aria-hidden="true" />
                        <input id="q-height" type="number" className="input-field" placeholder="170"
                          min="50" max="250" step="0.01"
                          value={formData.height_cm} onChange={(e) => update('height_cm', e.target.value)} />
                      </div>
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-weight">Weight (kg)</label>
                      <div className="input-with-icon">
                        <Weight className="field-icon" size={18} aria-hidden="true" />
                        <input id="q-weight" type="number" className="input-field" placeholder="70"
                          min="10" max="500" step="0.01"
                          value={formData.weight_kg} onChange={(e) => update('weight_kg', e.target.value)} />
                      </div>
                    </div>
                  </div>

                  {showPregnancy && (
                    <div className="q-toggle-group">
                      <label className="q-toggle-label" htmlFor="q-pregnant">
                        <Heart size={18} className="q-toggle-icon" />
                        <span>Currently Pregnant</span>
                      </label>
                      <label className="toggle-switch">
                        <input id="q-pregnant" type="checkbox"
                          checked={formData.is_pregnant}
                          onChange={(e) => update('is_pregnant', e.target.checked)} />
                        <span className="toggle-slider"></span>
                      </label>
                    </div>
                  )}

                  <div className="q-toggle-group">
                    <label className="q-toggle-label" htmlFor="q-donor">
                      <Stethoscope size={18} className="q-toggle-icon" />
                      <span>Organ Donor</span>
                    </label>
                    <label className="toggle-switch">
                      <input id="q-donor" type="checkbox"
                        checked={formData.organ_donor}
                        onChange={(e) => update('organ_donor', e.target.checked)} />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>
                </div>
              )}

              {/* ============ STEP 3: Medical History ============ */}
              {step === 3 && (
                <div className="q-card glass-card">
                  <div className="q-card-top">
                    <div className="q-icon-box primary"><ClipboardList size={22} /></div>
                    <h2>Medical History</h2>
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-history">Pre-existing Conditions / Medical History</label>
                    <textarea id="q-history" className="input-field" rows="3"
                      placeholder="E.g., Hypertension, Diabetes Type 2, Previous surgeries..."
                      value={formData.medical_history} onChange={(e) => update('medical_history', e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-meds">
                      <Pill size={14} style={{ display: 'inline', marginRight: '0.3rem', verticalAlign: 'text-bottom' }} />
                      Current Medications
                    </label>
                    <textarea id="q-meds" className="input-field" rows="3"
                      placeholder="List any medications you're currently taking..."
                      value={formData.medications} onChange={(e) => update('medications', e.target.value)} />
                  </div>
                  <div className="q-card-top mt-6">
                    <div className="q-icon-box warning"><AlertCircle size={22} /></div>
                    <h2>Allergies</h2>
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-allergies">Known Allergies</label>
                    <textarea id="q-allergies" className="input-field" rows="3"
                      placeholder="E.g., Penicillin, Latex, Shellfish..."
                      value={formData.allergies} onChange={(e) => update('allergies', e.target.value)} />
                  </div>
                </div>
              )}

              {/* ============ STEP 4: Confirmation ============ */}
              {step === 4 && (
                <div className="q-card glass-card">
                  <div className="q-confirm">
                    <div className="confirm-icon-circle">
                      <CheckCircle2 size={48} />
                    </div>
                    <h2>All Set!</h2>
                    <p>Your health profile is ready. You can update it anytime from your dashboard.</p>
                  </div>

                  <div className="q-summary">
                    <h3>Profile Summary</h3>
                    <div className="q-summary-grid">
                      <div className="q-summary-item">
                        <span className="q-summary-label">Name</span>
                        <span className="q-summary-value">{formData.full_name || '—'}</span>
                      </div>
                      <div className="q-summary-item">
                        <span className="q-summary-label">Date of Birth</span>
                        <span className="q-summary-value">{formData.date_of_birth || '—'}</span>
                      </div>
                      <div className="q-summary-item">
                        <span className="q-summary-label">Gender</span>
                        <span className="q-summary-value">{formData.gender || '—'}</span>
                      </div>
                      <div className="q-summary-item">
                        <span className="q-summary-label">Blood Type</span>
                        <span className="q-summary-value">{formData.blood_type || '—'}</span>
                      </div>
                      <div className="q-summary-item">
                        <span className="q-summary-label">Height</span>
                        <span className="q-summary-value">{formData.height_cm ? `${formData.height_cm} cm` : '—'}</span>
                      </div>
                      <div className="q-summary-item">
                        <span className="q-summary-label">Weight</span>
                        <span className="q-summary-value">{formData.weight_kg ? `${formData.weight_kg} kg` : '—'}</span>
                      </div>
                      {showPregnancy && (
                        <div className="q-summary-item">
                          <span className="q-summary-label">Pregnant</span>
                          <span className="q-summary-value">{formData.is_pregnant ? 'Yes' : 'No'}</span>
                        </div>
                      )}
                      <div className="q-summary-item">
                        <span className="q-summary-label">Organ Donor</span>
                        <span className="q-summary-value">{formData.organ_donor ? 'Yes' : 'No'}</span>
                      </div>
                    </div>
                    {formData.medical_history && (
                      <div className="q-summary-block">
                        <span className="q-summary-label">Medical History</span>
                        <p className="q-summary-text">{formData.medical_history}</p>
                      </div>
                    )}
                    {formData.medications && (
                      <div className="q-summary-block">
                        <span className="q-summary-label">Medications</span>
                        <p className="q-summary-text">{formData.medications}</p>
                      </div>
                    )}
                    {formData.allergies && (
                      <div className="q-summary-block">
                        <span className="q-summary-label">Allergies</span>
                        <p className="q-summary-text">{formData.allergies}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <div className="q-actions">
            {step > 1 && (
              <button type="button" className="btn btn-secondary" onClick={() => setStep(step - 1)}>
                <ChevronLeft size={18} /> Back
              </button>
            )}
            <button type="submit" className="btn btn-primary" style={{ marginLeft: 'auto' }}>
              {step === totalSteps ? 'Go to Dashboard' : 'Continue'} <ChevronRight size={18} />
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

export default Questionnaire;
