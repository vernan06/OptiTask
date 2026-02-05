import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Mic, MicOff, Volume2, VolumeX, Send, Bot, User, Loader2 } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function Assistant({ onTaskUpdate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hey! I'm OptiTask, your productivity companion. What can I help you with?" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Text-to-speech
  const speak = (text) => {
    if (!isSpeaking) return;
    const cleanText = text.replace(/[#*_`]/g, '').replace(/\n/g, '. ');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  };

  // Toggle voice input
  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition not supported in your browser. Try Chrome!');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // Send message to backend
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await res.json();
      const assistantResponse = data.response || "I understand!";

      setMessages(prev => [...prev, { role: 'assistant', content: assistantResponse }]);
      speak(assistantResponse);

      // Refresh tasks if action was taken
      if (['add_task', 'complete_task', 'delete_task'].includes(data.action)) {
        onTaskUpdate?.();
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Oops! Having trouble connecting. Make sure the backend is running." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`assistant-fab ${isOpen ? 'hidden' : ''}`}
        title="Talk to OptiTask"
      >
        <Bot size={24} />
        <span className="pulse-ring"></span>
      </button>

      {/* Chat Panel */}
      <div className={`assistant-panel ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="assistant-header">
          <div className="assistant-title">
            <Bot size={20} />
            <span>OptiTask AI</span>
          </div>
          <div className="assistant-controls">
            <button 
              onClick={() => setIsSpeaking(!isSpeaking)} 
              className={`icon-btn ${isSpeaking ? 'active' : ''}`}
              title={isSpeaking ? 'Mute voice' : 'Enable voice'}
            >
              {isSpeaking ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
            <button onClick={() => setIsOpen(false)} className="icon-btn">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="assistant-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-icon">
                {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div className="message-content">
                {msg.content.split('\n').map((line, j) => (
                  <p key={j}>{line}</p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-icon"><Bot size={16} /></div>
              <div className="message-content typing">
                <Loader2 size={16} className="spinner" />
                <span>Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="assistant-input">
          <button 
            onClick={toggleListening} 
            className={`voice-btn ${isListening ? 'listening' : ''}`}
            title={isListening ? 'Stop listening' : 'Speak'}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? 'Listening...' : 'Type or speak...'}
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            className="send-btn" 
            disabled={!input.trim() || isLoading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </>
  );
}
