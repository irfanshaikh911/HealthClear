import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Tag, ChevronLeft, ChevronRight, Clock, MapPin,
  Percent, Heart, Pill, FlaskConical, Syringe,
  Stethoscope, BadgePercent, Sparkles
} from 'lucide-react';
import './MedicalDeals.css';

const DEALS = [
  {
    id: 1,
    title: '50% Off Full Body Health Checkup',
    provider: 'Ruby Hall Clinic, Pune',
    category: 'Health Checkup',
    originalPrice: 4000,
    discountedPrice: 2000,
    discount: 50,
    validTill: 'Mar 15, 2026',
    description: 'Complete health screening including blood work, ECG, chest X-ray, and physician consultation. Walk-in available.',
    icon: Stethoscope,
    color: 'var(--color-primary)',
    featured: true,
  },
  {
    id: 2,
    title: 'Free Blood Donation Camp — Get Free CBC Report',
    provider: 'Sahyadri Hospital × Red Cross',
    category: 'Blood Donation',
    originalPrice: 800,
    discountedPrice: 0,
    discount: 100,
    validTill: 'Mar 5, 2026',
    description: 'Donate blood and receive a complimentary CBC test report. Refreshments and certificate provided.',
    icon: Heart,
    color: 'var(--color-danger)',
    featured: true,
  },
  {
    id: 3,
    title: '30% Off on All Prescription Medicines',
    provider: 'MedPlus Pharmacy, Pune',
    category: 'Pharmacy',
    originalPrice: null,
    discountedPrice: null,
    discount: 30,
    validTill: 'Feb 28, 2026',
    description: 'Flat 30% discount on all prescription medicines. Applicable on orders above ₹500. Home delivery available.',
    icon: Pill,
    color: 'var(--color-accent)',
    featured: false,
  },
  {
    id: 4,
    title: 'Diabetes Management Workshop — ₹299 Only',
    provider: 'Jehangir Hospital, Pune',
    category: 'Workshop',
    originalPrice: 1500,
    discountedPrice: 299,
    discount: 80,
    validTill: 'Mar 10, 2026',
    description: '3-hour interactive session with endocrinologists. Includes free sugar monitoring kit & diet plan.',
    icon: Sparkles,
    color: 'var(--color-cta)',
    featured: true,
  },
  {
    id: 5,
    title: 'COVID + Flu Combo Vaccination @ ₹999',
    provider: 'KEM Hospital, Pune',
    category: 'Vaccination',
    originalPrice: 2500,
    discountedPrice: 999,
    discount: 60,
    validTill: 'Mar 20, 2026',
    description: 'Get both COVID booster & Influenza vaccine in a single visit. No appointment needed, walk-in between 9 AM – 4 PM.',
    icon: Syringe,
    color: 'var(--color-success)',
    featured: false,
  },
  {
    id: 6,
    title: 'Thyroid Panel + Vitamin D Test @ ₹599',
    provider: 'Metropolis Labs, Pune',
    category: 'Lab Tests',
    originalPrice: 1800,
    discountedPrice: 599,
    discount: 67,
    validTill: 'Mar 12, 2026',
    description: 'Comprehensive thyroid function test (T3, T4, TSH) plus Vitamin D levels. Home sample collection included.',
    icon: FlaskConical,
    color: '#8B5CF6',
    featured: false,
  },
  {
    id: 7,
    title: 'Eye Checkup Camp — Completely Free',
    provider: 'Deenanath Mangeshkar Hospital',
    category: 'Health Camp',
    originalPrice: 1200,
    discountedPrice: 0,
    discount: 100,
    validTill: 'Mar 8, 2026',
    description: 'Free comprehensive eye examination including retina screening. Discounted spectacles available on-site.',
    icon: Stethoscope,
    color: 'var(--color-primary)',
    featured: true,
  },
  {
    id: 8,
    title: '₹500 Off on Dental Cleaning & Scaling',
    provider: 'SmileCare Dental Clinic, Pune',
    category: 'Dental',
    originalPrice: 1500,
    discountedPrice: 1000,
    discount: 33,
    validTill: 'Mar 25, 2026',
    description: 'Professional dental cleaning with ultrasonic scaling. Free dental X-ray included with every booking.',
    icon: BadgePercent,
    color: 'var(--color-accent)',
    featured: false,
  },
];

const FEATURED = DEALS.filter(d => d.featured);

