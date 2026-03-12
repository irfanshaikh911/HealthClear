import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Bed, Activity, Building2, MapPin, Clock,
    Search, AlertTriangle, CheckCircle2, XCircle,
    RefreshCw, Phone, CalendarCheck, X, User,
    FileText, Send
} from 'lucide-react';
import './ICUBeds.css';

const HOSPITALS_ICU = [
    {
        id: 1,
        name: 'Ruby Hall Clinic',
        city: 'Pune',
        address: 'Sassoon Road, Pune 411001',
        totalBeds: 45,
        available: 8,
        occupied: 37,
        ventilators: { total: 20, available: 4 },
        contact: '+91 20 2616 3391',
        email: 'icu@rubyhall.com',
        lastUpdated: '15 min ago',
    },
    {
        id: 2,
        name: 'Sahyadri Super Speciality Hospital',
        city: 'Pune',
        address: 'Plot 30-C, Karve Road, Pune 411004',
        totalBeds: 60,
        available: 3,
        occupied: 57,
        ventilators: { total: 30, available: 2 },
        contact: '+91 20 6721 4000',
        email: 'icu@sahyadri.com',
        lastUpdated: '10 min ago',
    },
    {
        id: 3,
        name: 'Jehangir Hospital',
        city: 'Pune',
        address: '32, Sassoon Road, Pune 411001',
        totalBeds: 35,
        available: 12,
        occupied: 23,
        ventilators: { total: 15, available: 6 },
        contact: '+91 20 6681 4444',
        email: 'icu@jehangir.com',
        lastUpdated: '5 min ago',
    },
    {
        id: 4,
        name: 'KEM Hospital',
        city: 'Pune',
        address: 'Sardar Moodliar Road, Rasta Peth, Pune 411011',
        totalBeds: 80,
        available: 0,
        occupied: 80,
        ventilators: { total: 35, available: 0 },
        contact: '+91 20 2612 6000',
        email: 'icu@kem.edu.in',
        lastUpdated: '20 min ago',
    },
    {
        id: 5,
        name: 'Deenanath Mangeshkar Hospital',
        city: 'Pune',
        address: 'Erandwane, Pune 411004',
        totalBeds: 50,
        available: 15,
        occupied: 35,
        ventilators: { total: 22, available: 8 },
        contact: '+91 20 4015 1000',
        email: 'icu@dmhospital.org',
        lastUpdated: '8 min ago',
    },
];

const getStatus = (available, total) => {
    const pct = (available / total) * 100;
    if (pct === 0) return { label: 'Full', color: 'var(--color-danger)', bgColor: 'var(--color-danger-muted)', icon: XCircle };
    if (pct <= 15) return { label: 'Critical', color: 'var(--color-warning)', bgColor: 'var(--color-warning-muted)', icon: AlertTriangle };
    return { label: 'Available', color: 'var(--color-success)', bgColor: 'var(--color-success-muted)', icon: CheckCircle2 };
};

