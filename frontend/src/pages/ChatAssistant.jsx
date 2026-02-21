import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Activity, User, Sparkles, Paperclip } from 'lucide-react';
import './ChatAssistant.css';

const ACTION_CHIPS = [
  "Explain my latest medical bill",
  "I have a persistent headache",
  "Find urgent care near me",
  "What's the fair price for an MRI?",
  "Compare treatment options for knee pain"
];

const INITIAL_MESSAGES = [
  {
    id: 1,
    sender: 'assistant',
    text: "Hello! I'm your HealthClear Assistant. I can help you understand bills, find treatments, or answer health-related questions. What would you like help with?"
  }
];

const SIMULATED_RESPONSES = {
  "Explain my latest medical bill": "Based on your most recent bill from City Hospital:\n\n• **MRI Scan (Contrast)**: Billed $3,500 — Fair market value is ~$1,200. This appears significantly overcharged.\n• **Room & Board**: $4,000 — This is within the expected range.\n• **Consultation Fee**: $800 — Typical range is $200–$400.\n\nOverall, you may be overpaying by approximately **$4,300**. Would you like me to help you draft a dispute letter?",
  "I have a persistent headache": "I'm sorry to hear that. Here are a few questions to help narrow things down:\n\n1. **Duration**: How long have you had this headache?\n2. **Location**: Is it one-sided, frontal, or all over?\n3. **Severity**: On a scale of 1–10, how would you rate the pain?\n4. **Other symptoms**: Any nausea, vision changes, or sensitivity to light?\n\nBased on your answers, I can suggest whether you should see a primary care doctor, neurologist, or visit urgent care. In the meantime, stay hydrated and rest in a dark, quiet room.",
  "Find urgent care near me": "I found **3 urgent care facilities** near your saved location (Seattle, WA):\n\n1. **CityMed Urgent Care** — 0.8 mi, ⭐ 4.7, Wait: ~10 min, Cost: $150–$250\n2. **ZoomCare Capitol Hill** — 1.2 mi, ⭐ 4.5, Wait: ~15 min, Cost: $125–$200\n3. **MultiCare Indigo** — 2.1 mi, ⭐ 4.6, Wait: ~5 min, Cost: $175–$300\n\nWould you like directions or more details about any of these?",
  "What's the fair price for an MRI?": "The fair market price for an **MRI** varies by type and location:\n\n| Type | Low | Average | High |\n|------|-----|---------|------|\n| Brain MRI | $400 | $1,200 | $3,500 |\n| Knee MRI | $350 | $900 | $2,800 |\n| Spine MRI | $500 | $1,400 | $4,000 |\n\n💡 **Tip**: Outpatient imaging centers are typically **40–60% cheaper** than hospital-based facilities. Would you like me to find affordable imaging centers near you?",
  "Compare treatment options for knee pain": "Here are common treatment paths for knee pain, ranked by invasiveness:\n\n1. **Physical Therapy** — $50–150/session, 6–12 sessions. Best for mild to moderate pain.\n2. **Corticosteroid Injection** — $100–350 per injection. Provides 3–6 months of relief.\n3. **PRP Therapy** — $500–2,000. Uses your own blood to promote healing.\n4. **Arthroscopic Surgery** — $5,000–15,000. For meniscus tears or cartilage damage.\n5. **Total Knee Replacement** — $30,000–70,000. Last resort for severe arthritis.\n\nBased on your profile (mild asthma, no surgical history), I'd recommend starting with **physical therapy**. Would you like me to find providers?"
};

const ChatAssistant = () => {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

  const handleSend = (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text }]);
    setInputValue('');
    setIsTyping(true);

    const responseText = SIMULATED_RESPONSES[text] ||
      `I understand you're asking about: "${text}". Let me look into that for you.\n\nBased on HealthClear's database, I'm cross-referencing treatment costs, provider ratings, and your medical profile to give you the most relevant information. In a production environment, this would connect to our FastAPI backend for real-time analysis.`;

    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'assistant', text: responseText }]);
    }, 1500 + Math.random() * 1000);
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
            <span className="badge badge-primary"><Sparkles size={12} /> AI Powered</span>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-body" role="log" aria-live="polite">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                className={`msg ${msg.sender}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
              >
                {msg.sender === 'assistant' && (
                  <div className="msg-avatar assistant-av"><Activity size={14} /></div>
                )}
                <div className="msg-bubble">
                  <p>{msg.text}</p>
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
          <div className="chip-row">
            {ACTION_CHIPS.map((chip, i) => (
              <button key={i} className="chip" onClick={() => handleSend(chip)} disabled={isTyping}>
                {chip}
              </button>
            ))}
          </div>
          <form className="chat-form" onSubmit={(e) => { e.preventDefault(); handleSend(inputValue); }}>
            <button type="button" className="btn-icon attach-btn" aria-label="Attach document">
              <Paperclip size={20} />
            </button>
            <input type="text" className="chat-input" placeholder="Ask about costs, treatments, or bills..."
              value={inputValue} onChange={(e) => setInputValue(e.target.value)} disabled={isTyping}
              aria-label="Type your message" />
            <button type="submit"
              className={`btn-icon send-btn ${inputValue.trim() ? 'ready' : ''}`}
              disabled={!inputValue.trim() || isTyping}
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