const slideVariants = {
  enter: (dir) => ({ x: dir > 0 ? 300 : -300, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir > 0 ? -300 : 300, opacity: 0 }),
};

const MedicalDeals = () => {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);
  const [paused, setPaused] = useState(false);

  const paginate = useCallback((dir) => {
    setDirection(dir);
    setCurrent((prev) => (prev + dir + FEATURED.length) % FEATURED.length);
  }, []);

  // Auto-advance
  useEffect(() => {
    if (paused) return;
    const timer = setInterval(() => paginate(1), 5000);
    return () => clearInterval(timer);
  }, [paused, paginate]);

  const deal = FEATURED[current];
  const Icon = deal.icon;

  return (
    <motion.div
      className="deals-page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <div className="deals-header animate-in delay-1">
        <div>
          <h1 className="deals-title"><Tag size={28} /> Medical Deals & Alerts</h1>
          <p className="deals-subtitle">Discover discounts, free camps, and offers on medical services near you</p>
        </div>
      </div>

      {/* ====== CAROUSEL ====== */}
      <div
        className="deals-carousel glass-card animate-in delay-2"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className="carousel-glow" aria-hidden="true" />

        <button className="carousel-arrow prev" onClick={() => paginate(-1)} aria-label="Previous deal">
          <ChevronLeft size={22} />
        </button>

        <div className="carousel-viewport">
          <AnimatePresence custom={direction} mode="wait">
            <motion.div
              key={deal.id}
              className="carousel-slide"
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="slide-badge" style={{ background: `${deal.color}18`, color: deal.color }}>
                <Icon size={14} />
                <span>{deal.category}</span>
              </div>
              <h2 className="slide-title">{deal.title}</h2>
              <p className="slide-provider"><MapPin size={14} /> {deal.provider}</p>
              <p className="slide-desc">{deal.description}</p>
              <div className="slide-bottom">
                <div className="slide-pricing">
                  {deal.originalPrice !== null && (
                    <span className="slide-original">₹{deal.originalPrice.toLocaleString()}</span>
                  )}
                  <span className="slide-discounted">
                    {deal.discountedPrice === 0 ? 'FREE' : deal.discountedPrice !== null ? `₹${deal.discountedPrice.toLocaleString()}` : `${deal.discount}% OFF`}
                  </span>
                  <span className="slide-discount-badge">
                    <Percent size={12} /> {deal.discount}% OFF
                  </span>
                </div>
                <div className="slide-validity">
                  <Clock size={14} /> Valid till {deal.validTill}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        <button className="carousel-arrow next" onClick={() => paginate(1)} aria-label="Next deal">
          <ChevronRight size={22} />
        </button>

        {/* Dots */}
        <div className="carousel-dots">
          {FEATURED.map((_, i) => (
            <button
              key={i}
              className={`carousel-dot ${i === current ? 'active' : ''}`}
              onClick={() => { setDirection(i > current ? 1 : -1); setCurrent(i); }}
              aria-label={`Go to deal ${i + 1}`}
            />
          ))}
        </div>
      </div>

      {/* ====== ALL DEALS GRID ====== */}
      <div className="deals-grid-section animate-in delay-3">
        <h2 className="section-heading">All Deals & Offers</h2>
        <div className="deals-grid">
          {DEALS.map((d, i) => {
            const DIcon = d.icon;
            return (
              <motion.div
                key={d.id}
                className="deal-card glass-card"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <div className="deal-card-top">
                  <span className="deal-category" style={{ background: `${d.color}18`, color: d.color }}>
                    <DIcon size={12} /> {d.category}
                  </span>
                  <span className="deal-discount-pill">
                    <Percent size={11} /> {d.discount}% OFF
                  </span>
                </div>
                <h3 className="deal-card-title">{d.title}</h3>
                <p className="deal-card-provider"><MapPin size={13} /> {d.provider}</p>
                <p className="deal-card-desc">{d.description}</p>
                <div className="deal-card-bottom">
                  <div className="deal-card-pricing">
                    {d.originalPrice !== null && (
                      <span className="deal-orig">₹{d.originalPrice.toLocaleString()}</span>
                    )}
                    <span className="deal-final">
                      {d.discountedPrice === 0 ? 'FREE' : d.discountedPrice !== null ? `₹${d.discountedPrice.toLocaleString()}` : `${d.discount}% OFF`}
                    </span>
                  </div>
                  <span className="deal-card-validity"><Clock size={12} /> {d.validTill}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};

export default MedicalDeals;
