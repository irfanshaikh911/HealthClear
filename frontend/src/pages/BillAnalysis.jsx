import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, File, X, ShieldAlert, CheckCircle, TrendingDown, DollarSign, Activity, AlertTriangle } from 'lucide-react';
import './BillAnalysis.css';

const BillAnalysis = () => {
  const [file, setFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const clearFile = () => { setFile(null); setResult(null); };

  const handleAnalyze = () => {
    if (!file) return;
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setResult({
        totalBilled: 12500,
        fairMarketValue: 8200,
        savingsFound: 4300,
        savingsPercent: 34,
        confidenceScore: 94,
        discrepancies: [
          { item: 'MRI Scan (Contrast)', billed: 3500, fair: 1200, status: 'overcharged' },
          { item: 'Room & Board (Overnight)', billed: 4000, fair: 4000, status: 'fair' },
          { item: 'Specialist Consultation', billed: 800, fair: 300, status: 'overcharged' },
          { item: 'Miscellaneous Supplies', billed: 4200, fair: 2700, status: 'overcharged' }
        ]
      });
    }, 2200);
  };

  return (
    <motion.div
      className="bill-page"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="page-top animate-in delay-1">
        <h1>Bill Verification & Analysis</h1>
        <p>Upload your medical bill to detect overcharges and compare with fair market values.</p>
      </div>

      {!result && (
        <div className="upload-card glass-card animate-in delay-2">
          {!file ? (
            <div className="drop-zone" onClick={() => fileInputRef.current?.click()} role="button" tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              aria-label="Upload a medical bill file">
              <div className="drop-icon-wrap">
                <UploadCloud size={36} />
              </div>
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
                <button className="btn-icon remove-file" onClick={clearFile} aria-label="Remove file">
                  <X size={20} />
                </button>
              </div>
              <button className="btn btn-cta w-full analyze-btn" onClick={handleAnalyze} disabled={isAnalyzing}>
                {isAnalyzing ? (
                  <><span className="spinner" /> Analyzing Document...</>
                ) : (
                  <><Activity size={18} /> Start Analysis</>
                )}
              </button>
            </div>
          )}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden-input"
            accept=".pdf,.jpg,.jpeg,.png" />
        </div>
      )}

      <AnimatePresence>
        {result && (
          <motion.div className="results-area"
            initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>

            <div className="results-top">
              <div>
                <h2>Analysis Complete</h2>
                <p>Confidence: <strong>{result.confidenceScore}%</strong></p>
              </div>
              <button className="btn btn-secondary" onClick={clearFile}>Analyze Another</button>
            </div>

            {/* Summary Cards */}
            <div className="summary-grid">
              <div className="summary-card glass-card">
                <div className="summary-icon danger"><DollarSign size={22} /></div>
                <div>
                  <p className="summary-label">Total Billed</p>
                  <h3 className="summary-value">${result.totalBilled.toLocaleString()}</h3>
                </div>
              </div>
              <div className="summary-card glass-card">
                <div className="summary-icon success"><CheckCircle size={22} /></div>
                <div>
                  <p className="summary-label">Fair Market Value</p>
                  <h3 className="summary-value">${result.fairMarketValue.toLocaleString()}</h3>
                </div>
              </div>
              <div className="summary-card glass-card highlight-card">
                <div className="summary-icon primary"><TrendingDown size={22} /></div>
                <div>
                  <p className="summary-label">Potential Savings</p>
                  <h3 className="summary-value">${result.savingsFound.toLocaleString()} <span className="savings-pct">({result.savingsPercent}%)</span></h3>
                </div>
              </div>
            </div>

            {/* Line Items */}
            <div className="breakdown glass-card">
              <h3>Line-Item Breakdown</h3>
              <div className="breakdown-table" role="table">
                <div className="breakdown-head" role="row">
                  <span role="columnheader">Description</span>
                  <span role="columnheader" className="text-right">Billed</span>
                  <span role="columnheader" className="text-right">Fair Value</span>
                  <span role="columnheader" className="text-center">Status</span>
                </div>
                {result.discrepancies.map((item, i) => (
                  <div className="breakdown-row" key={i} role="row">
                    <span className="row-name" role="cell">{item.item}</span>
                    <span className="text-right" role="cell">${item.billed.toLocaleString()}</span>
                    <span className="text-right row-fair" role="cell">${item.fair.toLocaleString()}</span>
                    <span className="text-center" role="cell">
                      {item.status === 'overcharged' ? (
                        <span className="badge badge-danger"><AlertTriangle size={12} /> Overcharged</span>
                      ) : (
                        <span className="badge badge-success"><CheckCircle size={12} /> Fair</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default BillAnalysis;
