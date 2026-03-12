import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    HandHeart, Search, Filter, ExternalLink,
    Building2, Landmark, Users, TrendingUp,
    Heart, ArrowRight
} from 'lucide-react';
import './Fundraisers.css';

const FUNDRAISERS = [
    {
        id: 1,
        name: 'Cancer Treatment Support Fund',
        organizer: 'Mukul Madhav Foundation',
        type: 'NGO',
        description: 'Supporting underprivileged cancer patients with chemotherapy, radiation, and surgical expenses across Maharashtra.',
        target: 5000000,
        raised: 3750000,
        beneficiaries: 142,
        category: 'Cancer Care',
        website: '#',
        featured: true,
    },
    {
        id: 2,
        name: 'PM National Relief Fund — Health',
        organizer: 'Government of India',
        type: 'Government',
        description: 'National-level fund for citizens requiring urgent medical treatment. Covers surgeries, transplants, and critical care.',
        target: 100000000,
        raised: 78000000,
        beneficiaries: 12450,
        category: 'Critical Care',
        website: '#',
        featured: true,
    },
    {
        id: 3,
        name: 'Child Heart Surgery Program',
        organizer: 'Punit Balan Group',
        type: 'Private',
        description: 'Funding pediatric cardiac surgeries for children from low-income families in Pune and surrounding districts.',
        target: 3000000,
        raised: 2100000,
        beneficiaries: 67,
        category: 'Pediatric Care',
        website: '#',
        featured: true,
    },
    {
        id: 4,
        name: 'Rural Health Infrastructure Fund',
        organizer: 'Poonawalla Foundation',
        type: 'Private',
        description: 'Building and equipping primary health centers in rural Maharashtra. Includes mobile health units and telemedicine.',
        target: 20000000,
        raised: 14500000,
        beneficiaries: 8900,
        category: 'Infrastructure',
        website: '#',
        featured: false,
    },
    {
        id: 5,
        name: 'Maharashtra CM Relief Fund — Medical',
        organizer: 'Govt. of Maharashtra',
        type: 'Government',
        description: 'State-level medical assistance for BPL families. Covers hospitalization, surgeries, and post-operative care costs.',
        target: 50000000,
        raised: 32000000,
        beneficiaries: 5670,
        category: 'Medical Aid',
        website: '#',
        featured: false,
    },
    {
        id: 6,
        name: 'Organ Transplant Support Initiative',
        organizer: 'Sahyadri Foundation',
        type: 'NGO',
        description: 'Financial assistance for organ transplant patients. Covers pre-transplant evaluation, surgery, and 6-month follow-up.',
        target: 8000000,
        raised: 4200000,
        beneficiaries: 34,
        category: 'Transplants',
        website: '#',
        featured: false,
    },
    {
        id: 7,
        name: 'Mental Health Awareness Drive',
        organizer: 'Vandrevala Foundation',
        type: 'NGO',
        description: 'Free counseling sessions, mental health helpline operations, and community workshops across Pune.',
        target: 2000000,
        raised: 1350000,
        beneficiaries: 3200,
        category: 'Mental Health',
        website: '#',
        featured: false,
    },
    {
        id: 8,
        name: 'Dialysis Support — Free Treatment',
        organizer: 'NephroPlus × Rotary Club Pune',
        type: 'Private',
        description: 'Offering free dialysis sessions for chronic kidney disease patients who cannot afford regular treatment.',
        target: 4000000,
        raised: 2900000,
        beneficiaries: 89,
        category: 'Kidney Care',
        website: '#',
        featured: true,
    },
];

const TABS = ['All', 'Government', 'Private', 'NGO'];
const typeIcons = { Government: Landmark, Private: Building2, NGO: Users };

