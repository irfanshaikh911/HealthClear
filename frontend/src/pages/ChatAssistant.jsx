import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { Send, Activity, User, Sparkles, Building, HandCoins, ShieldCheck, ActivitySquare, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { sendRagMessage } from '../services/api';
import './ChatAssistant.css';

const DEFAULT_CHIPS = [
  "I need a knee replacement",
  "How much does angioplasty cost?",
  "Find hospitals for cataract surgery",
  "I have a kidney stone",
];

const ResultCard = ({ result }) => {
  const summary = result.personalized_summary;
  const hospitals = result.hospital_comparison;
  
  const formatINR = (amt) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amt);

  return (
    <div className="result-card glass-card">
      <div className="rc-header">
        <Sparkles size={20} className="rc-icon" />
        <h3>Your Personalized Cost Estimate</h3>
      </div>
      
      <p className="rc-explanation">{result.ai_explanation}</p>
      
      <div className="rc-summary-row">
        <div className="rc-stat-box">
          <span className="rc-stat-label">Estimated Range</span>
          <strong className="rc-stat-value primary">
            {formatINR(summary.estimated_cost_range[0])} - {formatINR(summary.estimated_cost_range[1])}
          </strong>
        </div>
        <div className="rc-stat-box">
          <span className="rc-stat-label">Budget Fit</span>
          <strong className={`rc-stat-value ${summary.budget_fit ? 'success' : 'warning'}`}>
            {summary.budget_fit ? 'Within Budget ✓' : 'Exceeds Budget ⚠️'}
          </strong>
        </div>
      </div>
      
      <div className="rc-insurance-note">
        <ShieldCheck size={16} />
        <span>{summary.insurance_note}</span>
      </div>

      <div className="rc-hospitals">
        <h4 className="rc-hospitals-title">Top Recommended Hospitals</h4>
        <div className="rc-hospital-list">
          {hospitals.map((h, i) => (
            <motion.div 
              key={i} 
              className="rc-hospital-item"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="rc-hospital-info">
                <div className="rc-h-name">
                  <Building size={16} />
                  <strong>{h.hospital_name}</strong>
                  {i === 0 && <span className="rc-badge-best">Best Value</span>}
                </div>
                <div className="rc-h-stats">
                  <span><ActivitySquare size={13} /> {h.success_rate * 100}% Success</span>
                  <span><CheckCircle2 size={13} /> {h.recovery_days} days recovery</span>
                </div>
              </div>
              
              <div className="rc-hospital-cost">
                <span className="rc-h-cost-total">Total: {formatINR(h.personalized_cost)}</span>
                {h.insurance_accepted && h.amount_covered > 0 ? (
                  <div className="rc-h-covered-breakdown">
                    <span className="rc-text-success">Ins. Covers: {formatINR(h.amount_covered)}</span>
                    <strong className="rc-text-oop">You Pay: {formatINR(h.patient_out_of_pocket)}</strong>
                  </div>
                ) : (
                  <span className="rc-text-oop">No Insurance Coverage</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ChatAssistant = () => {
  const { user } = useAuth();
  const location = useLocation();
  const initialMessage = location.state?.initialMessage || null;
  
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // State from RAG backend
  const [sessionId, setSessionId] = useState(null);
  const [suggestedOptions, setSuggestedOptions] = useState(DEFAULT_CHIPS);
  const [isComplete, setIsComplete] = useState(false);
  
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

  // Initialize chat on mount
  useEffect(() => {
    let active = true;
    const initChat = async () => {
      setIsTyping(true);
      try {
        const patientId = user?.patient_id || null;
        const msgToSend = initialMessage || null;
        
        const res = await sendRagMessage(patientId, null, msgToSend);
        if (!active) return;
        
        setSessionId(res.session_id);
        
        // If initialMessage was provided, we want to show it as a user message first
        const newMessages = [];
        if (msgToSend) {
          newMessages.push({ id: Date.now() - 1, sender: 'user', text: msgToSend });
        }
        
        newMessages.push({ id: Date.now(), sender: 'assistant', text: res.reply, result: res.result });
        
        setMessages(newMessages);
        setSuggestedOptions(res.suggested_options || []);
        setIsComplete(res.is_complete);
        
      } catch (err) {
        if (!active) return;
        setMessages([{ id: Date.now(), sender: 'assistant', text: "Sorry, I couldn't connect to the server. Please try again later." }]);
      } finally {
        if (active) setIsTyping(false);
      }
    };
    initChat();
    return () => { active = false; };
  }, [user, initialMessage]); // Only run on mount or when initial params change

  const handleSend = async (text) => {
    if (!text.trim() || isTyping || isComplete) return;
    
    // Add user message
    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text }]);
    setInputValue('');
    setIsTyping(true);
    setSuggestedOptions([]); // hide chips while typing

    try {
      const res = await sendRagMessage(user?.patient_id || null, sessionId, text);
      
      setSessionId(res.session_id);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        sender: 'assistant', 
        text: res.reply,
        result: res.result 
      }]);
      setSuggestedOptions(res.suggested_options || []);
      setIsComplete(res.is_complete);
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now(), sender: 'assistant', text: "Sorry, there was an error processing your request." }]);
      setSuggestedOptions(DEFAULT_CHIPS);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <motion.div className="chat-page"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
      <div className="chat-container glass-card">
        {/* Header */}
        <div className="chat-head">
          <div className="chat-head-avatar">
            <Activity size={22} strokeWidth={2.5} />
          </div>
          <div>
            <h2>HealthClear Assistant</h2>
            <span className="badge badge-primary"><Sparkles size={12} /> AI Powered Cost Estimator</span>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-body" role="log" aria-live="polite">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                className={`msg ${msg.sender} ${msg.result ? 'msg-with-result' : ''}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
              >
                {msg.sender === 'assistant' && (
                  <div className="msg-avatar assistant-av"><Activity size={14} /></div>
                )}
                
                <div className={msg.result ? 'msg-content-wrapper result-wrapper' : 'msg-content-wrapper'}>
                  {msg.text && (
                    <div className="msg-bubble">
                      <p>{msg.text}</p>
                    </div>
                  )}
                  
                  {msg.result && <ResultCard result={msg.result} />}
                </div>

                {msg.sender === 'user' && (
                  <div className="msg-avatar user-av"><User size={14} /></div>
                )}
              </motion.div>
            ))}
            {isTyping && (
              <motion.div className="msg assistant"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="msg-avatar assistant-av"><Activity size={14} /></div>
                <div className="typing-dots"><span /><span /><span /></div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-foot">
          {suggestedOptions.length > 0 && !isComplete && (
            <div className="chip-row">
              {suggestedOptions.map((chip, i) => (
                <button key={i} className="chip" onClick={() => handleSend(chip)} disabled={isTyping}>
                  {chip}
                </button>
              ))}
            </div>
          )}
          
          <form className="chat-form" onSubmit={(e) => { e.preventDefault(); handleSend(inputValue); }}>
            <input type="text" className="chat-input" 
              placeholder={isComplete ? "Estimation complete. Start a new chat to begin again." : "Type your answer or question here..."}
              value={inputValue} onChange={(e) => setInputValue(e.target.value)} 
              disabled={isTyping || isComplete}
              aria-label="Type your message" />
            <button type="submit"
              className={`btn-icon send-btn ${inputValue.trim() && !isComplete ? 'ready' : ''}`}
              disabled={!inputValue.trim() || isTyping || isComplete}
              aria-label="Send message">
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatAssistant;
