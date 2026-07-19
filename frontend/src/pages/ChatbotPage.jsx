import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm ${
        isUser
          ? 'bg-primary-600 text-white'
          : 'bg-earth-600/30 border border-earth-500/40 text-xl'
      }`}>
        {isUser ? '👤' : '🌱'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
        isUser
          ? 'bg-primary-600 text-white rounded-tr-sm'
          : 'bg-white/10 border border-white/10 text-gray-100 rounded-tl-sm'
      }`}>
        {msg.content.split('\n').map((line, i) => (
          <span key={i}>
            {line}
            {i < msg.content.split('\n').length - 1 && <br />}
          </span>
        ))}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-earth-600/30 border border-earth-500/40 flex items-center justify-center text-xl flex-shrink-0">
        🌱
      </div>
      <div className="bg-white/10 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

export default function ChatbotPage() {
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const language = i18n.language || 'en';

  // Load suggested questions on mount and language change
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const response = await api.get(`/chatbot/suggestions/?lang=${language}`);
        setSuggestions(response.data.suggestions || []);
      } catch {
        // Non-critical — just hide suggestions
      }
    };
    loadSuggestions();
  }, [language]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setInput('');
    setError('');

    const userMessage = { role: 'user', content: messageText };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setLoading(true);

    try {
      const response = await api.post('/chatbot/', {
        messages: updatedMessages,
        language: language,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.message,
      };
      setMessages([...updatedMessages, assistantMessage]);
    } catch (err) {
      setError(err.response?.data?.error || t('common.error'));
      // Remove the user message if the request failed
      setMessages(messages);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError('');
  };

  const showWelcome = messages.length === 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-3xl mx-auto w-full px-4 pt-24 pb-4 flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              🌱 {t('chatbot.title')}
            </h1>
            <p className="text-gray-400 text-sm">{t('chatbot.subtitle')}</p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-gray-500 hover:text-gray-300 text-sm transition-colors px-3 py-1 rounded-lg hover:bg-white/10"
            >
              🗑️ {t('chatbot.clear')}
            </button>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 glass-card p-4 overflow-y-auto mb-4 min-h-96 max-h-[60vh]">

          {/* Welcome screen */}
          {showWelcome && (
            <div className="h-full flex flex-col items-center justify-center text-center py-8">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-xl font-bold text-white mb-2">
                {t('chatbot.welcome_title')}
              </h2>
              <p className="text-gray-400 text-sm max-w-sm mb-8">
                {t('chatbot.welcome_desc')}
              </p>

              {/* Suggested questions */}
              {suggestions.length > 0 && (
                <div className="w-full max-w-md space-y-2">
                  <p className="text-gray-500 text-xs mb-3">
                    {t('chatbot.try_asking')}
                  </p>
                  {suggestions.slice(0, 4).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="w-full text-left px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-gray-300 hover:text-white transition-all duration-200"
                    >
                      💬 {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Messages */}
          {!showWelcome && (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <Message key={i} msg={msg} />
              ))}
              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-3">
            {error}
          </div>
        )}

        {/* Input area */}
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chatbot.input_placeholder')}
            rows={1}
            className="input-field flex-1 resize-none py-3"
            style={{ minHeight: '48px', maxHeight: '120px' }}
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="btn-primary px-5 flex-shrink-0 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '➤'
            )}
          </button>
        </div>

        <p className="text-gray-600 text-xs text-center mt-2">
          {t('chatbot.powered_by')}
        </p>

      </main>
    </div>
  );
}