const ICUBeds = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [bookingModal, setBookingModal] = useState(null); // hospital object or null
    const [bookingSubmitted, setBookingSubmitted] = useState(false);
    const [formData, setFormData] = useState({ patientName: '', contactNo: '', reason: '', bedType: 'ICU' });

    const filtered = HOSPITALS_ICU.filter((h) =>
        h.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        h.address.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Summary stats
    const totalBeds = HOSPITALS_ICU.reduce((s, h) => s + h.totalBeds, 0);
    const totalAvailable = HOSPITALS_ICU.reduce((s, h) => s + h.available, 0);
    const totalVentAvail = HOSPITALS_ICU.reduce((s, h) => s + h.ventilators.available, 0);
    const occupancyPct = Math.round(((totalBeds - totalAvailable) / totalBeds) * 100);

    const openBooking = (hospital) => {
        setBookingModal(hospital);
        setBookingSubmitted(false);
        setFormData({ patientName: '', contactNo: '', reason: '', bedType: 'ICU' });
    };

    const handleBookingSubmit = (e) => {
        e.preventDefault();
        setBookingSubmitted(true);
    };

    return (
        <motion.div
            className="icu-page"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
            {/* Header */}
            <div className="icu-header animate-in delay-1">
                <div>
                    <h1 className="icu-title"><Bed size={28} /> ICU Beds Availability</h1>
                    <p className="icu-subtitle">Real-time ICU bed and ventilator availability across Pune hospitals</p>
                </div>
                <div className="icu-last-refresh">
                    <RefreshCw size={14} />
                    <span>Last refreshed: just now</span>
                </div>
            </div>

            {/* ── Summary Stats ── */}
            <div className="icu-stats animate-in delay-2">
                <div className="icu-stat-card glass-card">
                    <div className="icu-stat-icon" style={{ background: 'var(--color-primary-muted)', color: 'var(--color-primary)' }}>
                        <Bed size={22} />
                    </div>
                    <div>
                        <span className="icu-stat-value">{totalBeds}</span>
                        <span className="icu-stat-label">Total ICU Beds</span>
                    </div>
                </div>
                <div className="icu-stat-card glass-card">
                    <div className="icu-stat-icon" style={{ background: 'var(--color-success-muted)', color: 'var(--color-success)' }}>
                        <CheckCircle2 size={22} />
                    </div>
                    <div>
                        <span className="icu-stat-value">{totalAvailable}</span>
                        <span className="icu-stat-label">Available Now</span>
                    </div>
                </div>
                <div className="icu-stat-card glass-card">
                    <div className="icu-stat-icon" style={{ background: 'var(--color-warning-muted)', color: 'var(--color-warning)' }}>
                        <Activity size={22} />
                    </div>
                    <div>
                        <span className="icu-stat-value">{occupancyPct}%</span>
                        <span className="icu-stat-label">Occupancy Rate</span>
                    </div>
                </div>
                <div className="icu-stat-card glass-card">
                    <div className="icu-stat-icon" style={{ background: 'var(--color-accent-muted)', color: 'var(--color-accent)' }}>
                        <Activity size={22} />
                    </div>
                    <div>
                        <span className="icu-stat-value">{totalVentAvail}</span>
                        <span className="icu-stat-label">Ventilators Free</span>
                    </div>
                </div>
            </div>

            {/* ── Search ── */}
            <div className="icu-search-wrap glass-panel animate-in delay-3">
                <Search size={18} className="icu-search-icon" />
                <input
                    type="text"
                    className="icu-search-input"
                    placeholder="Search hospitals by name or address..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* ── Hospital Cards ── */}
            <div className="icu-hospital-list">
                {filtered.map((h, i) => {
                    const bedStatus = getStatus(h.available, h.totalBeds);
                    const ventStatus = getStatus(h.ventilators.available, h.ventilators.total);
                    const BedIcon = bedStatus.icon;
                    const occupancy = Math.round(((h.totalBeds - h.available) / h.totalBeds) * 100);
                    const isFull = h.available === 0;

                    return (
                        <motion.div
                            key={h.id}
                            className="icu-hospital-card glass-card"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.08 }}
                        >
                            <div className="icu-card-header">
                                <div className="icu-card-info">
                                    <div className="icu-hospital-icon">
                                        <Building2 size={20} />
                                    </div>
                                    <div>
                                        <h3 className="icu-hospital-name">{h.name}</h3>
                                        <p className="icu-hospital-address"><MapPin size={13} /> {h.address}</p>
                                    </div>
                                </div>
                                <div className="icu-status-badge" style={{ background: bedStatus.bgColor, color: bedStatus.color }}>
                                    <BedIcon size={13} />
                                    <span>{bedStatus.label}</span>
                                </div>
                            </div>

                            <div className="icu-card-body">
                                {/* ICU Beds */}
                                <div className="icu-metric-block">
                                    <div className="icu-metric-header">
                                        <span className="icu-metric-title"><Bed size={14} /> ICU Beds</span>
                                        <span className="icu-metric-count" style={{ color: bedStatus.color }}>
                                            {h.available} / {h.totalBeds} available
                                        </span>
                                    </div>
                                    <div className="icu-bar">
                                        <div
                                            className="icu-bar-fill"
                                            style={{
                                                width: `${occupancy}%`,
                                                background: occupancy === 100 ? 'var(--color-danger)' : occupancy > 85 ? 'var(--color-warning)' : 'var(--color-success)'
                                            }}
                                        />
                                    </div>
                                    <div className="icu-bar-labels">
                                        <span>{h.occupied} occupied</span>
                                        <span>{occupancy}% full</span>
                                    </div>
                                </div>

                                {/* Ventilators */}
                                <div className="icu-metric-block">
                                    <div className="icu-metric-header">
                                        <span className="icu-metric-title"><Activity size={14} /> Ventilators</span>
                                        <span className="icu-metric-count" style={{ color: ventStatus.color }}>
                                            {h.ventilators.available} / {h.ventilators.total} available
                                        </span>
                                    </div>
                                    <div className="icu-bar">
                                        <div
                                            className="icu-bar-fill"
                                            style={{
                                                width: `${Math.round(((h.ventilators.total - h.ventilators.available) / h.ventilators.total) * 100)}%`,
                                                background: h.ventilators.available === 0 ? 'var(--color-danger)' :
                                                    h.ventilators.available <= 3 ? 'var(--color-warning)' : 'var(--color-accent)'
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* ── Action Buttons ── */}
                            <div className="icu-card-actions">
                                <button
                                    className={`btn btn-primary icu-book-btn ${isFull ? 'disabled' : ''}`}
                                    onClick={() => !isFull && openBooking(h)}
                                    disabled={isFull}
                                >
                                    <CalendarCheck size={16} />
                                    {isFull ? 'No Beds Available' : 'Book / Reserve'}
                                </button>
                                <a href={`tel:${h.contact.replace(/\s/g, '')}`} className="btn btn-secondary icu-call-btn">
                                    <Phone size={16} />
                                    Call Hospital
                                </a>
                            </div>

                            <div className="icu-card-footer">
                                <span className="icu-updated"><Clock size={12} /> Updated {h.lastUpdated}</span>
                                <span className="icu-contact"><Phone size={12} /> {h.contact}</span>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {filtered.length === 0 && (
                <div className="icu-empty glass-card">
                    <Search size={40} />
                    <h3>No hospitals found</h3>
                    <p>Try adjusting your search criteria.</p>
                </div>
            )}

            {/* ══════════ BOOKING MODAL ══════════ */}
            <AnimatePresence>
                {bookingModal && (
                    <motion.div
                        className="icu-modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setBookingModal(null)}
                    >
                        <motion.div
                            className="icu-modal glass-card"
                            initial={{ opacity: 0, scale: 0.92, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.92, y: 20 }}
                            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button className="icu-modal-close" onClick={() => setBookingModal(null)} aria-label="Close">
                                <X size={20} />
                            </button>

                            {!bookingSubmitted ? (
                                <>
                                    <div className="icu-modal-header">
                                        <div className="icu-modal-badge">
                                            <CalendarCheck size={14} />
                                            <span>Book ICU Bed</span>
                                        </div>
                                        <h2>{bookingModal.name}</h2>
                                        <p className="icu-modal-address"><MapPin size={14} /> {bookingModal.address}</p>
                                        <div className="icu-modal-avail">
                                            <span className="badge badge-success">{bookingModal.available} beds available</span>
                                            <span className="badge badge-accent">{bookingModal.ventilators.available} ventilators free</span>
                                        </div>
                                    </div>

                                    <form className="icu-modal-form" onSubmit={handleBookingSubmit}>
                                        <div className="input-group">
                                            <label className="input-label">Patient Name</label>
                                            <div className="icu-input-wrap">
                                                <User size={16} className="icu-form-icon" />
                                                <input
                                                    type="text"
                                                    className="input-field icu-form-input"
                                                    placeholder="Full name of the patient"
                                                    required
                                                    value={formData.patientName}
                                                    onChange={(e) => setFormData({ ...formData, patientName: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <div className="input-group">
                                            <label className="input-label">Contact Number</label>
                                            <div className="icu-input-wrap">
                                                <Phone size={16} className="icu-form-icon" />
                                                <input
                                                    type="tel"
                                                    className="input-field icu-form-input"
                                                    placeholder="+91 XXXXX XXXXX"
                                                    required
                                                    value={formData.contactNo}
                                                    onChange={(e) => setFormData({ ...formData, contactNo: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <div className="input-group">
                                            <label className="input-label">Bed Type</label>
                                            <select
                                                className="input-field"
                                                value={formData.bedType}
                                                onChange={(e) => setFormData({ ...formData, bedType: e.target.value })}
                                            >
                                                <option value="ICU">ICU Bed</option>
                                                <option value="ICU+Ventilator">ICU + Ventilator</option>
                                                <option value="HDU">HDU (High Dependency Unit)</option>
                                            </select>
                                        </div>

                                        <div className="input-group">
                                            <label className="input-label">Reason / Condition</label>
                                            <div className="icu-input-wrap">
                                                <FileText size={16} className="icu-form-icon" />
                                                <input
                                                    type="text"
                                                    className="input-field icu-form-input"
                                                    placeholder="Brief description of medical condition"
                                                    value={formData.reason}
                                                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <div className="icu-modal-actions">
                                            <button type="submit" className="btn btn-primary w-full">
                                                <Send size={16} /> Submit Booking Request
                                            </button>
                                            <button type="button" className="btn btn-secondary w-full" onClick={() => setBookingModal(null)}>
                                                Cancel
                                            </button>
                                        </div>
                                    </form>

                                    <div className="icu-modal-contact-info">
                                        <p>For emergencies, call directly:</p>
                                        <a href={`tel:${bookingModal.contact.replace(/\s/g, '')}`} className="icu-modal-phone">
                                            <Phone size={16} /> {bookingModal.contact}
                                        </a>
                                    </div>
                                </>
                            ) : (
                                <div className="icu-booking-success">
                                    <div className="icu-success-icon">
                                        <CheckCircle2 size={48} />
                                    </div>
                                    <h2>Booking Request Submitted!</h2>
                                    <p>Your ICU bed reservation request for <strong>{bookingModal.name}</strong> has been received.</p>
                                    <div className="icu-success-details glass-subtle">
                                        <div className="icu-success-row">
                                            <span>Patient</span>
                                            <strong>{formData.patientName}</strong>
                                        </div>
                                        <div className="icu-success-row">
                                            <span>Contact</span>
                                            <strong>{formData.contactNo}</strong>
                                        </div>
                                        <div className="icu-success-row">
                                            <span>Bed Type</span>
                                            <strong>{formData.bedType}</strong>
                                        </div>
                                        <div className="icu-success-row">
                                            <span>Status</span>
                                            <span className="badge badge-warning">Pending Confirmation</span>
                                        </div>
                                    </div>
                                    <p className="icu-success-note">The hospital will contact you within 30 minutes to confirm availability.</p>
                                    <button className="btn btn-primary" onClick={() => setBookingModal(null)}>
                                        Done
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default ICUBeds;
