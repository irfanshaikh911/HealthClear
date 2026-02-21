import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, ClipboardList, AlertCircle, CheckCircle2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Questionnaire.css';

const Questionnaire = () => {
  const navigate = useNavigate();
  const { completeOnboarding } = useAuth();
  const [step, setStep] = useState(1);
  const totalSteps = 3;

  const [formData, setFormData] = useState({
    name: '', dob: '', gender: '', bloodType: '',
    conditions: '', medications: '', allergies: ''
  });

  const update = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      completeOnboarding(formData);
      navigate('/profile');
    }
  };

  const stepLabels = ['Personal', 'Medical', 'Confirm'];

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
              <span key={label} className={`step-label ${step > i ? 'done' : ''} ${step === i + 1 ? 'current' : ''}`}>
                <span className="step-dot">{step > i + 1 ? '✓' : i + 1}</span>
                {label}
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
                        value={formData.name} onChange={(e) => update('name', e.target.value)} required />
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-dob">Date of Birth</label>
                      <input id="q-dob" type="date" className="input-field"
                        value={formData.dob} onChange={(e) => update('dob', e.target.value)} required />
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-gender">Gender</label>
                      <select id="q-gender" className="input-field"
                        value={formData.gender} onChange={(e) => update('gender', e.target.value)} required>
                        <option value="">Select gender</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                        <option value="prefer-not">Prefer not to say</option>
                      </select>
                    </div>
                    <div className="input-group">
                      <label className="input-label" htmlFor="q-blood">Blood Type</label>
                      <select id="q-blood" className="input-field"
                        value={formData.bloodType} onChange={(e) => update('bloodType', e.target.value)}>
                        <option value="">Select type</option>
                        <option>A+</option><option>A-</option>
                        <option>B+</option><option>B-</option>
                        <option>O+</option><option>O-</option>
                        <option>AB+</option><option>AB-</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="q-card glass-card">
                  <div className="q-card-top">
                    <div className="q-icon-box accent"><ClipboardList size={22} /></div>
                    <h2>Medical History</h2>
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-conditions">Pre-existing Conditions</label>
                    <textarea id="q-conditions" className="input-field" rows="3"
                      placeholder="E.g., Hypertension, Diabetes Type 2..."
                      value={formData.conditions} onChange={(e) => update('conditions', e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-meds">Current Medications</label>
                    <textarea id="q-meds" className="input-field" rows="3"
                      placeholder="List any medications..."
                      value={formData.medications} onChange={(e) => update('medications', e.target.value)} />
                  </div>
                  <div className="q-card-top mt-6">
                    <div className="q-icon-box warning"><AlertCircle size={22} /></div>
                    <h2>Allergies</h2>
                  </div>
                  <div className="input-group">
                    <label className="input-label" htmlFor="q-allergies">Known Allergies</label>
                    <textarea id="q-allergies" className="input-field" rows="3"
                      placeholder="E.g., Penicillin, Latex..."
                      value={formData.allergies} onChange={(e) => update('allergies', e.target.value)} />
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="q-card glass-card q-confirm">
                  <div className="confirm-icon-circle">
                    <CheckCircle2 size={48} />
                  </div>
                  <h2>All Set!</h2>
                  <p>Your profile has been saved securely. You can update your medical history anytime from your dashboard.</p>
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
