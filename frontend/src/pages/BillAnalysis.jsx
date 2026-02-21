import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud, File, X, ShieldAlert, ShieldCheck, Shield,
  CheckCircle, TrendingDown, DollarSign, Activity, AlertTriangle,
  Copy, RefreshCw, Loader2
} from 'lucide-react';
import { uploadBill, getBillStatus, getBillReport } from '../services/api';
import './BillAnalysis.css';

const POLL_INTERVAL_MS = 3000;

const FLAG_CONFIG = {
  OK:          { label: 'Fair',        cls: 'badge-success',  icon: CheckCircle },
  OVERCHARGED: { label: 'Overcharged', cls: 'badge-danger',   icon: AlertTriangle },
  DUPLICATE:   { label: 'Duplicate',   cls: 'badge-warning',  icon: Copy },
  MATH_ERROR:  { label: 'Math Error',  cls: 'badge-danger',   icon: AlertTriangle },
  UNKNOWN:     { label: 'Unknown',     cls: 'badge-muted',    icon: Shield },
};

const VERDICT_CONFIG = {
  CLEAN:      { label: '✅ Clean',       cls: 'verdict-clean',      icon: ShieldCheck },
  SUSPICIOUS: { label: '⚠️ Suspicious', cls: 'verdict-suspicious', icon: ShieldAlert },
  FRAUDULENT: { label: '🚨 Fraudulent', cls: 'verdict-fraudulent', icon: ShieldAlert },
};