const MedicalDeals = () => {
    const [activeTab, setActiveTab] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');

    const filtered = FUNDRAISERS.filter((f) => {
        const matchTab = activeTab === 'All' || f.type === activeTab;
        const matchSearch = f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            f.organizer.toLowerCase().includes(searchQuery.toLowerCase());
        return matchTab && matchSearch;
    });

    const formatAmount = (n) => {
        if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)} Cr`;
        if (n >= 100000) return `₹${(n / 100000).toFixed(1)} L`;
        return `₹${n.toLocaleString()}`;
    };

    return (
        <motion.div
            className="fund-page"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
            {/* Header */}
            <div className="fund-header animate-in delay-1">
                <div>
                    <h1 className="fund-title"><HandHeart size={28} /> Fundraisers & Schemes</h1>
                    <p className="fund-subtitle">Discover government, private, and NGO healthcare funding — contribute or raise funds</p>
                </div>
            </div>

            {/* ── Raise a Fund CTA ── */}
            <div className="fund-cta-card glass-card animate-in delay-2">
                <div className="fund-cta-glow" aria-hidden="true" />
                <div className="fund-cta-content">
                    <div className="fund-cta-badge">
                        <Heart size={14} />
                        <span>Start a Fundraiser</span>
                    </div>
                    <h2>Need help with medical expenses?</h2>
                    <p>Raise a fund for yourself or a loved one. Thousands of donors are ready to help with medical bills, surgeries, and treatments.</p>
                    <button className="btn btn-cta fund-cta-btn">
                        Raise a Fund <ArrowRight size={16} />
                    </button>
                </div>
                <div className="fund-cta-stats">
                    <div className="fund-cta-stat">
                        <strong>₹12.5 Cr+</strong>
                        <span>Raised on platform</span>
                    </div>
                    <div className="fund-cta-stat">
                        <strong>30K+</strong>
                        <span>Beneficiaries helped</span>
                    </div>
                    <div className="fund-cta-stat">
                        <strong>450+</strong>
                        <span>Active campaigns</span>
                    </div>
                </div>
            </div>

            {/* ── Search & Tabs ── */}
            <div className="fund-controls animate-in delay-3">
                <div className="fund-search-wrap glass-panel">
                    <Search size={18} className="fund-search-icon" />
                    <input
                        type="text"
                        className="fund-search-input"
                        placeholder="Search funds by name or organizer..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="fund-tabs">
                    <Filter size={16} className="fund-filter-icon" />
                    {TABS.map((tab) => (
                        <button
                            key={tab}
                            className={`fund-tab ${activeTab === tab ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* ── Fund Grid ── */}
            <div className="fund-grid">
                {filtered.map((f, i) => {
                    const progress = Math.round((f.raised / f.target) * 100);
                    const TypeIcon = typeIcons[f.type] || Users;
                    return (
                        <motion.div
                            key={f.id}
                            className="fund-card glass-card"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.06 }}
                        >
                            {f.featured && <span className="fund-featured-badge">Featured</span>}
                            <div className="fund-card-top">
                                <span className="fund-type-badge" data-type={f.type.toLowerCase()}>
                                    <TypeIcon size={12} /> {f.type}
                                </span>
                                <span className="fund-cat-label">{f.category}</span>
                            </div>
                            <h3 className="fund-card-name">{f.name}</h3>
                            <p className="fund-card-organizer">{f.organizer}</p>
                            <p className="fund-card-desc">{f.description}</p>

                            {/* Progress */}
                            <div className="fund-progress-section">
                                <div className="fund-progress-bar">
                                    <div className="fund-progress-fill" style={{ width: `${Math.min(progress, 100)}%` }} />
                                </div>
                                <div className="fund-progress-labels">
                                    <span className="fund-raised">{formatAmount(f.raised)} raised</span>
                                    <span className="fund-target">of {formatAmount(f.target)}</span>
                                </div>
                            </div>

                            <div className="fund-card-bottom">
                                <div className="fund-beneficiaries">
                                    <TrendingUp size={14} />
                                    <span>{f.beneficiaries.toLocaleString()} beneficiaries</span>
                                </div>
                                <button className="btn btn-primary fund-contribute-btn">
                                    Contribute <ExternalLink size={14} />
                                </button>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {filtered.length === 0 && (
                <div className="fund-empty glass-card">
                    <Search size={40} />
                    <h3>No fundraisers found</h3>
                    <p>Try adjusting your search or filter criteria.</p>
                </div>
            )}
        </motion.div>
    );
};

export default MedicalDeals;
