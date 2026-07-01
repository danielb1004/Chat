import { useState, useRef, useEffect } from 'react';
import './index.css';

const renderMessageText = (text) => {
  if (!text) return '';
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};

function App() {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState([
    { text: '¡Hola! Estoy aquí para ayudarte con consultas del Tribunal Superior de Ibagué.', sender: 'bot', time: 'Ahora' }
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const recognitionRef = useRef(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 240);
  }, []);

  const currentTime = () => {
    return new Intl.DateTimeFormat('es-CO', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date());
  };

  const botReply = async (userMessage) => {
    setIsTyping(true);
    try {
      const response = await fetch(`http://${window.location.hostname}:8000/assistant/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pregunta: userMessage })
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      const reply = data.respuesta || data.response || data.message || data.answer || data.texto || (typeof data === 'string' ? data : JSON.stringify(data));

      setMessages(prev => [...prev, { text: reply, sender: 'bot', time: currentTime() }]);
    } catch (error) {
      console.error('Error fetching bot reply:', error);
      const errText = 'Lo siento, hubo un error al procesar tu solicitud.';
      setMessages(prev => [...prev, { text: errText, sender: 'bot', time: currentTime() }]);
    } finally {
      setIsTyping(false);
    }
  };

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Tu navegador no soporta el reconocimiento de voz. Intenta con Google Chrome o Safari.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'es-CO';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputValue(prev => prev ? `${prev} ${transcript}` : transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const speakText = (text) => {
    window.speechSynthesis.cancel();
    if (!text) return;

    const cleanText = text.replace(/\*\*/g, '');

    const utterance = new SynthesisUtteranceStub(cleanText);
    function SynthesisUtteranceStub(txt) {
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = 'es-CO';
      u.onstart = () => setIsBotSpeaking(true);
      u.onend = () => setIsBotSpeaking(false);
      u.onerror = () => setIsBotSpeaking(false);
      return u;
    }

    const voices = window.speechSynthesis.getVoices();
    const spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
    if (spanishVoice) {
      utterance.voice = spanishVoice;
    }

    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      window.speechSynthesis.cancel();
    };
  }, []);

  const handleSend = (text) => {
    const cleanText = text.trim();
    if (!cleanText) return;

    setMessages(prev => [...prev, { text: cleanText, sender: 'user', time: currentTime() }]);
    setInputValue('');
    botReply(cleanText);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend(inputValue);
  };

  const handleQuickAction = (question) => {
    handleSend(question);
  };

  return (
    <div className="chat-window-iframe">
      <header className="chat-header">
        <div className="header-row">
          <div className="title-wrap">
            <h2>Leya</h2>
            <p>Asistencia rápida para consultas del sitio</p>
          </div>
          <div className="header-actions">
            <div className="status-pill">
              <span className="status-dot"></span>
              En línea
            </div>
          </div>
        </div>
      </header>

      <div className="bot-profile">
        <div className="avatar" aria-hidden="true">
           {isBotSpeaking ? (
             <video autoPlay loop muted playsInline className="avatar-media">
               <source src="/avatar_mov.mp4" type="video/mp4" />
             </video>
           ) : (
             <img src="/avatar.jpeg" alt="Avatar" className="avatar-media" />
           )}
           <span className="avatar-badge">M</span>
         </div>
        <div className="profile-copy">
          <strong>Asistente del Tribunal</strong>
          <span>Escribe tu pregunta o elige una opción rápida para orientarte mejor.</span>
        </div>
      </div>

      <div className="messages" id="messages">
         {messages.map((msg, index) => (
           <div key={index} className={`message-row ${msg.sender}`}>
             <div className="bubble">
               <span className="bubble-text">{renderMessageText(msg.text)}</span>
               {msg.sender === 'bot' && (
                 <button 
                   type="button" 
                   className="speak-msg-btn" 
                   onClick={() => speakText(msg.text)} 
                   aria-label="Escuchar mensaje"
                 >
                   <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                     <path d="M11 5L6 9H2v6h4l5 4V5z" fill="currentColor"/>
                     <path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                   </svg>
                 </button>
               )}
               <span className="message-time">{msg.time}</span>
             </div>
           </div>
         ))}



        <div className={`typing ${isTyping ? 'active' : ''}`} id="typing" aria-label="El asistente está escribiendo">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-area" id="chatForm" onSubmit={handleSubmit}>
        <div className="input-box">
          <input 
            ref={inputRef}
            id="chatInput" 
            type="text" 
            placeholder={isListening ? "Escuchando..." : "Escribe tus dudas"} 
            autoComplete="off" 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <button 
            type="button" 
            className={`mic-btn ${isListening ? 'listening' : ''}`} 
            onClick={handleMicClick}
            aria-label="Hablar"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3Z" fill="currentColor"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button className="send-btn" type="submit" aria-label="Enviar mensaje">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 12L20 4L16.5 20L12.5 13.5L4 12Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
              <path d="M12.5 13.5L20 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <p className="input-note">Respuesta automática de orientación. Verifica siempre la información oficial.</p>
      </form>
    </div>
  );
}

export default App;