const BillAnalysis = () => {
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState('idle');        // idle | uploading | processing | done | error
  const [billUuid, setBillUuid] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  // ── Cleanup polling on unmount ──────────────────────────────
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  // ── Poll status until COMPLETED / FAILED ────────────────────
  const startPolling = useCallback((uuid) => {
    pollRef.current = setInterval(async () => {
      try {
        const { status } = await getBillStatus(uuid);
        if (status === 'COMPLETED') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          const report = await getBillReport(uuid);
          setResult(report);
          setPhase('done');
        } else if (status === 'FAILED') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setError('Analysis failed. Please try uploading again.');
          setPhase('error');
        }
      } catch {
        // Silently retry — network blips during polling are expected
      }
    }, POLL_INTERVAL_MS);
  }, []);

  // ── Upload + start polling ──────────────────────────────────
  const handleAnalyze = async () => {
    if (!file) return;
    setError(null);
    setPhase('uploading');

    try {
      const { bill_uuid } = await uploadBill(file);
      setBillUuid(bill_uuid);
      setPhase('processing');
      startPolling(bill_uuid);
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
      setPhase('error');
    }
  };

  // ── Reset to initial state ──────────────────────────────────
  const clearAll = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setFile(null);
    setResult(null);
    setError(null);
    setBillUuid(null);
    setPhase('idle');
  };

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setPhase('idle');
    }
  };

  const isProcessing = phase === 'uploading' || phase === 'processing';
  const verdictCfg = result ? VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.CLEAN : null;

  return (
    <motion.div className="bill-page" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
      <div className="page-top animate-in delay-1">
        <h1>Bill Verification &amp; Analysis</h1>
        <p>Upload your medical bill to detect overcharges and compare with fair market values.</p>
      </div>

      {/* ── Upload / Processing Card ─────────────────────────── */}
      {phase !== 'done' && (
        <div className="upload-card glass-card animate-in delay-2">
          {!file ? (
            <div
              className="drop-zone"
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              aria-label="Upload a medical bill file"
            >
              <div className="drop-icon-wrap"><UploadCloud size={36} /></div>
              <h3>Drop your bill here or click to browse</h3>
              <p>Supports PDF, JPG, PNG (Max 10MB)</p>
              <span className="btn btn-secondary mt-4">Choose File</span>
            </div>
          ) : (
            <div className="file-ready">
              <div className="file-info">
                <div className="file-icon-wrap"><File size={28} /></div>
                <div>
                  <h4>{file.name}</h4>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                {!isProcessing && (
                  <button className="btn-icon remove-file" onClick={clearAll} aria-label="Remove file">
                    <X size={20} />
                  </button>
                )}
              </div>

              {/* Processing indicator */}
              {isProcessing && (
                <div className="processing-state">
                  <Loader2 size={20} className="spin" />
                  <span>
                    {phase === 'uploading' ? 'Uploading bill...' : 'Analyzing — OCR extraction & verification in progress...'}
                  </span>
                </div>
              )}

              {/* Error message */}
              {error && (
                <div className="error-state">
                  <AlertTriangle size={18} />
                  <span>{error}</span>
                </div>
              )}

              <button
                className="btn btn-cta w-full analyze-btn"
                onClick={phase === 'error' ? handleAnalyze : handleAnalyze}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <><span className="spinner" /> Analyzing Document...</>
                ) : phase === 'error' ? (
                  <><RefreshCw size={18} /> Retry Analysis</>
                ) : (
                  <><Activity size={18} /> Start Analysis</>
                )}
              </button>
            </div>
          )}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden-input"
            accept=".pdf,.jpg,.jpeg,.png"
          />
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────── */}
      <AnimatePresence>
        {result && (
          <motion.div
            className="results-area"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            {/* Header */}
            <div className="results-top">
              <div>
                <h2>Analysis Complete</h2>
                <div className="results-meta">
                  <span className={`verdict-badge ${verdictCfg?.cls || ''}`}>
                    {verdictCfg?.label || result.verdict}
                  </span>
                  <span className="trust-score">
                    Trust Score: <strong>{result.trust_score}%</strong>
                  </span>
                </div>
              </div>
              <button className="btn btn-secondary" onClick={clearAll}>Analyze Another</button>
            </div>

            {/* Summary Cards */}
            <div className="summary-grid">
              <div className="summary-card glass-card">
                <div className="summary-icon danger"><DollarSign size={22} /></div>
                <div>
                  <p className="summary-label">Total Billed</p>
                  <h3 className="summary-value">₹{(result.total_billed || 0).toLocaleString()}</h3>
                </div>
              </div>
              <div className="summary-card glass-card">
                <div className="summary-icon success"><CheckCircle size={22} /></div>
                <div>
                  <p className="summary-label">Estimated Fair Price</p>
                  <h3 className="summary-value">₹{(result.estimated_fair_price || 0).toLocaleString()}</h3>
                </div>
              </div>
              <div className="summary-card glass-card highlight-card">
                <div className="summary-icon primary"><TrendingDown size={22} /></div>
                <div>
                  <p className="summary-label">Total Overcharge</p>
                  <h3 className="summary-value">
                    ₹{(result.total_overcharge || 0).toLocaleString()}{' '}
                    <span className="savings-pct">({result.overcharge_percent || 0}%)</span>
                  </h3>
                </div>
              </div>
            </div>

            {/* Summary Text */}
            {result.summary && (
              <div className="summary-text glass-card">
                <p>{result.summary}</p>
              </div>
            )}

            {/* Line Items Breakdown */}
            {result.findings && result.findings.length > 0 && (
              <div className="breakdown glass-card">
                <h3>Line-Item Breakdown ({result.total_items} items, {result.flagged_items} flagged)</h3>
                <div className="breakdown-table" role="table">
                  <div className="breakdown-head" role="row">
                    <span role="columnheader">Description</span>
                    <span role="columnheader" className="text-right">Billed</span>
                    <span role="columnheader" className="text-right">Fair Max</span>
                    <span role="columnheader" className="text-center">Status</span>
                  </div>
                  {result.findings.map((item, i) => {
                    const flagCfg = FLAG_CONFIG[item.flag] || FLAG_CONFIG.UNKNOWN;
                    const FlagIcon = flagCfg.icon;
                    return (
                      <div className="breakdown-row" key={i} role="row">
                        <span className="row-name" role="cell">
                          {item.item_name}
                          {item.category && <small className="row-category">{item.category}</small>}
                        </span>
                        <span className="text-right" role="cell">₹{(item.total_price || 0).toLocaleString()}</span>
                        <span className="text-right row-fair" role="cell">
                          {item.standard_max != null ? `₹${item.standard_max.toLocaleString()}` : '—'}
                        </span>
                        <span className="text-center" role="cell">
                          <span className={`badge ${flagCfg.cls}`}>
                            <FlagIcon size={12} /> {flagCfg.label}
                          </span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && (
              <div className="recommendations glass-card">
                <h3>Recommendations</h3>
                <pre className="reco-text">{result.recommendations}</pre>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default BillAnalysis;
